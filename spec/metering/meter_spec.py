from expects.testing import failure
from enerdata.metering.meter import *
from enerdata.metering.measure import *

from datetime import date


def generate_random_date():
    from random import randint
    from calendar import monthrange
    year = randint(2000, 2014)
    month = randint(1, 12)
    last_day = monthrange(year, month)[1]
    day = randint(1, last_day)
    return date(year, month, day)


with description('Creating a meter'):
    with before.all:
        self.meter = Meter('123456789')
    with it('should have an empty list of energy measures'):
        assert len(self.meter.energy_measures) == 0
    with it('should have an empty list of power measures'):
        assert len(self.meter.power_measures) == 0
    with context('If no date is passed'):
        with it('should be today'):
            assert self.meter.start_date == date.today()
    with context('If date is passed'):
        with it('must be the same'):
            m = Meter('XXX', date(1983, 5, 28))
            assert m.start_date == date(1983, 5, 28)

with description('Adding a measure'):
    with before.each:
        self.meter = Meter('123456789', start_date=date(2014, 1, 1))
    with it('only accepts EnergyMeasure or PowerMeasure'):
        with failure:
            m = Measure(date(2014, 1, 1), TariffPeriod('P1', 'te'), 0)
            self.meter.add_measure(m)
    with it('don\'t accepts measures which date is before start date'):
        self.meter.start_date = date(2014, 1, 1)
        with failure:
            m = EnergyMeasure(date(2013, 1, 1), TariffPeriod('P1', 'te'), 0)
            self.meter.add_measure(m)
    with it('don\'t accepts mesasures which date is greater than end date'):
        self.meter.end_date = date(2014, 2, 1)
        m = EnergyMeasure(date(2014, 2, 2), TariffPeriod('P1', 'te'), 0)
        with failure:
            self.meter.add_measure(m)

    with context('Energy'):
        with it('should be added in energy measures list'):
            em = EnergyMeasure(date(2014, 1, 1), TariffPeriod('P1', 'te'), 0)
            self.meter.add_measure(em)
            assert len(self.meter.energy_measures) == 1
            assert self.meter.energy_measures[0] == em
        with it('should mantain energy measures sorted'):
            self.meter.start_date = date(2000, 1, 1)
            for _x in range(1, 1000):
                d = generate_random_date()
                m = EnergyMeasure(d, TariffPeriod('P1', 'te'), 0)
                self.meter.add_measure(m)
            before = EnergyMeasure(date(1999, 1, 1), TariffPeriod('P1', 'te'), 0)
            for x in self.meter.energy_measures:
                assert x >= before
                before = x
    with context('Power'):
        with it('should be added in energy measures list'):
            pm = PowerMeasure(date(2014, 1, 1), TariffPeriod('P1', 'tp'), 0)
            self.meter.add_measure(pm)
            assert len(self.meter.power_measures) == 1
            assert self.meter.power_measures[0] == pm
        with it('should mantain power measures sorted'):
            self.meter.start_date = date(2000, 1, 1)
            for _x in range(1, 1000):
                d = generate_random_date()
                m = PowerMeasure(d, TariffPeriod('P1', 'tp'), 0)
                self.meter.add_measure(m)
            before = EnergyMeasure(date(1999, 1, 1), TariffPeriod('P1', 'te'), 0)
            for x in self.meter.power_measures:
                assert x >= before
                before = x
