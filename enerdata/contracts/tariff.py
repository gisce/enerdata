# -*- coding: utf-8 -*-
import calendar
from datetime import datetime, timedelta
from enerdata.contracts.normalized_power import NormalizedPower
from enerdata.datetime.station import get_station
from enerdata.datetime.holidays import get_holidays
from enerdata.datetime.timezone import TIMEZONE
from enerdata.datetime.work_and_holidays import get_num_of_workdays_holidays
from enerdata.contracts.electrical_seasons import PERIODS_2x_BY_ELECTRIC_ZONE_CIR03_2020, \
    PERIODS_3x_BY_ELECTRIC_ZONE_CIR03_2020, PERIODS_6x_BY_ELECTRIC_ZONE, DAYTYPE_BY_ELECTRIC_ZONE, \
    DAYTYPE_BY_ELECTRIC_ZONE_CIR03_2020, TARIFFS_START_DATE_STR, PERIODS_6x_BY_ELECTRIC_ZONE_CIR03_2020


def check_range_hours(hours):
    before = (0, 0)
    for range_hours in sorted(hours):
        start, end = range_hours
        if start >= end:
            return False
        if start < 0 or start > 24:
            return False
        if end < 1 or end > 24:
            return False
        if start < before[1]:
            return False
        before = (start, end)
    return True


def are_powers_ascending(powers):
    power_ant = 0
    for power_new in powers:
        if power_new < power_ant:
            return False
        power_ant = power_new

    return True


def set_day_type_electric_zone(current_date):
    if current_date.strftime('%Y-%m-%d') >= TARIFFS_START_DATE_STR:
        day_type_by_zone = DAYTYPE_BY_ELECTRIC_ZONE_CIR03_2020
    else:
        day_type_by_zone = DAYTYPE_BY_ELECTRIC_ZONE
    return day_type_by_zone

def get_daytype_by_date_and_zone(date_time, zone='1', holidays=None):
    """
    Calcultes daytype from date and zone.
    :param date_time in datetime format
    :param zone in ['1', '2', '3' ,'4', '5']
    :param holidays list of holidays
    :returns char ('A', 'A1', 'B', 'B1', 'C', 'D')
    """
    is_weekend = (
        calendar.weekday(
            date_time.year,
            date_time.month,
            date_time.day
        ) in (5, 6)
    )
    if is_weekend or date_time.date() in holidays:
        return 'D'

    day_type_by_zone = set_day_type_electric_zone(date_time)

    monthday = date_time.strftime('%m/%d')
    for daytype, periods in day_type_by_zone[zone].items():
        for period in periods:
            if period[0] <= monthday <= period[1]:
                return daytype


