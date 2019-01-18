import logging
from PIL import Image, ImageChops, ImageEnhance, ImageOps
from io import BytesIO
from os import path
import tempfile
import subprocess
import pgmagick
import cv2
import numpy as np


def gmagick_from_pil(img, fmt="jpeg"):
    """ Convert a PIL Image into a GraphicsMagick Image.
        Currently we do this by rendering the PIL image to a JPEG
        and creating the GM image from that.
    """
    buf = BytesIO()
    img.save(buf, format=fmt)
    return pgmagick.Image(pgmagick.Blob(buf.getvalue()))


def cv2_from_pil(img):
    return cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)


def pil_from_cv2(img):
    return Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))


class ImageGroup(object):
    def __init__(self, images):
        self.log = logging.getLogger(__name__)
        self.images = images

    def save_pdf(self, filename):
        self.process_images()
        img_list = pgmagick.ImageList()
        for image in self.processed_images:
            self.log.info("Saving page (size %sx%s)", image.size[0], image.size[1])
            img = gmagick_from_pil(image)
            if image.size[0] > image.size[1]:
                img.page(pgmagick.Geometry(b"842x595>"))
            else:
                img.page(pgmagick.Geometry(b"A4"))
            img_list.append(img)

        img_list.writeImages(filename.encode())

    def ocr(self, filename):
        with tempfile.TemporaryDirectory() as dirname, tempfile.NamedTemporaryFile(
            suffix=".txt"
        ) as listfile:
            count = 0
            files = []
            for image in self.processed_images:
                self.log.info(
                    "Saving page %s (size %sx%s)", count, image.size[0], image.size[1]
                )
                fname = path.join(dirname, "img%03i.jpg" % count)
                image.save(fname, dpi=(300, 300))
                files.append(fname)
                count += 1

            listfile.write(("\n".join(files)).encode("utf-8"))
            listfile.flush()

            # Tesseract kindly appends .pdf to the output file so we'll remove it.
            filename = filename.replace('.pdf', '').encode()

            proc = subprocess.Popen(
                ["tesseract", listfile.name, filename, "pdf"],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            stdout, stderr = proc.communicate()
            if len(stdout) > 0:
                self.log.info("Tesseract stdout: %s", stdout)
            if len(stderr) > 0:
                self.log.info("Tesseract stderr: %s", stderr)

    def process_images(self):
        self.processed_images = [self.process(im) for im in self.images]

    def process(self, im):
        # im is a PIL image, we need to turn it to a cv2 image for this...
        self.log.info("Processing image (size %sx%s)", im.size[0], im.size[1])
        deskewed = deskew(cv2_from_pil(im))
        cropped = autocrop(deskewed)
        im = pil_from_cv2(cropped)
        self.log.info("Deskewed (size %sx%s)", im.size[0], im.size[1])
        return self.enhance(im)

    def resize(self, im, max_size):
        ratio = max(1, min(max_size[0] / im.size[0], max_size[1] / im.size[1]))
        im.thumbnail(((int(im.size[0] * ratio), int(im.size[1] * ratio))))
        return im

    def trim(self, im):
        bg = Image.new(im.mode, im.size, im.getpixel((0, 0)))
        diff = ImageChops.difference(im, bg)
        diff = ImageChops.add(diff, diff, 2.0, -100)
        bbox = diff.getbbox()
        if bbox:
            return im.crop(bbox)

    def enhance(self, im):
        im = ImageOps.autocontrast(im)
        enhancer = ImageEnhance.Sharpness(im)
        return enhancer.enhance(1)

    def is_colour(self, im):
        """ Detect if an image is colour using mean luminance """
        hsl = cv2.cvtColor(im, cv2.COLOR_BGR2HSV)
        h, s, v = np.mean(hsl, (0, 1))
        if s < 100:
            self.log.info(
                "Grayscale scan detected (hsv %s, %s, %s), converting...", h, s, v
            )
            return False
        return True


def deskew(im, max_skew=10):
    """ Remove 90 degree landscape rotation and skew from a scanned image.

        We do this by detecting lines in the image using a Hough transform, working
        out which lines are important, and aligning them so the're horizontal.
    """
    width, height, _channels = im.shape

    # Create a grayscale image
    im_gs = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)

    # Denoising doesn't seem to help much here and it's slow!
    # im_gs = cv2.fastNlMeansDenoising(im_gs, h=3)

    # Create an inverted B&W copy using Otsu (automatic) thresholding
    im_bw = cv2.threshold(im_gs, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]

    # Detect lines in this image
    lines = cv2.HoughLinesP(
        im_bw, 1, np.pi / 180, 200, minLineLength=width / 12, maxLineGap=width / 150
    )

    # Collect the angles of these lines (in radians)
    angles = []
    for line in lines:
        x1, y1, x2, y2 = line[0]
        angles.append(np.arctan2(y2 - y1, x2 - x1))

    # If the majority of our lines are vertical, this is probably a landscape image
    landscape = np.sum([abs(angle) > np.pi / 4 for angle in angles]) > len(angles) / 2

    # Filter the angles to remove outliers based on max_skew
    if landscape:
        angles = [
            angle
            for angle in angles
            if np.deg2rad(90 - max_skew) < abs(angle) < np.deg2rad(90 + max_skew)
        ]
    else:
        angles = [angle for angle in angles if abs(angle) < np.deg2rad(max_skew)]

    if len(angles) < 5:
        # Insufficient data to deskew
        return im

    # Average the angles to a degree offset
    angle_deg = np.rad2deg(np.median(angles))

    # If this is landscape image, rotate the entire canvas appropriately
    # Note that we can't tell the difference between +90 and -90 degree rotation,
    # so we assume it's always counterclockwise because that's how most scanners work.
    if landscape:
        im = cv2.rotate(im, cv2.ROTATE_90_COUNTERCLOCKWISE)
        angle_deg = abs(angle_deg) - 90
        width, height, _ = im.shape

    # Rotate the image by the residual offset
    M = cv2.getRotationMatrix2D((width / 2, height / 2), angle_deg, 1)
    im = cv2.warpAffine(im, M, (height, width), borderMode=cv2.BORDER_REPLICATE)
    return im


