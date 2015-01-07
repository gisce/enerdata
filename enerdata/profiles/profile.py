import bisect
from datetime import datetime, date, timedelta
from itertools import islice

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
        post_1 = bisect.bisect_right(self.coefs, coefs[-1])
        del self.coefs[pos_0:post_1]
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
