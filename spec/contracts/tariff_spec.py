from expects.testing import failure

from enerdata.contracts.tariff import *

with description('Create a period'):
    with it('accepts "te"'):
        TariffPeriod('P1', 'te')
    with it('accepts "tp"'):
        TariffPeriod('P1', 'tp')
    with it('fails when is not "te" nor "tp"'):
        with failure:
            TariffPeriod('P1', 'foo')


with context('A tariff'):
    with before.all:
        self.tariff = Tariff('T1')
    with it('periods should be a set type'):
        assert isinstance(self.tariff.periods, set)
    with it('should return the number of periods of te'):
        self.tariff.periods = (TariffPeriod('1', 'te'), TariffPeriod('2', 'te'))
        assert self.tariff.get_number_of_periods() == 2