def crop_mask(mask, crop_offset=0.5):
    """ Move in from each edge, detecting where the mask starts to contain zeros.
        Then move in a further crop_offset% of the image dimension to (ideally)
        completely trim off the edge.
    """
    maxx, maxy, minx, miny = 0, 0, 0, 0
    for r in range(0, mask.shape[0]):
        if np.min(mask[r]) < 255:
            minx = int(r + mask.shape[0] * (crop_offset / 100))
            break

    for r in range(mask.shape[0] - 1, 0, -1):
        if np.min(mask[r]) < 255:
            maxx = int(r - mask.shape[0] * (crop_offset / 100))
            break

    for c in range(0, mask.shape[1]):
        if np.min(mask[:, c]) < 255:
            miny = int(c + mask.shape[1] * (crop_offset / 100))
            break

    for c in range(mask.shape[1] - 1, 0, -1):
        if np.min(mask[:, c]) < 255:
            maxy = int(c - mask.shape[1] * (crop_offset / 100))
            break

    return (maxx, maxy, minx, miny)


def autocrop(im, tolerance=0.15, crop_offset=2):
    """ Crop scanner background out of an image. It probably helps to have a colour
        image here even if the scanned document is B&W.
    """
    # Assume the mean of the top-left four pixels of an image is the background colour.
    background = np.mean([im[0, 0], im[0, 1], im[1, 0], im[1, 1]], 0)

    # Generate a mask out of the image, highlighting this background colour.
    mask = cv2.inRange(im, background * (1 - tolerance), background * (1 + tolerance))

    # The MORPH_OPEN operator filters out smaller features which leaves us only with
    # the border we're interested in. This isn't necessary with this simple cropping
    # algorithm but I'm leaving it here in case we want to try doing it using contours
    # again.
    # kernel = cv2.getStructuringElement(cv2.MORPH_CROSS, (20, 20))
    # m_morph = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    # Detect the extents of the interesting region
    maxx, maxy, minx, miny = crop_mask(mask)

    # TODO: safety check here to make sure we're not cropping out the whole image?

    return im[minx:maxx, miny:maxy]
