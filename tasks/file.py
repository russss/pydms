# coding=utf-8
from __future__ import division, absolute_import, print_function, unicode_literals
import logging
import shutil

from task import Task


class FileThread(Task):
    def __init__(self, callback=None):
        self.log = logging.getLogger(__name__)
        super(FileThread, self).__init__(name="FileThread", callback=callback)

    def process(self, job):
        self.log.info("Writing files for job %r", job)
        shutil.move(job.pdf, job.filename)
