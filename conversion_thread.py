# coding=utf-8
from __future__ import division, absolute_import, print_function, unicode_literals
import logging
from threading import Thread
from Queue import Queue

from imagetools import ImageGroup


class ConversionThread(Thread):
    def __init__(self):
        self.log = logging.getLogger(__name__)
        self.job_queue = Queue()
        super(ConversionThread, self).__init__(name="ConversionThread")
        self.daemon = True

    def run(self):
        while True:
            self.process(self.job_queue.get())

    def process(self, job):
        self.log.info("Processing job %r", job)
        ig = ImageGroup(job.images)
        ig.save_pdf(job.filename)

    def submit_job(self, job):
        self.job_queue.put(job)
