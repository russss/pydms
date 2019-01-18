# coding=utf-8
from __future__ import division, absolute_import, print_function, unicode_literals
import logging
import os
from camlipy import Camlistore

from task import Task


class CamlistoreThread(Task):
    def __init__(self, callback=None):
        """ Take a finished PDF file and upload it to Camlistore """
        self.log = logging.getLogger(__name__)
        self.camlistore = Camlistore("http://localhost:3179")
        super(CamlistoreThread, self).__init__(name="CamlistoreThread", callback=callback)

    def process(self, job):
        self.log.info("Uploading file for job %r", job)
        with open(job.pdf, 'rb') as fh:
            self.camlistore.put_blobs([fh])
        os.unlink(job.pdf)
