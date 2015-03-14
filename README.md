# PyDMS: a minimal scanning system

A replacement for awful scanning software.

Acquires images from your scanner using SANE, processes them, and
spits out a PDF.

It should work on Mac and Linux.

There are a few bits which are specific to my setup at the moment. It
won't work for you out of the box.

## Requirements

    pip install enum pgmagick pillow pyinsane

## TODO

* Configuration
* Blank page detection
* A web interface
* Metadata extraction/storage
* Direct support for Camlistore

## See Also

* [Paperwork](https://github.com/jflesch/paperwork)
