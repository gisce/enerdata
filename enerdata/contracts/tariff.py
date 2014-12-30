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
    def __init__(self, code):
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
        self.code = '2.0A'
        self.periods = (
            TariffPeriod('P1', 'te'),
            TariffPeriod('P1', 'tp')
        )
        self.ocsum = 'XXX'
        self.min_power = 0
        self.max_power = 10
        self.type = 'BT'

class T20DHA(Tariff):
    def __init__(self):
        self.code = '2.0DHA'
        self.periods = (
            TariffPeriod('P1', 'te', winter_hours=[(12, 22)], summer_hours=[(13, 23)]),
            TariffPeriod('P2', 'te', winter_hours=[(0, 12), (22, 24)], summer_hours=[(0, 13), (23, 24)])
        )


