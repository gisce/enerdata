import os
import bisect
from datetime import datetime, date, timedelta
from multiprocessing import Lock
from StringIO import StringIO
from urlparse import urlparse

from enerdata.datetime.timezone import TIMEZONE
from enerdata.metering.measure import Measure
from enerdata.utils.profile import *

import xlrd

SUPPORTED_TARIFFS = ['2.0A', '2.0.DHA', '2.0.DHS',
                     '2.1A', '2.1.DHA', '2.1.DHS',
                     '3.0A', '3.1A',
                     '6.1', '6.2', '6.3', '6.4']


class REELossProfileParser(object):

    @classmethod
    def get(cls, m, header=None):
        book = xlrd.open_workbook(file_contents=m.read())
        tariffs = book.sheet_names()
        coefs = dict()
        for tariff in tariffs:
            if tariff not in SUPPORTED_TARIFFS:
                raise Exception('Not supported tariff: {tariff}'.format(**locals()))

            dataset = book.sheet_by_name(tariff)
            _header= False
            for row_idx in range(dataset.nrows):
                row = dataset.row_values(row_idx)
                if row[0].startswith('Fecha'):
                    _header = True
                    continue
                if not _header:
                    continue

                date_raw = row[1]
                date = datetime.strptime(date_raw, '%d/%m/%Y')
                key = date.strftime('%Y%m%d')
                coefs.setdefault(key, {})
                if tariff not in coefs[key]:
                    coefs[key][tariff] = row[4:]
        return coefs


class REELossProfile(RemoteProfile):
    HOST = 'http://www.esios.ree.es'
    PATH = 'Solicitar?fileName={perff_file}&fileType=xls&idioma=es&tipoSolicitar=Publicaciones'

    @classmethod
    def get(cls, year, month):
        key = '%(year)s%(month)02i' % locals()
        perff_file = 'COEF_PERD_PEN_MM_%(key)s' % locals()
        uri = '/'.join([cls.HOST, cls.PATH.format(**locals())])
        return super(REELossProfile, cls).get('PERD', year, month, REELossProfileParser, uri, True)