class Tariff(object):
    """Energy DSO Tariff.
    """
    def __init__(self, code=None, **kwargs):
        self.code = code
        self._periods = tuple()
        self.cof = None
        self.require_powers_above_min_power = False
        self.require_summer_winter_hours = True
        self.periods_validation = True

    @property
    def periods(self):
        return self._periods

    @periods.setter
    def periods(self, value):
        self._periods = value
        validate = self.periods_validation
        hours = {
            'holidays': [],
            'no_holidays': []
        }
        for period in self.energy_periods.values():
            if period.holiday:
                hours['holidays'].append(period)
            else:
                hours['no_holidays'].append(period)

        for station in ('summer', 'winter'):
            for holiday in (False, True):
                total_hours = 0
                range_hours = []
                for period in self.energy_periods.values():
                    if period.holiday == holiday:
                        total_hours += getattr(period, 'total_%s_hours' % station)
                        range_hours += getattr(period, '%s_hours' % station)
                range_hours = sorted(range_hours)
                if total_hours != 24 and validate:
                    if (holiday and total_hours) or not holiday:
                        raise ValueError(
                            'The sum of hours in %s%s must be 24h: %s'
                            % (station, holiday and ' (in holidays)' or '',
                               range_hours)
                        )
                if not check_range_hours(range_hours) and validate:
                    raise ValueError(
                        'Invalid range of hours in %s%s: %s'
                        % (station, holiday and ' (in holidays)' or '',
                           range_hours)
                    )

    @property
    def energy_periods(self):
        return dict((p.code, p) for p in self.periods if p.type == 'te')

    @property
    def power_periods(self):
        return dict((p.code, p) for p in self.periods if p.type == 'tp')

    def get_number_of_periods(self):
        return len([p for p in self.periods if p.type == 'te'])

    def get_min_power(self):
        return self.min_power

    def get_max_power(self):
        return self.max_power

    def get_period_by_date(self, date_time, holidays=None, magn='te'):
        station = get_station(date_time)
        if holidays is None:
            holidays = []
        date = date_time.date()
        if (calendar.weekday(date.year, date.month, date.day) in (5, 6)
                or date in holidays):
            holiday = True
        else:
            holiday = False
        periods = self.energy_periods
        if magn == 'tp':
            periods = self.power_periods
        for period in periods.values():
            if period.holiday == holiday or not self.has_holidays_periods:
                if period.daytype:
                    zone = period.geom_zone
                    daytype = get_daytype_by_date_and_zone(
                        date_time, zone, holidays
                    )
                    periods_ranges = period.periods_by_zone_and_day[zone][daytype]
                    range_list = periods_ranges[int(period.code[-1]) - 1]
                else:
                    range_list = getattr(period, '%s_hours' % station)
                for range_h in range_list:
                    if range_h[0] <= date_time.hour < range_h[1]:
                        return period
            elif magn == 'tp':
                if period.daytype:
                    zone = period.geom_zone
                    daytype = get_daytype_by_date_and_zone(
                        date_time, zone, holidays
                    )
                    periods_ranges = period.periods_by_zone_and_day[zone][daytype]
                    range_list = periods_ranges[int(period.code[-1]) - 1]
                else:
                    if holiday and self.has_holidays_hours_in_periods:
                        if period.holiday_hours:
                            range_list = getattr(period, 'holiday_hours')
                        else:
                            continue
                    else:
                        range_list = getattr(period, '%s_hours' % station)
                for range_h in range_list:
                    if range_h[0] <= date_time.hour < range_h[1]:
                        return period
        return None

    def get_hours_by_period(self, start_time, end_time, holidays=None,
                            zone='1'):
        hours_by_period = {}
        for period in self.energy_periods.values():
            hours_by_period[period.code] = period.get_hours_between_dates(
                start_time, end_time, holidays, zone
            )
        return hours_by_period

    def get_period_by_timestamp(self, timestamp):
        """
        Gets the number of energy period
        :param timestamp: datetime in format 'YYYY-MM-DD HH'
        :return: period number
        """
        day, hours = timestamp.split(' ')
        dt_tz = TIMEZONE.normalize(TIMEZONE.localize(datetime.strptime(day, '%Y-%m-%d')) + timedelta(hours=int(hours)))
        # "get_period_by_date" expects a local timestamp without timezone
        # decreases 1 minute because is final datetime open interval (not included)
        dt = dt_tz.replace(tzinfo=None) - timedelta(minutes=1)
        return self.get_period_by_date(dt).code

    @property
    def has_holidays_periods(self):
        return any(p.holiday for p in self.energy_periods.values())

    @property
    def has_holidays_hours_in_periods(self):
        return any(p.holiday_hours for p in self.periods)

    @property
    def has_holidays_periods(self):
        return any(p.holiday for p in self.energy_periods.values())

    def is_maximum_power_correct(self, max_pow):
        return self.min_power < max_pow <= self.max_power

    def is_minimum_powers_correct(self, min_pow):
        if self.require_powers_above_min_power:
            return self.min_power < min_pow <= self.max_power
        else:
            return True

    @staticmethod
    def are_powers_normalized(powers):
        np = NormalizedPower()
        for power in powers:
            if not np.is_normalized(int(power * 1000)):
                return False

        return True

    def evaluate_powers_all_checks(self, powers):
        """

        :param powers: [pow1, pow2,...]
        :return: [Error1, Error2] if errors else []
        """
        errors = []
        if min(powers) <= 0:
            errors.append(NotPositivePower())
        if not len(self.power_periods) == len(powers):
            errors.append(IncorrectPowerNumber(len(powers), len(self.power_periods)))
        if not self.is_maximum_power_correct(max(powers)):
            errors.append(IncorrectMaxPower(max(powers), self.min_power, self.max_power))
        if not self.is_minimum_powers_correct(min(powers)):
            errors.append(IncorrectMinPower(min(powers), self.min_power, self.max_power))
        if not self.are_powers_normalized(powers):
            errors.append(NotNormalizedPower())

        return errors

    def evaluate_powers(self, powers):
        if min(powers) <= 0:
            raise NotPositivePower()
        if not len(self.power_periods) == len(powers):
            raise IncorrectPowerNumber(len(powers), len(self.power_periods))
        if not self.is_maximum_power_correct(max(powers)):
            raise IncorrectMaxPower(max(powers), self.min_power, self.max_power)
        if not self.is_minimum_powers_correct(min(powers)):
            raise IncorrectMinPower(min(powers), self.min_power, self.max_power)
        if not self.are_powers_normalized(powers):
            raise NotNormalizedPower()

        return True

    def correct_powers(self, powers):
        raise NotImplementedError


