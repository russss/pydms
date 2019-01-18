#!/usr/bin/env python3
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
from tasks.ocr import OCRThread
from tasks.file import FileThread


class PyDMS(object):
    DESTINATION = '/Users/russ/scan-inbox'

    def __init__(self):
        self.log = logging.getLogger(__name__)
        print("Looking for scanner...")
        devices = pyinsane.get_devices()
        if len(devices) == 0:
            raise "No scanner found"
        scanner = pyinsane.Scanner(name=devices[0].name)
        try:
            scanner.options
        except SaneStatus:
            self.log.exception("Unable to connect to scanner")
            sys.exit(1)
        print("Found scanner %s." % devices[0].name)
        self.temp_dir = tempfile.mkdtemp(prefix='pydms')
        self.file_thread = FileThread()
        self.ocr_thread = OCRThread(self.file_thread.submit_job)
        self.convert_thread = ConversionThread(self.temp_dir, self.ocr_thread.submit_job)
        self.scan_thread = ScanningThread(scanner, self.convert_thread.submit_job)
        self.file_thread.start()
        self.ocr_thread.start()
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
            job.filename = os.path.join(self.DESTINATION, input('File Name: '))
            source_str = input('Enter source (f, b, [d]): ')
            if source_str == 'f':
                job.side = Side.front
            elif source_str == 'b':
                job.side = Side.back
            else:
                job.side = Side.duplex
            print("Starting scan...")
            self.scan_thread.submit_job(job)


logging.basicConfig(level=logging.INFO, filename="pydms.log")
PyDMS().run()
