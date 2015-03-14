# coding=utf-8
from __future__ import division, absolute_import, print_function, unicode_literals
import logging
from time import sleep
from threading import Thread
from Queue import Queue
from job import Side

side_map = {
    Side.front: 'ADF Front',
    Side.back: 'ADF Back',
    Side.duplex: 'ADF Duplex'
}


class ScanningThread(Thread):
    def __init__(self, scanner, callback):
        self.log = logging.getLogger(__name__)
        self.scanner = scanner
        self.callback = callback
        self.job_queue = Queue()
        self.log.info("Using scanner: %r", self.scanner)
        super(ScanningThread, self).__init__(name="ScanningThread")
        self.daemon = True

    def run(self):
        while True:
            self.process(self.job_queue.get())

    def process(self, job):
        self.log.info("Processing job %r", job)
        self.scanner.options['source'].value = side_map[job.side]
        self.scanner.options['mode'].value = 'Color'
        self.wait_for_page()
        job.images = self.acquire()
        if self.callback:
            self.callback(job)

    def wait_for_page(self):
        if 'page-loaded' not in self.scanner.options:
            return
        while self.scanner.options['page-loaded'].value == 0:
            sleep(0.25)

    def acquire(self):
        self.log.info("Starting scan...")
        session = self.scanner.scan(multiple=True)
        try:
            while True:
                try:
                    session.scan.read()
                except EOFError:
                    self.log.info("Page finished.")
        except StopIteration:
            self.log.info("Document finished.")
        return session.images

    def submit_job(self, job):
        self.job_queue.put(job)
