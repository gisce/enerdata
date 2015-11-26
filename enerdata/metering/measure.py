from enerdata.contracts import TariffPeriod


class Measure(object):

    __slots__ = ('date', 'period', 'measure')

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

    __slots__ = ('type', 'consumption')

    def __init__(self, date, period, measure, mtype='A', consumption=0):
        assert period.type == 'te'
        super(EnergyMeasure, self).__init__(date, period, measure)
        self.type = mtype
        self.consumption = consumption

    def __repr__(self):
        return '<EnergyMeasure: [%s] %s - %s: %s>' % (
            self.date,
            self.period.code,
            self.period.type,
            self.measure
        )

    @classmethod
    def intervals(cls, measures):
        """Get the intervals of dates between measures.

        :param measures: A list of EnergyMeasures
        :return: A sorted list of `date` objects
        """

        dates = []
        for measure in sorted(measures):
            if measure.date not in dates:
                dates.append(measure.date)
        return dates


class PowerMeasure(Measure):
    def __init__(self, date, period, measure):
        assert period.type == 'tp'
        super(PowerMeasure, self).__init__(date, period, measure)