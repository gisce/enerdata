class Tariff(object):
    """Energy DSO Tariff.
    """
    def __init__(self, code, **kwargs):
        self.periods = set()

    def get_number_of_periods(self):
        return len([p for p in self.periods if p.type == 'te'])


class TariffPeriod(object):
    """Tariff period.
    """
    def __init__(self, code, ptype):
        assert ptype in ('te', 'tp')
        self.code = code
        self.type = ptype


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