class TariffPreTD(Tariff):
    """Energy DSO Tariff.
    """
    def __init__(self, code=None):
        self.code = code
        self._periods = tuple()
        self.cof = None
        self.require_powers_above_min_power = False
        self.require_summer_winter_hours = True

    @property
    def periods(self):
        return self._periods

    @periods.setter
    def periods(self, value):
        self._periods = value
        if self.require_summer_winter_hours:
            hours = {
                'holidays': [],
                'no_holidays': []
            }
            for period in self.energy_periods.values():
                if period.holiday:
                    hours['holidays'].append(period)
                else:
                    hours['no_holidays'].append(period)

            for station in ('summer', 'winter'):
                for holiday in (False, True):
                    total_hours = 0
                    range_hours = []
                    for period in self.energy_periods.values():
                        if period.holiday == holiday:
                            total_hours += getattr(period, 'total_%s_hours' % station)
                            range_hours += getattr(period, '%s_hours' % station)
                    range_hours = sorted(range_hours)
                    if total_hours != 24:
                        if (holiday and total_hours) or not holiday:
                            raise ValueError(
                                'The sum of hours in %s%s must be 24h: %s'
                                % (station, holiday and ' (in holidays)' or '',
                                range_hours)
                            )
                    if not check_range_hours(range_hours):
                        raise ValueError(
                            'Invalid range of hours in %s%s: %s'
                            % (station, holiday and ' (in holidays)' or '',
                               range_hours)
                        )

    @property
    def energy_periods(self):
        return dict((p.code, p) for p in self.periods if p.type == 'te')

    @property
    def power_periods(self):
        return dict((p.code, p) for p in self.periods if p.type == 'tp')

    def get_number_of_periods(self):
        return len([p for p in self.periods if p.type == 'te'])

    def get_min_power(self):
        return self.min_power

    def get_max_power(self):
        return self.max_power

    def get_period_by_date(self, date_time):
        datetime_previous_hour = date_time - timedelta(hours=1)
        station = get_station(datetime_previous_hour)
        date = datetime_previous_hour.date()
        holidays = get_holidays(date.year)
        if (calendar.weekday(date.year, date.month, date.day) in (5, 6) or
                date in holidays):
            holiday = True
        else:
            holiday = False

        # Map hour 0 to 24
        hour = date_time.hour or 24
        for period in self.periods:
            if period.holiday == holiday or not self.has_holidays_periods:
                for range_h in getattr(period, '%s_hours' % station):
                    if range_h[0] < hour <= range_h[1]:
                        return period
        return None


    @property
    def has_holidays_periods(self):
        return any(p.holiday for p in self.energy_periods.values())

    def is_maximum_power_correct(self, max_pow):
        return self.min_power < max_pow <= self.max_power

    def is_minimum_powers_correct(self, min_pow):
        if self.require_powers_above_min_power:
            return self.min_power < min_pow <= self.max_power
        else:
            return True

    @staticmethod
    def are_powers_normalized(powers):
        np = NormalizedPower()
        for power in powers:
            if not np.is_normalized(int(power * 1000)):
                return False

        return True

    def evaluate_powers_all_checks(self, powers):
        """

        :param powers: [pow1, pow2,...]
        :return: [Error1, Error2] if errors else []
        """
        errors = []
        if min(powers) <= 0:
            errors.append(NotPositivePower())
        if not len(self.power_periods) == len(powers):
            errors.append(IncorrectPowerNumber(len(powers), len(self.power_periods)))
        if not self.is_maximum_power_correct(max(powers)):
            errors.append(IncorrectMaxPower(max(powers), self.min_power, self.max_power))
        if not self.is_minimum_powers_correct(min(powers)):
            errors.append(IncorrectMinPower(min(powers), self.min_power, self.max_power))
        if not self.are_powers_normalized(powers):
            errors.append(NotNormalizedPower())

        return errors

    def evaluate_powers(self, powers):
        if min(powers) <= 0:
            raise NotPositivePower()
        if not len(self.power_periods) == len(powers):
            raise IncorrectPowerNumber(len(powers), len(self.power_periods))
        if not self.is_maximum_power_correct(max(powers)):
            raise IncorrectMaxPower(max(powers), self.min_power, self.max_power)
        if not self.is_minimum_powers_correct(min(powers)):
            raise IncorrectMinPower(min(powers), self.min_power, self.max_power)
        if not self.are_powers_normalized(powers):
            raise NotNormalizedPower()

        return True

    def correct_powers(self, powers):
        raise NotImplementedError


