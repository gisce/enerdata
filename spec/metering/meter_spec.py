from datetime import date

from expects.testing import failure
from enerdata.metering.meter import *
from enerdata.metering.measure import *


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
with description('Adding a measure'):
    with before.all:
        self.meter = Meter('123456789')
    with context('Energy'):
        with it('only EnergyMeasures accepted'):
            with failure:
                m = PowerMeasure(date(2014, 1, 1), TariffPeriod('P1', 'tp'), 10)
                self.meter.add_energy_measure(m)
        with it('should mantain energy measures sorted'):
            for _x in range(1, 1000):
                d = generate_random_date()
                m = EnergyMeasure(d, TariffPeriod('P1', 'te'), 0)
                self.meter.add_energy_measure(m)
            before = EnergyMeasure(date(1999, 1, 1), TariffPeriod('P1', 'te'), 0)
            for x in self.meter.energy_measures:
                assert x >= before
                before = x

    with context('Power'):
        with it('only PowerMeasures accepted'):
            with failure:
                m = EnergyMeasure(date(2014, 1, 1), TariffPeriod('P1', 'te'), 10)
                self.meter.add_power_measure(m)
        with it('should mantain power measures sorted'):
            for _x in range(1, 1000):
                d = generate_random_date()
                m = PowerMeasure(d, TariffPeriod('P1', 'tp'), 0)
                self.meter.add_power_measure(m)
            before = EnergyMeasure(date(1999, 1, 1), TariffPeriod('P1', 'te'), 0)
            for x in self.meter.power_measures:
                assert x >= before
                before = x
