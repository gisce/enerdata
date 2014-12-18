from datetime import date

from expects.testing import failure
from enerdata.metering.meter import *
from enerdata.metering.measure import *


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
    with context('Power'):
        with it('only PowerMeasures accepted'):
            with failure:
                m = EnergyMeasure(date(2014, 1, 1), TariffPeriod('P1', 'te'), 10)
                self.meter.add_power_measure(m)