class TariffPeriod(object):
    """Tariff period.
    """
    def __init__(self, code, ptype, **kwargs):
        assert ptype in ('te', 'tp')
        self.code = code
        self.type = ptype
        winter_hours = kwargs.pop('winter_hours', [(0, 24)])
        if not check_range_hours(winter_hours):
            raise ValueError('Invalid winter hours')
        self.winter_hours = winter_hours
        summer_hours = kwargs.pop('summer_hours', [(0, 24)])
        if not check_range_hours(summer_hours):
            raise ValueError('Invalid summer hours')
        self.summer_hours = summer_hours
        holiday_hours = kwargs.pop('holiday_hours', [])
        if holiday_hours:
            if not check_range_hours(holiday_hours):
                raise ValueError('Invalid holiday hours')
        self.holiday = kwargs.pop('holiday', False)
        self.tariff_has_holiday_periods = kwargs.pop(
            'tariff_has_holiday_periods', self.holiday
        )
        # daytype tariffs (6.x)
        self.periods_by_zone_and_day = kwargs.pop('periods_by_zone_and_day', PERIODS_6x_BY_ELECTRIC_ZONE)
        self.daytype = kwargs.pop('daytype', False)
        if self.daytype:
            self.geom_zone = kwargs.pop('geom_zone', '1')
            periods_dict = self.periods_by_zone_and_day[self.geom_zone]
            for daytype in periods_dict.keys():
                hours = [p for lp in periods_dict[daytype] if lp for p in lp]
                if not check_range_hours(hours):
                    raise ValueError(
                        'Invalid {0} hours for {1} '
                        'geographic zone '.format(daytype, self.geom_zone)
                    )

    @property
    def total_summer_hours(self):
        hours = 0
        for range_h in self.summer_hours:
            hours += (range_h[1] - range_h[0])
        return hours

    @property
    def total_winter_hours(self):
        hours = 0
        for range_h in self.winter_hours:
            hours += (range_h[1] - range_h[0])
        return hours


class T20A(TariffPreTD):
    def __init__(self):
        super(T20A, self).__init__()
        self.code = '2.0A'
        self.cof = 'A'
        self.periods = (
            TariffPeriod('P1', 'te'),
            TariffPeriod('P1', 'tp')
        )
        self.min_power = 0
        self.max_power = 10
        self.type = 'BT'

    def correct_powers(self, powers):
        try:
            if self.evaluate_powers(powers):
                return powers
        except:
            pass

        norm_power = NormalizedPower().get_norm_powers(
            int(self.min_power * 1000), int(self.max_power * 1000)
        ).next()

        return [norm_power / 1000.0] * len(self.power_periods)


class T20DHA(T20A):
    def __init__(self):
        super(T20DHA, self).__init__()
        self.code = '2.0DHA'
        self.cof = 'B'
        self.periods = (
            TariffPeriod(
                'P1', 'te',
                winter_hours=[(12, 22)],
                summer_hours=[(13, 23)]
            ),
            TariffPeriod(
                'P2', 'te',
                winter_hours=[(0, 12), (22, 24)],
                summer_hours=[(0, 13), (23, 24)]
            ),
            TariffPeriod(
                'P1', 'tp'
            )
        )


class T20DHS(T20DHA):
    def __init__(self):
        super(T20DHS, self).__init__()
        self.code = '2.0DHS'
        self.cof = 'D'
        self.periods = (
            TariffPeriod(
                'P1', 'te',
                winter_hours=[(13, 23)],
                summer_hours=[(13, 23)]
            ),
            TariffPeriod(
                'P2', 'te',
                winter_hours=[(0, 1), (7, 13), (23, 24)],
                summer_hours=[(0, 1), (7, 13), (23, 24)]
            ),
            TariffPeriod(
                'P3', 'te',
                winter_hours=[(1, 7)],
                summer_hours=[(1, 7)]
            ),
            TariffPeriod(
                'P1', 'tp'
            )
        )


class T21A(T20A):
    def __init__(self):
        super(T21A, self).__init__()
        self.code = '2.1A'
        self.cof = 'A'
        self.min_power = 10
        self.max_power = 15


class T21DHA(T20DHA):
    def __init__(self):
        super(T21DHA, self).__init__()
        self.code = '2.1DHA'
        self.cof = 'B'
        self.min_power = 10
        self.max_power = 15


class T21DHS(T20DHS):
    def __init__(self):
        super(T21DHS, self).__init__()
        self.code = '2.1DHS'
        self.cof = 'D'
        self.min_power = 10
        self.max_power = 15


