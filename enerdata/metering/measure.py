from enerdata.contracts import TariffPeriod


class Measure(object):
    def __init__(self, date, period, measure):
        self.date = date,
        assert isinstance(period, TariffPeriod)
        self.period = period
        self.measure = measure


class EnergyMeasure(Measure):
    def __init__(self, date, period, measure, mtype='A'):
        assert period.type == 'te'
        super(EnergyMeasure, self).__init__(date, period, measure)
        self.type = mtype


class PowerMeasure(Measure):
    def __init__(self, date, period, measure):
        assert period.type == 'tp'
        super(PowerMeasure, self).__init__(date, period, measure)