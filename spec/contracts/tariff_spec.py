from expects.testing import failure
from expects import *
from enerdata.contracts.tariff import *
from datetime import datetime

with description('Create a period'):
    with it('accepts "te"'):
        TariffPeriod('P1', 'te')
    with it('accepts "tp"'):
        TariffPeriod('P1', 'tp')
    with it('fails when is not "te" nor "tp"'):
        with failure:
            TariffPeriod('P1', 'foo')
    with it('should raise an exception if range of hours is invalid'):
        expect(lambda: TariffPeriod('P1', 'te', winter_hours=[
            (0, 12), (11, 23)
        ])).to(raise_error(ValueError, 'Invalid winter hours'))
        expect(lambda: TariffPeriod('P1', 'te', summer_hours=[
            (0, 12), (11, 23)
        ])).to(raise_error(ValueError, 'Invalid summer hours'))

with description('A period'):
    with it('should have a range of hours 24 for winter by default'):
        p1 = TariffPeriod('P1', 'te')
        assert p1.winter_hours == [(0, 24)]
    with it('should be possible to set the range of winter hours in creation'):
        p1 = TariffPeriod('P1', 'te', winter_hours=[(0, 12)])
        assert p1.winter_hours == [(0, 12)]
    with it('should have a range of hours 24 for summer by default'):
        p1 = TariffPeriod('P1', 'te')
        assert p1.summer_hours == [(0, 24)]
    with it('should be possible to set the range of sumer hours in creation'):
        p1 = TariffPeriod('P1', 'te', summer_hours=[(0, 12)])
        assert p1.summer_hours == [(0, 12)]
    with it('has to validate range hours is correct'):
        assert check_range_hours([(0, 12)]) is True
        assert check_range_hours([(0, 12), (12, 24)]) is True
        assert check_range_hours([(-1, 0)]) is False
        assert check_range_hours([(0, 25)]) is False
        assert check_range_hours([(0, 0)]) is False
        assert check_range_hours([(4, 1)]) is False
        assert check_range_hours([(0, 1), (0, 2)]) is False
        assert check_range_hours([(0, 12), (12, 24)]) is True
    with it('should know the total of hours in summer'):
        p1 = TariffPeriod('P1', 'te', summer_hours=[(0, 12), (22, 24)])
        assert p1.total_summer_hours == 14
    with it('should know the total of hours in winter'):
        p1 = TariffPeriod('P1', 'te', winter_hours=[(12, 22)])
        assert p1.total_winter_hours == 10



with context('A tariff'):
    with before.all:
        self.tariff = Tariff('T1')
    with it('periods should be a tuple type'):
        assert isinstance(self.tariff.periods, tuple)
    with it('should return the number of periods of te'):
        self.tariff.periods = (
            TariffPeriod('1', 'te', winter_hours=[(12, 22)], summer_hours=[(13, 23)]),
            TariffPeriod('2', 'te', winter_hours=[(0, 12), (22, 24)], summer_hours=[(0, 13), (23, 24)])
        )
        assert self.tariff.get_number_of_periods() == 2
    with it('should return the periods of energy'):
        assert len(self.tariff.energy_periods) == 2
        assert self.tariff.energy_periods.keys() == ['1', '2']
    with it('should return the periods of power'):
        assert len(self.tariff.power_periods) == 0
        self.tariff.periods += (TariffPeriod('1', 'tp'),)
        assert len(self.tariff.power_periods) == 1
        assert self.tariff.power_periods.keys() == ['1']
    with it('should have 24h of range ours in its energy periods'):
        def set_periods():
            self.tariff.periods = (
                TariffPeriod('1', 'te', summer_hours=[(12, 22)]),
                TariffPeriod('2', 'te', summer_hours=[(0, 12), (22, 23)])
            )
        expect(set_periods).to(raise_error(ValueError))

    with it('should check range of hours'):
        def set_periods():
            self.tariff.periods = (
                TariffPeriod('1', 'te', summer_hours=[(13, 23)]),
                TariffPeriod('2', 'te', summer_hours=[(0, 12), (22, 24)])
            )
        expect(set_periods).to(raise_error(ValueError))

    with it('should check range and hours if a holiday period is defined'):
        def set_periods():
            self.tariff.periods = (
                TariffPeriod('P1', 'te', winter_hours=[(18, 22)], summer_hours=[(11, 15)]),
                TariffPeriod('P2', 'te', winter_hours=[(8, 18), (22, 24)], summer_hours=[(8, 11), (15, 24)]),
                TariffPeriod('P3', 'te', winter_hours=[(0, 8)], summer_hours=[(0, 8)]),
                TariffPeriod('P4', 'te', holiday=True, winter_hours=[(18, 22)], summer_hours=[(11, 15)]),
                TariffPeriod('P5', 'te', holiday=True, winter_hours=[(8, 18), (22, 24)], summer_hours=[(8, 11), (15, 24)]),
                TariffPeriod('P6', 'te', holiday=True, winter_hours=[(0, 8)], summer_hours=[(1, 8)])
            )
        expect(set_periods).to(raise_error(ValueError, 'The sum of hours in summer (in holidays) must be 24h: [(1, 8), (8, 11), (11, 15), (15, 24)]'))

    with it('should find the period by datetime'):
        self.tariff.periods = (
            TariffPeriod('P1', 'te', winter_hours=[(18, 22)], summer_hours=[(11, 15)]),
            TariffPeriod('P2', 'te', winter_hours=[(8, 18), (22, 24)], summer_hours=[(8, 11), (15, 24)]),
            TariffPeriod('P3', 'te', winter_hours=[(0, 8)], summer_hours=[(0, 8)]),
            TariffPeriod('P4', 'te', holiday=True, winter_hours=[(18, 22)], summer_hours=[(11, 15)]),
            TariffPeriod('P5', 'te', holiday=True, winter_hours=[(8, 18), (22, 24)], summer_hours=[(8, 11), (15, 24)]),
            TariffPeriod('P6', 'te', holiday=True, winter_hours=[(0, 8)], summer_hours=[(0, 8)])
        )
        dt = datetime(2014, 12, 27, 18, 0, 0)
        period = self.tariff.get_period_by_date(dt, 'winter')
        assert period.code == 'P4'
        dt = datetime(2014, 12, 27, 17, 0, 0)
        period = self.tariff.get_period_by_date(dt, 'winter')
        assert period.code == 'P5'
        dt = datetime(2014, 12, 27, 1, 0, 0)
        period = self.tariff.get_period_by_date(dt, 'winter')
        assert period.code == 'P6'

with context('3.0A tariff'):
    with before.all:
        self.tariff = T30A()
        self.periods = self.tariff.energy_periods
    with it("should return 6 energy periods"):
        assert len(self.periods) == 6
    with it("should contain P1 to P6 periods"):
        assert 'P1' in self.periods.keys()
        assert 'P2' in self.periods.keys()
        assert 'P3' in self.periods.keys()
        assert 'P4' in self.periods.keys()
        assert 'P5' in self.periods.keys()
        assert 'P6' in self.periods.keys()
