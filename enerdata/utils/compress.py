#!/usr/bin/env python
# -*- coding: utf-8 -*-

import struct
import gzip
import bz2


class CompressedFile (object):
    magic = None
    file_type = None
    mime_type = None
    proper_extension = None

    @classmethod
    def is_magic(cls, data):
        return data.startswith(cls.magic)


class GZFile (CompressedFile):
    magic = '\x1f\x8b\x08'
    file_type = 'gz'
    mime_type = 'compressed/gz'

    @classmethod
    def read(cls, c):
        return gzip.GzipFile(fileobj=c).read()


class BZFile (CompressedFile):
    magic = '\x42\x5a\x68'
    file_type = 'bz2'
    mime_type = 'compressed/bz'

    @classmethod
    def read(cls, c):
        return bz2.decompress(c.buf)


def is_compressed_file(f):
    start_of_file = f.read(5)
    f.seek(0)
    for cls in (GZFile, BZFile):
        if cls.is_magic(start_of_file):
            return True
    return False


class FileTypeNotSupportedException(Exception):
    pass


def get_compressed_file(f):
    start_of_file = f.read(5)
    f.seek(0)
    for cls in (GZFile, BZFile):
        if cls.is_magic(start_of_file):
            return cls
    raise FileTypeNotSupportedException
