#!/usr/bin/env python
import sys
import os.path
import logging
import pyinsane.abstract as pyinsane
from pyinsane.rawapi import SaneStatus
from job import Job, Side
from scanning_thread import ScanningThread
from conversion_thread import ConversionThread


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
        self.convert_thread = ConversionThread()
        self.scan_thread = ScanningThread(scanner, self.convert_thread.submit_job)
        self.convert_thread.start()
        self.scan_thread.start()
        self.log.info("Running")

    def run(self):
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

logging.basicConfig()
PyDMS().run()
