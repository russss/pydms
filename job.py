# coding=utf-8
from __future__ import division, absolute_import, print_function, unicode_literals
from enum import Enum


class Side(Enum):
    front = 1
    back = 2
    duplex = 3


class Job(object):
    def __init__(self):
        self.images = None
        self.filename = None
        self.side = None