class T30A(TariffPreTD):
    def __init__(self):
        super(T30A, self).__init__()
        self.code = '3.0A'
        self.cof = 'C'
        self.min_power = 15
        self.max_power = 1000000
        self.require_powers_above_min_power = True
        self.type = 'BT'
        self.periods = (
            TariffPeriod(
                'P1', 'te',
                winter_hours=[(18, 22)],
                summer_hours=[(11, 15)]
            ),
            TariffPeriod(
                'P2', 'te',
                winter_hours=[(8, 18), (22, 24)],
                summer_hours=[(8, 11), (15, 24)]
            ),
            TariffPeriod(
                'P3', 'te',
                winter_hours=[(0, 8)],
                summer_hours=[(0, 8)]
            ),
            TariffPeriod(
                'P4', 'te',
                holiday=True,
                winter_hours=[(18, 22)],
                summer_hours=[(11, 15)]
            ),
            TariffPeriod(
                'P5', 'te',
                holiday=True,
                winter_hours=[(8, 18), (22, 24)],
                summer_hours=[(8, 11), (15, 24)]
            ),
            TariffPeriod(
                'P6', 'te',
                holiday=True,
                winter_hours=[(0, 8)],
                summer_hours=[(0, 8)]
            ),
            TariffPeriod(
                'P1', 'tp'
            ),
            TariffPeriod(
                'P2', 'tp'
            ),
            TariffPeriod(
                'P3', 'tp'
            )
        )


class T30ANoFestivos(T30A):
    def __init__(self):
        super(T30ANoFestivos, self).__init__()
        self.periods = (
            TariffPeriod(
                'P1', 'te',
                winter_hours=[(18, 22)],
                summer_hours=[(11, 15)]
            ),
            TariffPeriod(
                'P2', 'te',
                winter_hours=[(8, 18), (22, 24)],
                summer_hours=[(8, 11), (15, 24)]
            ),
            TariffPeriod(
                'P3', 'te',
                winter_hours=[(0, 8)],
                summer_hours=[(0, 8)]
            ),
            TariffPeriod(
                'P1', 'tp'
            ),
            TariffPeriod(
                'P2', 'tp'
            ),
            TariffPeriod(
                'P3', 'tp'
            )
        )

class T30A_one_period(T30A):
    """
    A 3.0A with one unique period
    """
    def __init__(self):
        super(T30A_one_period, self).__init__()
        self.periods = (
            TariffPeriod('P1', 'te'),
            TariffPeriod('P1', 'tp')
        )


class T31A(T30A):
    """
    3.1A Tariff patched with 3.1ALB
    """
    def __init__(self, kva=None):
        super(T31A, self).__init__()
        self.code = '3.1A'
        self.cof = 'C'
        self.min_power = 1
        self.max_power = 450
        self.losses = 0.04
        self.type = 'AT'
        self.require_powers_above_min_power = False
        if kva:
            if not isinstance(kva, (int, float)):
                raise ValueError('kva must be an enter value')
            self.low_voltage_measure = True
            self.kva = kva
        else:
            self.low_voltage_measure = False
        self.hours_by_period = {
            'P1': 6,
            'P2': 10,
            'P3': 8,
            'P4': 0,
            'P5': 6,
            'P6': 18
        }
        self.periods = (
            TariffPeriod(
                'P1', 'te',
                winter_hours=[(17, 23)],
                summer_hours=[(10, 16)]
            ),
            TariffPeriod(
                'P2', 'te',
                winter_hours=[(8, 17), (23, 24)],
                summer_hours=[(8, 10), (16, 24)]
            ),
            TariffPeriod(
                'P3', 'te',
                winter_hours=[(0, 8)],
                summer_hours=[(0, 8)]
            ),
            TariffPeriod(
                'P5', 'te',
                holiday=True,
                winter_hours=[(18, 24)],
                summer_hours=[(18, 24)]
            ),
            TariffPeriod(
                'P6', 'te',
                holiday=True,
                winter_hours=[(0, 18)],
                summer_hours=[(0, 18)]
            ),
            TariffPeriod(
                'P1', 'tp'
            ),
            TariffPeriod(
                'P2', 'tp'
            ),
            TariffPeriod(
                'P3', 'tp'
            )
        )

    @staticmethod
    def are_powers_normalized(powers):
        # 3.1A doesn't need to have normalized powers
        return True

    def apply_31A_LB_cof(self, balance, start_date, end_date):
        consumptions = balance.copy()
        period_hours = self.hours_by_period
        holidays_list = get_holidays(start_date.year)
        (workdays, holidays) = get_num_of_workdays_holidays(
            start_date, end_date, holidays_list
        )

        cofs = {}
        for period in period_hours:
            if period > 'P3':
                cofs[period] = period_hours.get(period, 0) * holidays
            else:
                cofs[period] = period_hours.get(period, 0) * workdays
        for period, consumption in balance.items():
            consumptions[period] = round(
                consumption * (1 + self.losses), 2
            ) + round(0.01 * cofs[period] * self.kva, 2)

        return consumptions

    def apply_curve_losses(self, measures):
        for idx, measure in enumerate(measures):
            values = measure._asdict()
            consumption = round(measure.measure * (1 + self.losses), 2) + round(0.01 * self.kva, 2)
            values['measure'] = consumption
            measures[idx] = measure._replace(**values)
        return measures

    def evaluate_powers(self, powers):
        super(T31A, self).evaluate_powers(powers)

        if not are_powers_ascending(powers):
            raise NotAscendingPowers()

        return True

    def evaluate_powers_all_checks(self, powers):
        errors = super(T31A, self).evaluate_powers_all_checks(powers)
        if not are_powers_ascending(powers):
            errors.append(NotAscendingPowers())

        return errors


