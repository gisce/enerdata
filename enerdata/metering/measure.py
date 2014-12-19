from enerdata.contracts import TariffPeriod


class Measure(object):
    def __init__(self, date, period, measure):
        self.date = date
        assert isinstance(period, TariffPeriod)
        self.period = period
        self.measure = measure

    def __lt__(self, other):
        return self.date < other.date

    def __le__(self, other):
        return self.date <= other.date

    def __gt__(self, other):
        return self.date > other.date

    def __ge__(self, other):
        return self.date >= other.date


class EnergyMeasure(Measure):
    def __init__(self, date, period, measure, mtype='A'):
        assert period.type == 'te'
        super(EnergyMeasure, self).__init__(date, period, measure)
        self.type = mtype
        self.consumption = 0

    def __repr__(self):
        return '<EnergyMeasure: [%s] %s - %s: %s>' % (
            self.date,
            self.period.code,
            self.period.type,
            self.measure
        )


class PowerMeasure(Measure):
    def __init__(self, date, period, measure):
        assert period.type == 'tp'
        super(PowerMeasure, self).__init__(date, period, measure)