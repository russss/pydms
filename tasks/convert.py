# coding=utf-8
from __future__ import division, absolute_import, print_function, unicode_literals
import logging
import random
import string
import os.path

from task import Task
from timing import Timer
from imagetools import ImageGroup


class ConversionThread(Task):
    """ Convert a list of images into a PDF file, and save that file to a temporary location.
        Due to the limitations of GraphicsMagick, we *have* to use a file on disk.
    """
    def __init__(self, temp_dir, callback=None):
        self.temp_dir = temp_dir
        self.log = logging.getLogger(__name__)
        super(ConversionThread, self).__init__(name="ConversionThread", callback=callback)

    def process(self, job):
        self.log.info("Processing job %r", job)
        with Timer() as t:
            job.pdf = self.get_pdf_filename()
            ig = ImageGroup(job.images)
            ig.save_pdf(job.pdf)
        self.log.info("Job %r: %i images converted in %s", job, len(job.images), t)
        del job.images

    def get_pdf_filename(self):
        name = ''.join(random.choice(string.letters) for x in range(6)) + '.pdf'
        return os.path.join(self.temp_dir, name)