class T31A_one_period(T31A):
    """
    A 3.1A with one unique period
    """
    def __init__(self):
        super(T31A_one_period, self).__init__()
        self.periods = (
            TariffPeriod('P1', 'te'),
            TariffPeriod('P1', 'tp')
        )


class T31ANoFestivos(T31A):
    def __init__(self, kva=None):
        super(T31ANoFestivos, self).__init__(kva=kva)
        self.hours_by_period = {
            'P1': 6,
            'P2': 10,
            'P3': 8,
        }
        self.periods = (
            TariffPeriod(
                'P1', 'te',
                winter_hours=[(17, 23)],
                summer_hours=[(10, 16)]
            ),
            TariffPeriod(
                'P2', 'te',
                winter_hours=[(8, 17), (23, 24)],
                summer_hours=[(8, 10), (16, 24)]
            ),
            TariffPeriod(
                'P3', 'te',
                winter_hours=[(0, 8)],
                summer_hours=[(0, 8)]
            ),
            TariffPeriod(
                'P1', 'tp'
            ),
            TariffPeriod(
                'P2', 'tp'
            ),
            TariffPeriod(
                'P3', 'tp'
            )
        )


class T61A(TariffPreTD):
    """
    6.1A Tariff
    """
    def __init__(self):
        super(T61A, self).__init__()
        self.code = '6.1A'
        self.cof = 'C'
        self.min_power = 450
        self.max_power = 1000000
        self.type = 'AT'
        self.periods = (
            #
            # TODO: Implement correct energy periods
            #
            TariffPeriod('P1', 'te'),
            TariffPeriod(
                'P1', 'tp'
            ),
            TariffPeriod(
                'P2', 'tp'
            ),
            TariffPeriod(
                'P3', 'tp'
            ),
            TariffPeriod(
                'P4', 'tp'
            ),
            TariffPeriod(
                'P5', 'tp'
            ),
            TariffPeriod(
                'P6', 'tp'
            ),
        )

    @staticmethod
    def are_powers_normalized(powers):
        # 6.1A doesn't need to have normalized powers
        return True

    def evaluate_powers(self, powers):
        super(T61A, self).evaluate_powers(powers)

        if not are_powers_ascending(powers):
            raise NotAscendingPowers()

        return True

    def evaluate_powers_all_checks(self, powers):
        errors = super(T61A, self).evaluate_powers_all_checks(powers)
        if not are_powers_ascending(powers):
            errors.append(NotAscendingPowers())

        return errors


class T61B(T61A):
    """
    6.1B Tariff
    """
    def __init__(self):
        super(T61B, self).__init__()
        self.code = '6.1B'


class T62(T61A):
    """
    6.2 Tariff
    """
    def __init__(self):
        super(T62, self).__init__()
        self.code = '6.2'


class T63(T61A):
    """
    6.3 Tariff
    """
    def __init__(self):
        super(T63, self).__init__()
        self.code = '6.3'


class T64(T61A):
    """
    6.4 Tariff
    """
    def __init__(self):
        super(T64, self).__init__()
        self.code = '6.4'


class TRE(TariffPreTD):
    def __init__(self):
        super(TRE, self).__init__()
        self.code = 'RE'
        self.cof = 'A'

        self.periods = (
            TariffPeriod('P0', 'te'),
            TariffPeriod('P0', 'tp')
        )


