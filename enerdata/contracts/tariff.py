import calendar

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


class Tariff(object):
    """Energy DSO Tariff.
    """
    def __init__(self, code=None):
        self.code = code
        self._periods = tuple()

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

    def get_period_by_date(self, date_time):
        station = get_station(date_time)
        date = date_time.date()
        holidays = get_holidays(date.year)
        if (calendar.weekday(date.year, date.month, date.day) in (5, 6)
                or date in holidays):
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
        self.periods = (
            TariffPeriod('P1', 'te'),
            TariffPeriod('P1', 'tp')
        )
        self.min_power = 0
        self.max_power = 10
        self.type = 'BT'


class T20DHA(T20A):
    def __init__(self):
        super(T20DHA, self).__init__()
        self.code = '2.0DHA'
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
        self.min_power = 10
        self.max_power = 15


class T21DHA(T20DHA):
    def __init__(self):
        super(T21DHA, self).__init__()
        self.code = '2.1DHA'
        self.min_power = 10
        self.max_power = 15


class T21DHS(T20DHS):
    def __init__(self):
        super(T21DHS, self).__init__()
        self.code = '2.1DHS'
        self.min_power = 10
        self.max_power = 15


class T30A(Tariff):
    def __init__(self):
        super(T30A, self).__init__()
        self.code = '3.0A'
        self.min_power = 15
        self.max_power = 99999
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
        '3.0A': T30A
    }
    return available.get(code, None)