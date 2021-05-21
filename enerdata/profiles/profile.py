from __future__ import division

import bisect
import logging
try:
    from collections import namedtuple, Counter
except ImportError:
    from backport_collections import namedtuple, Counter
from datetime import datetime, date, timedelta
from multiprocessing import Lock
from six.moves import StringIO
from dateutil.relativedelta import relativedelta
from decimal import Decimal

from enerdata.profiles import Dragger
from enerdata.contracts.tariff import (Tariff, T30A_one_period,
                                       T31A_one_period, T31A)
from enerdata.datetime.timezone import TIMEZONE
from enerdata.metering.measure import Measure, EnergyMeasure
from enerdata.datetime.holidays import get_holidays
from enerdata.datetime.work_and_holidays import get_num_of_workdays_holidays
from enerdata.datetime.solar_hour import convert_to_solar_hour

from os import path
import pandas as pd

logger = logging.getLogger(__name__)


class Coefficent(namedtuple('Coefficient', ['hour', 'cof'])):
    __slots__ = ()

    def __lt__(self, other):
        return self.hour < other.hour

    def __le__(self, other):
        return self.hour <= other.hour

    def __gt__(self, other):
        return self.hour > other.hour

    def __ge__(self, other):
        return self.hour >= other.hour


class Coefficients(object):
    def __init__(self, coefs=None):
        if coefs is None:
            coefs = []
        assert isinstance(coefs, list)
        self.coefs = list(coefs)

    def _check_pos(self, pos):
        if pos == len(self.coefs):
            raise ValueError('start date not found in coefficients')

    def insert_coefs(self, coefs):
        pos_0 = bisect.bisect_left(self.coefs, Coefficent(coefs[0][0], {}))
        pos_1 = bisect.bisect_right(self.coefs, Coefficent(coefs[-1][0], {}))
        logger.debug('Deleting from {start}({pos_0}) to {end}({pos_1})'.format(
            start=coefs[0][0], end=coefs[-1][0], pos_0=pos_0, pos_1=pos_1
        ))
        del self.coefs[pos_0:pos_1]
        for c in reversed(coefs):
            logger.debug('Inserting {c} into {pos_0}'.format(
                c=c, pos_0=pos_0
            ))
            self.coefs.insert(pos_0, c)

    def get(self, dt):
        assert isinstance(dt, datetime)
        if dt.dst() is None:
            dt = TIMEZONE.localize(dt)
        dt = TIMEZONE.normalize(dt)
        pos = bisect.bisect_left(self.coefs, Coefficent(dt, {}))
        self._check_pos(pos)
        return self.coefs[pos]

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
        pos = bisect.bisect_left(self.coefs, Coefficent(start, {}))
        self._check_pos(pos)
        end_pos = bisect.bisect_right(self.coefs, Coefficent(end, {}))
        return self.coefs[pos:end_pos]

    def get_coefs_by_tariff(self, tariff, start, end):
        assert hasattr(tariff, 'get_period_by_date')
        assert hasattr(tariff, 'energy_periods')
        assert isinstance(start, date)
        assert isinstance(end, date)
        sum_cofs = dict.fromkeys(tariff.energy_periods.keys(), 0)
        for hour, coef in self.get_range(start, end):
            if len(sum_cofs) > 1:
                period = tariff.get_period_by_date(hour)
                p_name = period.code
            else:
                p_name = sum_cofs.keys()[0]
            sum_cofs[p_name] += coef[tariff.cof]
        return sum_cofs