# Tariffs from BOE-A-2020-1066 (https://www.boe.es/eli/es/cir/2020/01/15/3)
class T20TD(Tariff):
    """Classe que implementa la Tarifa 2.0TD."""
    def __init__(self, **kwargs):
        super(T20TD, self).__init__(**kwargs)
        self.code = '2.0TD'
        self.cof = '2.0TD'
        self.min_power = 0
        self.max_power = 15
        self.require_summer_winter_hours = False

        self.type = 'BT'

        # set subsystem and periods by zone
        self.geom_zone = kwargs.pop('geom_zone', '1')
        self.periods_by_zone_and_day = PERIODS_3x_BY_ELECTRIC_ZONE_CIR03_2020

        self.periods_validation = False

        self.periods = (
            TariffPeriod('P1', 'te',
                         tariff_has_holiday_periods=True,
                         periods_by_zone_and_day=PERIODS_3x_BY_ELECTRIC_ZONE_CIR03_2020,
                         daytype=True,
                         geom_zone=self.geom_zone
                         ),
            TariffPeriod('P2', 'te',
                         tariff_has_holiday_periods=True,
                         periods_by_zone_and_day=PERIODS_3x_BY_ELECTRIC_ZONE_CIR03_2020,
                         daytype=True,
                         geom_zone=self.geom_zone
                         ),
            TariffPeriod('P3', 'te',
                         tariff_has_holiday_periods=True,
                         periods_by_zone_and_day=PERIODS_3x_BY_ELECTRIC_ZONE_CIR03_2020,
                         daytype=True,
                         geom_zone=self.geom_zone
                         ),
            TariffPeriod('P1', 'tp',
                         tariff_has_holiday_periods=True,
                         periods_by_zone_and_day=PERIODS_2x_BY_ELECTRIC_ZONE_CIR03_2020,
                         daytype=True,
                         geom_zone=self.geom_zone
                         ),
            TariffPeriod('P2', 'tp',
                         tariff_has_holiday_periods=True,
                         periods_by_zone_and_day=PERIODS_2x_BY_ELECTRIC_ZONE_CIR03_2020,
                         daytype=True,
                         geom_zone=self.geom_zone
                         )
        )


class T30TD(Tariff):
    """Classe que implementa la Tarifa 3.0TD."""
    def __init__(self, **kwargs):
        super(T30TD, self).__init__(**kwargs)
        self.code = '3.0TD'
        self.cof = '3.0TD'
        self.min_power = 15
        self.max_power = 100000
        self.require_summer_winter_hours = False

        self.type = 'BT'
        self.geom_zone = kwargs.pop('geom_zone', '1')

        self.periods_validation = False
        self.periods = (
            TariffPeriod('P1', 'te',
                          tariff_has_holiday_periods=True,
                          periods_by_zone_and_day=PERIODS_6x_BY_ELECTRIC_ZONE_CIR03_2020,
                          daytype=True,
                          geom_zone=self.geom_zone),
            TariffPeriod('P2', 'te',
                          tariff_has_holiday_periods=True,
                          periods_by_zone_and_day=PERIODS_6x_BY_ELECTRIC_ZONE_CIR03_2020,
                          daytype=True,
                          geom_zone=self.geom_zone),
            TariffPeriod('P3', 'te',
                          tariff_has_holiday_periods=True,
                          periods_by_zone_and_day=PERIODS_6x_BY_ELECTRIC_ZONE_CIR03_2020,
                          daytype=True,
                          geom_zone=self.geom_zone),
            TariffPeriod('P4', 'te',
                          tariff_has_holiday_periods=True,
                          periods_by_zone_and_day=PERIODS_6x_BY_ELECTRIC_ZONE_CIR03_2020,
                          daytype=True,
                          geom_zone=self.geom_zone),
            TariffPeriod('P5', 'te',
                          tariff_has_holiday_periods=True,
                          periods_by_zone_and_day=PERIODS_6x_BY_ELECTRIC_ZONE_CIR03_2020,
                          daytype=True,
                          geom_zone=self.geom_zone),
            TariffPeriod('P6', 'te',
                          tariff_has_holiday_periods=True,
                          periods_by_zone_and_day=PERIODS_6x_BY_ELECTRIC_ZONE_CIR03_2020,
                          daytype=True,
                          geom_zone=self.geom_zone),
            TariffPeriod('P1', 'tp',
                          tariff_has_holiday_periods=True,
                          periods_by_zone_and_day=PERIODS_6x_BY_ELECTRIC_ZONE_CIR03_2020,
                          daytype=True,
                          geom_zone=self.geom_zone),
            TariffPeriod('P2', 'tp',
                          tariff_has_holiday_periods=True,
                          periods_by_zone_and_day=PERIODS_6x_BY_ELECTRIC_ZONE_CIR03_2020,
                          daytype=True,
                          geom_zone=self.geom_zone),
            TariffPeriod('P3', 'tp',
                          tariff_has_holiday_periods=True,
                          periods_by_zone_and_day=PERIODS_6x_BY_ELECTRIC_ZONE_CIR03_2020,
                          daytype=True,
                          geom_zone=self.geom_zone),
            TariffPeriod('P4', 'tp',
                          tariff_has_holiday_periods=True,
                          periods_by_zone_and_day=PERIODS_6x_BY_ELECTRIC_ZONE_CIR03_2020,
                          daytype=True,
                          geom_zone=self.geom_zone),
            TariffPeriod('P5', 'tp',
                          tariff_has_holiday_periods=True,
                          periods_by_zone_and_day=PERIODS_6x_BY_ELECTRIC_ZONE_CIR03_2020,
                          daytype=True,
                          geom_zone=self.geom_zone),
            TariffPeriod('P6', 'tp',
                          tariff_has_holiday_periods=True,
                          periods_by_zone_and_day=PERIODS_6x_BY_ELECTRIC_ZONE_CIR03_2020,
                          daytype=True,
                          geom_zone=self.geom_zone)
        )


