import bisect
from datetime import datetime, date, timedelta
from itertools import islice
from StringIO import StringIO

from enerdata.contracts.tariff import Tariff
from enerdata.datetime.timezone import TIMEZONE
from enerdata.datetime.station import get_station



class Coefficients(object):

    def __init__(self, coefs=None):
        if coefs is None:
            coefs = []
        assert isinstance(coefs, list)
        self.coefs = list(coefs)

    def insert_coefs(self, coefs):
        pos_0 = bisect.bisect_left(self.coefs, coefs[0])
        pos_1 = bisect.bisect_right(self.coefs, coefs[-1])
        del self.coefs[pos_0:pos_1]
        self.coefs.extend(coefs)

    def get_range(self, start, end):
        assert isinstance(start, date)
        assert isinstance(end, date)
        start = TIMEZONE.localize(datetime(
            start.year, start.month, start.day, 1), is_dst=True
        )
        # Sum one day to get the hour 00:00 of the next day
        end += timedelta(days=1)
        end = TIMEZONE.localize(datetime(
            end.year, end.month, end.day), is_dst=True
        ) + timedelta(seconds=1)
        pos = bisect.bisect_left(self.coefs, (start, {}))
        if pos == len(self.coefs):
            raise ValueError('start date not found in coefficients')
        end_pos = bisect.bisect_right(self.coefs, (end, {}))
        return self.coefs[pos:end_pos]

    def get_coefs_by_tariff(self, tariff, start, end):
        assert isinstance(tariff, Tariff)
        assert isinstance(start, date)
        assert isinstance(end, date)
        holidays = []
        sum_cofs = dict.fromkeys(tariff.energy_periods.keys(), 0)
        for hour, coef in self.get_range(start, end):
            if len(sum_cofs) > 1:
                period = tariff.get_period_by_date(hour, holidays)
                p_name = period.code
            else:
                p_name = sum_cofs.keys()[0]
            sum_cofs[p_name] += coef[tariff.cof]
        return sum_cofs


class Profiler(object):

    def __init__(self, coefficient):
        self.coefficient = coefficient

    def profile(self, tariff, measures):
        #{'PX': [(datetime(XXXX-XX-XX), 100), (datetime(XXXX-XX-XX), 110)]}
        measures = dict(
            (m.code, (m.date, m.consumption)) for m in sorted(measures)
        )
        start, end = measures.values()[0][0], measures.values()[0][-1]
        sum_cofs = self.coefficient.get_coefs_by_tariff(tariff, start, end)
        drag = 0
        for hour, cof in self.coeficient.get_range(start, end):
            # TODO: Implement holidays
            period = tariff.get_period_by_date(hour)
            pos = bisect.bisect_left(measures[period.code], hour)
            consumption = measures[period.code][pos][1]
            cof = cof[tariff.cof]
            hour_c = ((consumption * cof) / sum_cofs) + drag
            aprox = round(hour_c)
            drag = hour_c - aprox
            yield (
                hour,
                {
                    'aprox': aprox,
                    'drag': drag,
                    'consumption': consumption,
                    'consumption_date': measures[period.code][pos][0],
                    'sum_cofs': sum_cofs
                }
            )


class REEProfile(object):

    HOST = 'www.ree.es'
    PATH = '/sites/default/files/simel/perff'

    _CACHE = {}

    @classmethod
    def get(cls, year, month):
        import csv
        import httplib
        key = '%(year)s%(month)02i' % locals()
        if key in cls._CACHE:
            return cls_CACHE[key]
        perff_file = 'PERFF_%(key)s.gz' % locals()
        try:
            conn = httplib.HTTPConnection(cls.HOST)
            conn.request('GET', '%s/%s' % (cls.PATH, perff_file))
            r = conn.getresponse()
            if r.msg.type == 'application/x-gzip':
                import gzip
                c = StringIO(r.read())
                m = StringIO(gzip.GzipFile(fileobj=c).read())
                c.close()
                reader = csv.reader(m, delimiter=';')
                header = True
                cofs = []
                for vals in reader:
                    if header:
                        header = False
                        continue
                    if int(vals[3]) == 1:
                        n_hour = 1
                    dt = datetime(
                        int(vals[0]), int(vals[1]), int(vals[2])
                    )
                    day = TIMEZONE.localize(dt, is_dst=bool(not int(vals[4])))
                    day += timedelta(hours=n_hour)
                    n_hour += 1
                    cofs.append(
                        (TIMEZONE.normalize(day), {
                            'A': vals[5], 'B': vals[6], 'C': vals[7], 'D': vals[8]
                        })
                    )
                cls._CACHE[key] = cofs
                return cofs
            else:
                raise Exception('Profiles from REE not found')
        finally:
            conn.close()
