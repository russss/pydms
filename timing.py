# coding=utf-8
from __future__ import division, absolute_import, print_function, unicode_literals
import time


class Timer(object):
    def __enter__(self):
        self.interval = None
        self.start = time.time()
        return self

    def __exit__(self, *args):
        self.end = time.time()
        self.interval = self.end - self.start

    def __str__(self):
        return "%.2f seconds" % (self.interval)