class T61TD(T30TD):
    """Classe que implementa la Tarifa 6.1TD."""
    def __init__(self, **kwargs):
        super(T61TD, self).__init__(**kwargs)
        self.code = '6.1TD'
        self.cof = '6.1TD'
        self.min_power = 0
        self.max_power = 100000
        self.require_summer_winter_hours = False

        self.type = 'AT'


class T62TD(T61TD):
    """Classe que implementa la Tarifa 6.2TD."""
    def __init__(self, **kwargs):
        super(T62TD, self).__init__(**kwargs)
        self.code = '6.2TD'


class T63TD(T61TD):
    """Classe que implementa la Tarifa 6.3TD."""
    def __init__(self, **kwargs):
        super(T63TD, self).__init__(**kwargs)
        self.code = '6.3TD'


class T64TD(T61TD):
    """Classe que implementa la Tarifa 6.4TD."""
    def __init__(self, **kwargs):
        super(T64TD, self).__init__(**kwargs)
        self.code = '6.4TD'


# Vehículo Eléctrico
class T30TDVE(T30TD):
    """Classe que implementa la Tarifa 3.0TDVE."""
    def __init__(self, **kwargs):
        super(T30TDVE, self).__init__(**kwargs)
        self.code = '3.0TDVE'


class T61TDVE(T61TD):
    """Classe que implementa la Tarifa 6.1TDVE."""
    def __init__(self, **kwargs):
        super(T61TDVE, self).__init__(**kwargs)
        self.code = '6.1TDVE'


class NotPositivePower(Exception):
    def __init__(self):
        super(NotPositivePower, self).__init__(
            'Power should allways be higher than 0'
        )


class NotNormalizedPower(Exception):
    def __init__(self):
        super(NotNormalizedPower, self).__init__(
            'One or more of the powers doen\'t have a normalized value'
        )


class IncorrectPowerNumber(Exception):
    def __init__(self, power_number, expected_number):
        super(IncorrectPowerNumber, self).__init__(
            'Expected {0} power(s) and got {1}'.format(
                expected_number, power_number
            )
        )
        self.power_number = power_number
        self.expected_number = expected_number


class IncorrectMaxPower(Exception):
    def __init__(self, power, min_power, max_power):
        super(IncorrectMaxPower, self).__init__(
            'Power {0} is not between {1} and {2}'.format(
                power, min_power, max_power
            )
        )
        self.power = power
        self.min_power = min_power
        self.max_power = max_power


class IncorrectMinPower(Exception):
    def __init__(self, power, min_power, max_power):
        super(IncorrectMinPower, self).__init__(
            'Power {0} is not between {1} and {2}'.format(
                power, min_power, max_power
            )
        )
        self.power = power
        self.min_power = min_power
        self.max_power = max_power


class NotAscendingPowers(Exception):
    def __init__(self):
        super(NotAscendingPowers, self).__init__(
            'For this tariff powers should go in an ascending order (Pn+1>=Pn)'
        )


def get_tariff_by_code(code):
    """Get tariff class by code

    :param code: Tariff code
    :return: Tariff
    """
    available = {
        '2.0A': T20A,
        '2.0DHA': T20DHA,
        '2.0DHS': T20DHS,
        '2.1A': T21A,
        '2.1DHA': T21DHA,
        '2.1DHS': T21DHS,
        '3.0A': T30A,
        '3.0A C2': T30ANoFestivos,
        '3.1A': T31A,
        '3.1A LB': T31A,
        '3.1A C2': T31ANoFestivos,
        '6.1A': T61A,
        '6.1B': T61B,
        '6.2': T62,
        '6.3': T63,
        '6.4': T64,
        'RE': TRE,
        # New access tariffs 2021
        '2.0TD': T20TD,
        '3.0TD': T30TD,
        '6.1TD': T61TD,
        '6.2TD': T62TD,
        '6.3TD': T63TD,
        '6.4TD': T64TD,
        '3.0TDVE': T30TDVE,
        '6.1TDVE': T61TDVE
    }
    return available.get(code, None)