class Profiler(object):
    def __init__(self, coefficient):
        self.coefficient = coefficient

    def profile(self, tariff, measures, drag_method='hour'):
        """
        :param tariff:
        :param measures:
        :param drag_method: 'hour' means drag is passed to the next hour
                            'period' means drag is passed to the next hour for
                            the same period
        :return:
        """
        # {'PX': [(date(XXXX-XX-XX), 100), (date(XXXX-XX-XX), 110)]}
        _measures = list(measures)
        measures = {}
        for m in sorted(_measures):
            measures.setdefault(m.period.code, [])
            measures[m.period.code].append(m)
        measures_intervals = EnergyMeasure.intervals(_measures)
        logger.debug('Profiling {0} intervals'.format(len(measures_intervals)))
        for idx, measure_date in enumerate(measures_intervals):
            if idx + 1 == len(measures_intervals):
                break
            start = measure_date
            if idx > 0:
                start += timedelta(days=1)
            end = measures_intervals[idx + 1]
            logger.debug('Getting coeffs from {0} to {1}'.format(
                start, end
            ))
            sum_cofs = self.coefficient.get_coefs_by_tariff(tariff, start, end)
            dragger = Dragger()
            for hour, cof in self.coefficient.get_range(start, end):
                period = tariff.get_period_by_date(hour)
                if drag_method == 'hour':
                    dp = 'hour'
                else:
                    dp = period.code
                d = hour.date()
                if hour.hour == 0:
                    d -= timedelta(days=1)
                # To take the first measure
                if d == start:
                    d += timedelta(days=1)
                fake_m = Measure(d, period, 0)
                pos = bisect.bisect_left(measures.get(period.code, []), fake_m)
                pcode = period.code
                if pcode not in measures or pos >= len(measures[period.code]):
                    consumption = 0
                    consumption_date = None
                else:
                    consumption = measures[period.code][pos].consumption
                    consumption_date = measures[period.code][pos].date
                logger.debug('Hour: {0} Period: {1} Consumption: {2}'.format(
                    hour, period.code, consumption
                ))
                cof = cof[tariff.cof]
                hour_c = ((consumption * cof) / sum_cofs[period.code])
                aprox = dragger.drag(hour_c, key=dp)
                yield (
                    hour,
                    {
                        'aprox': aprox,
                        'drag': dragger[dp],
                        'consumption': consumption,
                        'consumption_date': consumption_date,
                        'sum_cofs': sum_cofs[period.code],
                        'cof': cof,
                        'period': period.code
                    }
                )


class REEProfile(object):
    HOST = 'www.ree.es'
    PATH = '/sites/default/files/simel/perff'
    down_lock = Lock()

    _CACHE = {}

    @classmethod
    def get_range(cls, start, end):
        cofs = []
        start = datetime(start.year, start.month, 1)
        end = datetime(end.year, end.month, 1)
        while start <= end:
            logger.debug('Downloading coefficients for {0}/{1}'.format(
                start.month, start.year
            ))
            cofs.extend(REEProfile.get(start.year, start.month))
            start += relativedelta(months=1)
        return cofs

    @classmethod
    def get(cls, year, month):
        try:
            import ssl
            try:
                _create_unverified_https_context = ssl._create_unverified_context
            except AttributeError:
                pass
            else:
                ssl._create_default_https_context = _create_unverified_https_context
        except ImportError:
            pass
        try:
            cls.down_lock.acquire()
            import csv
            import httplib
            key = '%(year)s%(month)02i' % locals()
            conn = None
            if key in cls._CACHE:
                logger.debug('Using CACHE for REEProfile {0}'.format(key))
                return cls._CACHE[key]
            perff_file = 'PERFF_%(key)s.gz' % locals()
            conn = httplib.HTTPSConnection(cls.HOST)
            conn.request('GET', '%s/%s' % (cls.PATH, perff_file))
            logger.debug('Downloading REEProfile from {0}/{1}'.format(
                cls.PATH, perff_file
            ))
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
                    cofs.append(Coefficent(
                        TIMEZONE.normalize(day), dict(
                            (k, float(vals[i])) for i, k in enumerate('ABCD', 5)
                        ))
                    )
                cls._CACHE[key] = cofs
                return cofs
            else:
                raise Exception('Profiles from REE not found')
        finally:
            if conn is not None:
                conn.close()
            cls.down_lock.release()


