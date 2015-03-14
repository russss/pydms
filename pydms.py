#!/usr/bin/env python
import sys
import os.path
import logging
import tempfile
import shutil
import pyinsane.abstract as pyinsane
from pyinsane.rawapi import SaneStatus
from job import Job, Side
from tasks.scan import ScanningThread
from tasks.convert import ConversionThread
from tasks.file import FileThread


class PyDMS(object):
    DESTINATION = '/Users/russ/scan-inbox'

    def __init__(self):
        self.log = logging.getLogger(__name__)
        scanner = pyinsane.Scanner(name="epjitsu:libusb:002:012-04c5-11ed-ff-ff")
        try:
            scanner.options
        except SaneStatus:
            self.log.exception("Unable to connect to scanner")
            sys.exit(1)
        self.temp_dir = tempfile.mkdtemp(prefix='pydms')
        self.file_thread = FileThread()
        self.convert_thread = ConversionThread(self.temp_dir, self.file_thread.submit_job)
        self.scan_thread = ScanningThread(scanner, self.convert_thread.submit_job)
        self.file_thread.start()
        self.convert_thread.start()
        self.scan_thread.start()
        self.log.info("Running")

    def run(self):
        try:
            self.run_ui()
        finally:
            shutil.rmtree(self.temp_dir)

    def run_ui(self):
        while True:
            job = Job()
            job.filename = os.path.join(self.DESTINATION, raw_input('File Name: '))
            source_str = raw_input('Enter source (f, b, [d]): ')
            if source_str == 'f':
                job.side = Side.front
            elif source_str == 'b':
                job.side = Side.back
            else:
                job.side = Side.duplex
            print "Starting scan..."
            self.scan_thread.submit_job(job)

logging.basicConfig(level=logging.INFO)
PyDMS().run()
