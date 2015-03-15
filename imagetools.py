# coding=utf-8
from __future__ import division, absolute_import, print_function, unicode_literals
import logging
from PIL import Image, ImageChops, ImageEnhance
from StringIO import StringIO
import pgmagick


def gmagick_from_pil(img, fmt='jpeg'):
    """ Convert a PIL Image into a GraphicsMagick Image.
        Currently we do this by rendering the PIL image to a JPEG
        and creating the GM image from that.
    """
    buf = StringIO()
    img.save(buf, format=fmt)
    return pgmagick.Image(pgmagick.Blob(buf.getvalue()))


class ImageGroup(object):
    def __init__(self, images):
        self.log = logging.getLogger(__name__)
        self.images = images

    def save_pdf(self, filename):
        processed_images = [self.process(im) for im in self.images]
        img_list = pgmagick.ImageList()
        for image in processed_images:
            img_list.append(gmagick_from_pil(image))

        img_list.writeImages(filename.encode())

    def process(self, im):
        return self.enhance(self.resize(self.trim(im), (2000, 2000)))

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
        enhancer = ImageEnhance.Sharpness(im)
        return enhancer.enhance(1)