class REProfile(object):
    translate_month = {
        1: 'Enero',
        2: 'Febrero',
        3: 'Marzo',
        4: 'Abril',
        5: 'Mayo',
        6: 'Junio',
        7: 'Julio',
        8: 'Agosto',
        9: 'Septiembre',
        10: 'Octubre',
        11: 'Noviembre',
        12: 'Diciembre'
    }

    @classmethod
    def get_range(cls, start, end):
        sheet_name = 'zona_{}'.format(cls.climatic_zone)
        filename = path.join(
            path.dirname(path.realpath(__file__)), 'data/coefficients_RE.xlsx'
        )
        df = pd.read_excel(filename, sheet_name=sheet_name)
        key = df.keys()[0]
        cofs = []
        while start <= end:
            month = cls.translate_month[start.month]
            solar_hour = convert_to_solar_hour(start)
            if solar_hour.hour != 0:
                hour = solar_hour.hour
            else:
                hour = 24
            coff_value = float(df[df[key] == month][hour])
            coff = Coefficent(start, {'A': coff_value})
            cofs.append(coff)
            start += relativedelta(hours=1)
        return cofs

    @classmethod
    def validate_exported_energy(cls, measures):
        """
        Check if there are ProfileHour with energy != 0 in periods with RE coefficient == 0
        :param measures: A list ProfileHour objects
        :return valid: A boolean that indicates if all the profiles in measures are valid
        :return invalid_profiles: A list containing the invalid profiles in measures
        """
        # Check if measures list is valid
        valid = True
        # Save invalid profiles
        invalid_profiles = []
        # get and iterate RE coefficients
        coefficients = cls.get_range(min(measures).date, max(measures).date)
        # iterate all RE measures
        for measure in measures:
            # if energy value is not zero
            if measure[1] != 0:
                # fetch coeff by profile date
                cof = False
                for c in coefficients:
                    if c.hour == measure[0]:
                        cof = c
                        break
                if cof:
                    # if coeff is zero
                    if cof.cof['A'] == 0:
                        # replace energy value by 'warning'
                        invalid_profiles.append(measure)
                        # mark measures as invalid
                        valid = False
        return valid, invalid_profiles


class REProfileZone1(REProfile):
    climatic_zone = 1


class REProfileZone2(REProfile):
    climatic_zone = 2


class REProfileZone3(REProfile):
    climatic_zone = 3


class REProfileZone4(REProfile):
    climatic_zone = 4


class REProfileZone5(REProfile):
    climatic_zone = 5


class REProfileHydraulic(REProfile):
    @classmethod
    def get_range(cls, start, end):
        filename = path.join(path.dirname(path.realpath(__file__)), 'data/coefficients_HIDRO_RE.csv')
        df = pd.read_csv(filename)
        cofs = []
        while start <= end:
            month = cls.translate_month[start.month]
            coff_value = float(df[df['MES'] == month]['Factor de funcionamiento'])
            coff = Coefficent(start, {'A': coff_value})
            cofs.append(coff)
            start += relativedelta(hours=1)
        return cofs


class REProfileFlat(REProfile):
    flat_cof = 0.85
    @classmethod
    def get_range(cls, start, end):
        cofs = []
        while start <= end:
            cofs.append(Coefficent(start, {'A': cls.flat_cof}))
            start += relativedelta(hours=1)
        return cofs


class ProfileHour(namedtuple('ProfileHour', ['date', 'measure', 'valid', 'accumulated'])):

    __slots__ = ()

    def __lt__(self, other):
        return self.date < other.date

    def __le__(self, other):
        return self.date <= other.date

    def __gt__(self, other):
        return self.date > other.date

    def __ge__(self, other):
        return self.date >= other.date


