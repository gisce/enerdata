# -*- coding: utf-8 -*-
from datetime import date
from expects import *
from expects.testing import failure
from enerdata.metering.measure import *
from mamba import description, it, context, before


with description('Creating a measure'):
    with it('should fail if not is a period object'):
        with failure:
            m = Measure(date(2014, 1, 1), 'P1', 0)
    with context('If is energy measure'):
        with it('only accepts periods of te'):
            with failure:
                m = EnergyMeasure(date(2014, 1, 1), TariffPeriod('P1', 'tp'), 0)
        with it('should have 0 consumption'):
            m = EnergyMeasure(date(2014, 1, 1), TariffPeriod('P1', 'te'), 10)
            assert m.consumption == 0
    with context('If is power measure'):
        with it('only accepts periods of tp'):
            with failure:
                m = PowerMeasure(date(2014, 1, 1), TariffPeriod('P1', 'te'), 0)

with description('Comparing measures by date'):
    with before.all:
        self.m1 = Measure(date(2014, 1, 1), TariffPeriod('P1', 'te'), 0)
        self.m2 = Measure(date(2014, 1, 2), TariffPeriod('P1', 'te'), 0)
    with it('can compare if is greater than another'):
        assert self.m2 > self.m1
    with it('can compare if is lower than anoter'):
        assert self.m1 < self.m2


with description('Get intervals of measures'):
    with it('must return the interval of different measures'):
        measures = [
            EnergyMeasure(
                date(2014, 9, 30),
                TariffPeriod('P1', 'te'), 307, consumption=145
            ),
            EnergyMeasure(
                date(2014, 9, 30),
                TariffPeriod('P2', 'te'), 108, consumption=10
            ),
            EnergyMeasure(
                date(2014, 10, 15),
                TariffPeriod('P1', 'te'), 410, consumption=103
            ),
            EnergyMeasure(
                date(2014, 10, 15),
                TariffPeriod('P2', 'te'), 130, consumption=22
            ),
            EnergyMeasure(
                date(2014, 10, 31),
                TariffPeriod('P1', 'te'), 540, consumption=130
            ),
            EnergyMeasure(
                date(2014, 10, 31),
                TariffPeriod('P2', 'te'), 150, consumption=20
            )
        ]
        expect(EnergyMeasure.intervals(measures)).to(contain_exactly(
            date(2014, 9, 30),  date(2014, 10, 15), date(2014, 10, 31)
        ))