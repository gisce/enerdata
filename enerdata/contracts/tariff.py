import calendar

from enerdata.contracts.normalized_power import NormalizedPower
from enerdata.datetime.station import get_station
from enerdata.datetime.holidays import get_holidays


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


class Tariff(object):
    """Energy DSO Tariff.
    """
    def __init__(self, code=None):
        self.code = code
        self._periods = tuple()
        self.cof = None

    @property
    def periods(self):
        return self._periods

    @periods.setter
    def periods(self, value):
        self._periods = value
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
        station = get_station(date_time)
        date = date_time.date()
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

    @staticmethod
    def are_powers_normalized(powers):
        np = NormalizedPower()
        for power in powers:
            if not np.is_normalized(int(power * 1000)):
                return False

        return True

    def evaluate_powers(self, powers):
        if min(powers) <= 0:
            raise NotPositivePower()
        if not len(self.power_periods) == len(powers):
            raise IncorrectPowerNumber(len(powers), len(self.power_periods))
        if not self.is_maximum_power_correct(max(powers)):
            raise IncorrectMaxPower(max(powers), self.min_power, self.max_power)
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
        self.holiday = kwargs.pop('holiday', False)

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


class T20A(Tariff):
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


class T30A(Tariff):
    def __init__(self):
        super(T30A, self).__init__()
        self.code = '3.0A'
        self.cof = 'C'
        self.min_power = 15
        self.max_power = 1000000
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


class T31A(T30A):
    """
    3.1A Tariff
    """
    def __init__(self):
        super(T31A, self).__init__()
        self.code = '3.1A'
        self.cof = 'C'
        self.min_power = 1
        self.max_power = 450
        self.type = 'AT'
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

    def evaluate_powers(self, powers):
        super(T31A, self).evaluate_powers(powers)

        if not are_powers_ascending(powers):
            raise NotAscendingPowers()

        return True


class T61A(Tariff):
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


class T61B(T61A):
    """
    6.1B Tariff
    """
    def __init__(self):
        super(T61B, self).__init__()
        self.code = '6.1B'


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
        '3.1A': T31A,
        '3.1A LB': T31A,
        '6.1A': T61A,
        '6.1B': T61B,
    }
    return available.get(code, None)
