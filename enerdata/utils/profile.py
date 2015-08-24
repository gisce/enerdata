import os
import bisect
from datetime import datetime, date, timedelta
from multiprocessing import Lock
from StringIO import StringIO
from urlparse import urlparse, urljoin

from enerdata.datetime.timezone import TIMEZONE
from enerdata.metering.measure import Measure
from enerdata.utils.compress import is_compressed_file, get_compressed_file


class BaseProfile(object):
    _CACHE = {}

    @classmethod
    def get(cls, f, parser, header):
        if not parser:
            raise Exception('Parser required')

        m = StringIO(f.read())
        if is_compressed_file(m):
            cf = get_compressed_file(m)
            m = StringIO(cf.read(m))
        return parser.get(m, header)

    @classmethod
    def get_cached(cls, key):
        if key in cls._CACHE:
            return cls._CACHE[key]


class RemoteProfile(BaseProfile):
    down_lock = Lock()

    @classmethod
    def get(cls, tag, year, month, parser=None, uri=None, header=False):
        key = '%(tag)s%(year)s%(month)02i' % locals()
        cached = super(RemoteProfile, cls).get_cached(key)
        if cached:
            return cached

        if not uri:
            raise Exception('Profile uri required')
        url = urlparse(uri)
        host = url.netloc
        path = url.path + '?' + url.query

        cls.down_lock.acquire()
        import httplib
        conn = None
        try:
            conn = httplib.HTTPConnection(host)
            conn.request('GET', path)
            f = conn.getresponse()
            cls._CACHE[key] = super(RemoteProfile, cls).get(f, parser, header)
            return cls._CACHE[key]
        finally:
            if conn is not None:
                conn.close()
            cls.down_lock.release()

        if not os.path.isdir(path):
                raise Exception('Profile directory {path} not found'.format(**locals()))


class LocalProfile(BaseProfile):

    @classmethod
    def get(cls, tag, year, month, parser=None, path=None, header=False):
        key = '%(tag)s%(year)s%(month)02i' % locals()
        cached = super(LocalProfile, cls).get_cached(key)
        if cached:
            return cached

        if not path:
            raise Exception('Profile directory required')
        if not os.path.isfile(path):
            raise Exception('Profile file {path} not found'.format(**locals()))

        with open(path) as f:
                cls._CACHE[key] = super(LocalProfile, cls).get(f, parser, header)
                return cls._CACHE[key]
