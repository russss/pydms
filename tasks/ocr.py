import logging

from task import Task
from timing import Timer


class OCRThread(Task):
    def __init__(self, callback=None):
        self.log = logging.getLogger(__name__)
        super().__init__(name="OCRThread", callback=callback)

    def process(self, job):
        self.log.info("OCRing job %r", job)
        with Timer() as t:
            job.ig.ocr(job.pdf)
        self.log.info("Job %r: OCRed in %s", job, t)
