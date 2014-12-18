from datetime import date

from expects.testing import failure
from enerdata.metering.measure import *


with description('Creating a measure'):
    with it('should fail if not is a period object'):
        with failure:
            m = Measure(date(2014, 1, 1), 'P1', 0)
    with context('If is energy measure'):
        with it('only accepts periods of te'):
            with failure:
                m = EnergyMeasure(date(2014, 1, 1), TariffPeriod('P1', 'tp'), 0)
    with context('If is power measure'):
        with it('only accepts periods of tp'):
            with failure:
                m = PowerMeasure(date(2014, 1, 1), TariffPeriod('P1', 'te'), 0)