class Profile(object):
    """A Profile object representing hours and consumption.
    """

    def __init__(self, start, end, measures, accumulated=None, drag_by_periods=True):
        self.measures = measures[:]
        self.gaps = []  # Containing the gaps and invalid measures
        self.adjusted_periods = [] # If a period is adjusted
        self.start_date = start
        self.end_date = end
        self.profile_class = REEProfile

        assert type(drag_by_periods) == bool, "drag_by_periods must be a Boolean"
        self.drag_by_periods = drag_by_periods

        self.accumulated = Decimal(0)
        if accumulated:
            assert type(accumulated) == float or isinstance(accumulated, Decimal), "Provided accumulated must be a Decimal or a float"
            assert accumulated < 1 and accumulated > -1, "Provided accumulated '{}' must be -1 < accumulated < 1".format(accumulated)
            self.accumulated = accumulated

        measures_by_date = dict(
            [(m.date, m.measure) for m in measures if m.valid]
        )
        # End is included
        while start <= end:
            if measures_by_date.pop(TIMEZONE.normalize(start), None) is None:
                self.gaps.append(start)
            start += timedelta(hours=1)

    @property
    def n_hours(self):
        # End date is included, we have to sum one hour
        return int((self.end_date - self.start_date).total_seconds() / 3600) + 1

    @property
    def n_hours_measures(self):
        return len(self.measures)

    @property
    def total_consumption(self):
        return sum(x[1] for x in self.measures)

    @property
    def first_day_of_month(self):
        return self.end_date.day == 1 and self.end_date.hour > 0

    @staticmethod
    def simple_dragger(measures):
        dragger = Dragger()
        for idx, measure in enumerate(measures):
            values = measure._asdict()
            consumption = dragger.drag(measure.measure)
            values['measure'] = consumption
            measures[idx] = measure._replace(**values)
        return measures

    def get_hours_per_period(self, tariff, only_valid=False):
        assert isinstance(tariff, Tariff)
        hours_per_period = Counter()
        if only_valid:
            for m in self.measures:
                if m.valid:
                    period = tariff.get_period_by_date(m.date)
                    hours_per_period[period.code] += 1
        else:
            start_idx = self.start_date
            end = self.end_date
            while start_idx <= end:
                period = tariff.get_period_by_date(start_idx)
                hours_per_period[period.code] += 1
                start_idx += timedelta(hours=1)
        return hours_per_period

    def get_consumption_per_period(self, tariff):
        assert isinstance(tariff, Tariff)
        consumption_per_period = Counter()
        for period in tariff.energy_periods:
            consumption_per_period[period] = 0
        for m in self.measures:
            if m.valid:
                period = tariff.get_period_by_date(m.date)
                consumption_per_period[period.code] += m.measure
        return consumption_per_period

    def get_estimable_hours(self, tariff):
        assert isinstance(tariff, Tariff)
        total_hours = self.get_hours_per_period(tariff)
        valid_hours = self.get_hours_per_period(tariff, only_valid=True)
        estimable_hours = {}
        for period in total_hours.keys():
            estimable_hours[period] = total_hours[period] - valid_hours[period]
        return estimable_hours

    def get_estimable_consumption(self, tariff, balance):
        assert isinstance(tariff, Tariff)
        consumption_per_period = self.get_consumption_per_period(tariff)
        estimable = {}
        for period in consumption_per_period:
            estimable[period] = balance[period] - consumption_per_period[period]
        return estimable

    def estimate(self, tariff, balance):
        assert isinstance(tariff, Tariff)
        logger.debug('Estimating for tariff: {0}'.format(
            tariff.code
        ))

        # Adapt balance for simplified T30A with just one period
        if isinstance(tariff, T30A_one_period) or isinstance(tariff, T31A_one_period):
            balance = {
                "P1": sum([values for values in balance.values()])
            }
        # Adapt T31A6P adding P4 to P1
        if isinstance(tariff, T31A) and balance.get('P4', 0) > 0:
            balance['P1'] += balance['P4']
            balance['P4'] = 0

        measures = [x for x in self.measures if x.valid]
        start = self.start_date
        end = self.end_date
        # - REE cofs get from (year/month)
        # - Simel cofs get from (year/month/day hour) - can't substract one day
        if self.first_day_of_month or not issubclass(self.profile_class,
                                                     REEProfile):
            cofs = self.profile_class.get_range(start, end)
        else:
            cofs = self.profile_class.get_range(
                start, end - relativedelta(days=1)
            )
        cofs = Coefficients(cofs)
        cofs_per_period = Counter()

        for gap in self.gaps:
            period = tariff.get_period_by_date(gap)
            gap_cof = cofs.get(gap)
            cofs_per_period[period.code] += gap_cof.cof[tariff.cof]

        logger.debug('Coefficients per period calculated: {0}'.format(
            cofs_per_period
        ))

        energy_per_period = self.get_estimable_consumption(tariff, balance)
        energy_per_period_rem = energy_per_period.copy()

        dragger = Dragger()

        # Initialize the Dragger with passed accumulated value
        if len(self.gaps) > 0:
            # Drag by_hours
            if not self.drag_by_periods:
                init_drag_key = "default"
            else:
                init_drag_key = tariff.get_period_by_date(self.gaps[0]).code

            dragger.drag(self.accumulated, key=init_drag_key)

            for idx, gap in enumerate(self.gaps):
                logger.debug('Gap {0}/{1}'.format(
                    idx + 1, len(self.gaps)
                ))
                period = tariff.get_period_by_date(gap)

                drag_key = period.code if not self.drag_by_periods else "default"

                gap_cof = cofs.get(gap).cof[tariff.cof]
                energy = energy_per_period[period.code]
                # If the balance[period] < energy_profile[period] fill with 0
                if energy < 0:
                    energy = 0

                try:
                    gap_energy = (energy * gap_cof) / cofs_per_period[period.code]
                except ZeroDivisionError as error:
                    gap_energy = 0
                    logger.debug(error)

                aprox = dragger.drag(gap_energy, key=drag_key)
                energy_per_period_rem[period.code] -= gap_energy

                logger.debug(
                    'Energy for hour {0} is {1}. {2} Energy {3}/{4}'.format(
                        gap, aprox, period.code,
                        energy_per_period_rem[period.code], energy
                ))
                pos = bisect.bisect_left(measures, ProfileHour(gap, 0, True, 0.0))
                profile_hour = ProfileHour(TIMEZONE.normalize(gap), aprox, True, dragger[drag_key])

                measures.insert(pos, profile_hour)

        profile = Profile(self.start_date, self.end_date, measures)
        return profile

    def adjust(self, tariff, balance, diff=0):
        # Adjust values
        if self.gaps:
            raise Exception('Is not possible to adjust a profile with gaps')
        profile = Profile(self.start_date, self.end_date, self.measures)
        dragger = Dragger()
        energy_per_period = profile.get_consumption_per_period(tariff)
        for period_name, period_balance in balance.items():
            period_profile = energy_per_period[period_name]
            margin_bottom = period_balance - diff
            margin_top = period_balance + diff
            if not margin_bottom <= period_profile <= margin_top:
                profile.adjusted_periods.append(period_name)
                for idx, measure in enumerate(profile.measures):
                    period = tariff.get_period_by_date(measure.date).code
                    if period != period_name:
                        continue
                    values = measure._asdict()
                    values['valid'] = True
                    if not energy_per_period[period]:
                        values['measure'] = dragger.drag(measure.measure * 0)
                    else:
                        values['measure'] = dragger.drag(measure.measure * (
                            balance[period] / energy_per_period[period]
                        ))
                    profile.measures[idx] = measure._replace(**values)
        return profile

    def fixit(self, tariff, balance, diff=0):
        # Fill the gaps
        profile = self.estimate(tariff, balance)
        # Adjust to the balance
        profile = profile.adjust(tariff, balance, diff)

        if isinstance(tariff, T31A) and tariff.low_voltage_measure:
            # Apply losses
            profile.measures = tariff.apply_curve_losses(profile.measures)
            profile.measures = self.simple_dragger(profile.measures)
        return profile

    def __repr__(self):
        return '<Profile ({0} - {1}) {2}h {3}kWh>'.format(
            self.start_date, self.end_date, self.n_hours, self.total_consumption
        )
