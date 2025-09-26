# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from enerdata.contracts.tariff import *
from expects.testing import failure
from expects import *
from enerdata.datetime.timezone import TIMEZONE
from mamba import before, context, description, it


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
        self.tariff = TariffPreTD('T1')
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
        assert list(self.tariff.energy_periods.keys()) == ['1', '2']
    with it('should return the periods of power'):
        assert len(self.tariff.power_periods) == 0
        self.tariff.periods += (TariffPeriod('1', 'tp'),)
        assert len(self.tariff.power_periods) == 1
        assert list(self.tariff.power_periods.keys()) == ['1']
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
        dt = TIMEZONE.localize(datetime(2015, 12, 24, 19, 0, 0))
        period = self.tariff.get_period_by_date(dt)
        assert period.code == 'P1'
        dt = TIMEZONE.localize(datetime(2015, 12, 25, 19, 0, 0))
        period = self.tariff.get_period_by_date(dt)
        assert period.code == 'P4'
        dt = TIMEZONE.localize(datetime(2015, 12, 27, 19, 0, 0))
        period = self.tariff.get_period_by_date(dt)
        assert period.code == 'P4'
        dt = TIMEZONE.localize(datetime(2015, 12, 27, 19, 0, 0))
        period = self.tariff.get_period_by_date(dt)
        assert period.code == 'P4'
        dt = TIMEZONE.localize(datetime(2015, 12, 27, 17, 0, 0))
        period = self.tariff.get_period_by_date(dt)
        assert period.code == 'P5'
        dt = TIMEZONE.localize(datetime(2015, 12, 27, 1, 0, 0))
        period = self.tariff.get_period_by_date(dt)
        assert period.code == 'P6'
    with it('should allow to check if a set of powers is correct'):
        tari_T20A = T20A()
        expect(lambda: tari_T20A.evaluate_powers([-10])).to(
            raise_error(NotPositivePower))
        expect(lambda: tari_T20A.evaluate_powers([0])).to(
            raise_error(NotPositivePower))
        expect(lambda: tari_T20A.evaluate_powers([5.55])).to(
            raise_error(NotNormalizedPower))
        assert tari_T20A.evaluate_powers([5.5])
        expect(lambda: tari_T20A.evaluate_powers([5, 7])).to(
            raise_error(IncorrectPowerNumber, 'Expected 1 power(s) and got 2'))
        expect(lambda: tari_T20A.evaluate_powers([100])).to(
            raise_error(IncorrectMaxPower))

        tari_T30A = T30A()
        expect(lambda: tari_T30A.evaluate_powers([-10, -5, 0])).to(
            raise_error(NotPositivePower))
        expect(lambda: tari_T30A.evaluate_powers([15, 15, 15])).to(
            raise_error(IncorrectMaxPower))
        expect(lambda: tari_T30A.evaluate_powers([16, 17.1, 16])).to(
            raise_error(NotNormalizedPower))
        expect(lambda: tari_T30A.evaluate_powers([14, 15.242, 15.242])).to(
            raise_error(IncorrectMinPower))
        assert tari_T30A.evaluate_powers([15.242, 15.242, 16.454])
        expect(lambda: tari_T30A.evaluate_powers([16, 17])).to(
            raise_error(IncorrectPowerNumber, 'Expected 3 power(s) and got 2'))

        tari_T31A = T31A()
        expect(lambda: tari_T31A.evaluate_powers([-10, -5, 0])).to(
            raise_error(NotPositivePower))
        assert tari_T31A.evaluate_powers([10, 13, 16])
        expect(lambda: tari_T31A.evaluate_powers([16, 17])).to(
            raise_error(IncorrectPowerNumber, 'Expected 3 power(s) and got 2'))
        expect(lambda: tari_T31A.evaluate_powers([16, 20, 16])).to(
            raise_error(NotAscendingPowers))

        tari_T61A = T61A()
        expect(lambda: tari_T61A.evaluate_powers([-10, -5, 0, 10, 20])).to(
            raise_error(NotPositivePower))
        assert tari_T61A.evaluate_powers([400, 410, 420, 430, 440, 451])
        assert tari_T61A.evaluate_powers([500, 600, 700, 800, 900, 1000])
        expect(lambda: tari_T61A.evaluate_powers([16, 17])).to(
            raise_error(IncorrectPowerNumber, 'Expected 6 power(s) and got 2'))
        expect(
            lambda: tari_T61A.evaluate_powers([500, 600, 700, 700, 600, 500])
        ).to(
            raise_error(NotAscendingPowers))

        tari_T61B = T61B()
        expect(lambda: tari_T61B.evaluate_powers([-10, -5, 0, 10, 20])).to(
            raise_error(NotPositivePower))
        assert tari_T61B.evaluate_powers([400, 410, 420, 430, 440, 451])
        assert tari_T61B.evaluate_powers([500, 600, 700, 800, 900, 1000])
        expect(lambda: tari_T61B.evaluate_powers([16, 17])).to(
            raise_error(IncorrectPowerNumber, 'Expected 6 power(s) and got 2'))
        expect(
            lambda: tari_T61B.evaluate_powers([500, 600, 700, 700, 600, 500])
        ).to(
            raise_error(NotAscendingPowers))

        tari_T62 = T62()
        expect(lambda: tari_T62.evaluate_powers([-10, -5, 0, 10, 20])).to(
            raise_error(NotPositivePower))
        assert tari_T62.evaluate_powers([400, 410, 420, 430, 440, 451])
        assert tari_T62.evaluate_powers([500, 600, 700, 800, 900, 1000])
        expect(lambda: tari_T62.evaluate_powers([16, 17])).to(
            raise_error(IncorrectPowerNumber, 'Expected 6 power(s) and got 2'))
        expect(
            lambda: tari_T62.evaluate_powers([500, 600, 700, 700, 600, 500])
        ).to(
            raise_error(NotAscendingPowers))

        tari_T63 = T63()
        expect(lambda: tari_T63.evaluate_powers([-10, -5, 0, 10, 20])).to(
            raise_error(NotPositivePower))
        assert tari_T63.evaluate_powers([400, 410, 420, 430, 440, 451])
        assert tari_T63.evaluate_powers([500, 600, 700, 800, 900, 1000])
        expect(lambda: tari_T63.evaluate_powers([16, 17])).to(
            raise_error(IncorrectPowerNumber, 'Expected 6 power(s) and got 2'))
        expect(
            lambda: tari_T63.evaluate_powers([500, 600, 700, 700, 600, 500])
        ).to(
            raise_error(NotAscendingPowers))

        tari_T64 = T64()
        expect(lambda: tari_T64.evaluate_powers([-10, -5, 0, 10, 20])).to(
            raise_error(NotPositivePower))
        assert tari_T64.evaluate_powers([400, 410, 420, 430, 440, 451])
        assert tari_T64.evaluate_powers([500, 600, 700, 800, 900, 1000])
        expect(lambda: tari_T64.evaluate_powers([16, 17])).to(
            raise_error(IncorrectPowerNumber, 'Expected 6 power(s) and got 2'))
        expect(
            lambda: tari_T64.evaluate_powers([500, 600, 700, 700, 600, 500])
        ).to(
            raise_error(NotAscendingPowers))
    with it('should allow to check if a set of powers is correct'):
        tari_T20A = T20A()
        assert len(tari_T20A.evaluate_powers_all_checks([-10]))
        assert len(tari_T20A.evaluate_powers_all_checks([0]))
        assert len(tari_T20A.evaluate_powers_all_checks([3.5])) == 0
        assert len(tari_T20A.evaluate_powers_all_checks([5, 7]))
        assert len(tari_T20A.evaluate_powers_all_checks([100]))

        tari_T30A = T30A()
        assert len(tari_T30A.evaluate_powers_all_checks([-10, -5, 0]))
        assert len(tari_T30A.evaluate_powers_all_checks([15, 15, 15]))
        assert len(tari_T30A.evaluate_powers_all_checks([16, 17.1, 16]))
        assert len(tari_T30A.evaluate_powers_all_checks([14, 15.242, 15.242]))
        assert len(tari_T30A.evaluate_powers_all_checks([15.242, 15.242, 16.454])) == 0
        assert len(tari_T30A.evaluate_powers_all_checks([16, 17]))

        tari_T31A = T31A()
        assert len(tari_T31A.evaluate_powers_all_checks([-10, -5, 0]))
        assert len(tari_T31A.evaluate_powers_all_checks([10, 13, 16])) == 0
        assert len(tari_T31A.evaluate_powers_all_checks([16, 17]))
        assert len(tari_T31A.evaluate_powers_all_checks([16, 20, 16]))

        tari_T61A = T61A()
        assert len(tari_T61A.evaluate_powers_all_checks([-10, -5, 0, 10, 20]))
        assert len(tari_T61A.evaluate_powers_all_checks([400, 410, 420, 430, 440, 451])) == 0
        assert len(tari_T61A.evaluate_powers_all_checks([500, 600, 700, 800, 900, 1000])) == 0
        assert len(tari_T61A.evaluate_powers_all_checks([16, 17]))
        assert len(tari_T61A.evaluate_powers_all_checks([500, 600, 700, 700, 600, 500]))

    with it('shouldn\'t fail due to bad rounding'):
        tari_T20A = T20A()
        assert tari_T20A.evaluate_powers([8050.0/1000])
    with it('should allow to check if a maximum power is correct'):
        tari_T20A = T20A()
        assert not tari_T20A.is_maximum_power_correct(-10)
        assert not tari_T20A.is_maximum_power_correct(0)
        assert tari_T20A.is_maximum_power_correct(7)
        assert tari_T20A.is_maximum_power_correct(10)
        assert not tari_T20A.is_maximum_power_correct(1000)
    with context('without correct_power implemented'):
        with it('should raise NotImplemented on correct_power call'):
            # All 2.X have it so we don't check anything on them here
            # All others don't have it implemented so far
            expect(lambda: T30A().correct_powers([1, 2, 3])).to(
                raise_error(NotImplementedError))
            expect(lambda: T31A().correct_powers([1, 2, 3])).to(
                raise_error(NotImplementedError))
            expect(lambda: T61A().correct_powers([1, 2, 3, 4, 5, 6])).to(
                raise_error(NotImplementedError))
            expect(lambda: T61B().correct_powers([1, 2, 3, 4, 5, 6])).to(
                raise_error(NotImplementedError))
            expect(lambda: T62().correct_powers([1, 2, 3, 4, 5, 6])).to(
                raise_error(NotImplementedError))
            expect(lambda: T63().correct_powers([1, 2, 3, 4, 5, 6])).to(
                raise_error(NotImplementedError))
            expect(lambda: T64().correct_powers([1, 2, 3, 4, 5, 6])).to(
                raise_error(NotImplementedError))
    with context('with correct_power implemented'):
        with it('should return a correct power if a wrong one is sent'):
            t_20A = T20A()
            corr_powers_20A = t_20A.correct_powers([0])
            assert t_20A.are_powers_normalized(corr_powers_20A)

            t_20DHA = T20DHA()
            corr_powers_20DHA = t_20DHA.correct_powers([0])
            assert t_20DHA.are_powers_normalized(corr_powers_20DHA)

            t_20DHS = T20DHS()
            corr_powers_20DHS = t_20DHS.correct_powers([0])
            assert t_20DHS.are_powers_normalized(corr_powers_20DHS)

            t_21A = T21A()
            corr_powers_21A = t_21A.correct_powers([10])
            assert t_21A.are_powers_normalized(corr_powers_21A)

            t_21DHA = T21DHA()
            corr_powers_21DHA = t_21DHA.correct_powers([10])
            assert t_21DHA.are_powers_normalized(corr_powers_21DHA)

            t_21DHS = T21DHS()
            corr_powers_21DHS = t_21DHS.correct_powers([10])
            assert t_21DHS.are_powers_normalized(corr_powers_21DHS)
        with it('should return the same power if it\'s correct'):
            assert T20A().correct_powers([0.330]) == [0.330]
            assert T20DHA().correct_powers([0.345]) == [0.345]
            assert T20DHS().correct_powers([0.660]) == [0.660]
            assert T21A().correct_powers([10.350]) == [10.350]
            assert T21DHA().correct_powers([10.392]) == [10.392]
            assert T21DHS().correct_powers([11.000]) == [11.000]
    with it('should return it\'s min and max powers'):
        assert T20A().get_min_power() == 0
        assert T20DHA().get_min_power() == 0
        assert T20DHS().get_min_power() == 0
        assert T21A().get_min_power() == 10
        assert T21DHA().get_min_power() == 10
        assert T21DHS().get_min_power() == 10
        assert T30A().get_min_power() == 15
        assert T31A().get_min_power() == 1
        assert T61A().get_min_power() == 450
        assert T61B().get_min_power() == 450
        assert T62().get_min_power() == 450
        assert T63().get_min_power() == 450
        assert T64().get_min_power() == 450

        assert T20A().get_max_power() == 10
        assert T20DHA().get_max_power() == 10
        assert T20DHS().get_max_power() == 10
        assert T21A().get_max_power() == 15
        assert T21DHA().get_max_power() == 15
        assert T21DHS().get_max_power() == 15
        # T30A doesn't have a max power
        assert T31A().get_max_power() == 450
        # T6X don't have a max power

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

with context('A 3.1A LB Tariff'):
    with it('must indicate the kva with an integer'):
        def createT31A_LB():
            T31A(kva='1')

        expect(createT31A_LB).to(raise_error(ValueError, 'kva must be an enter value'))

    with it('must activate LB flag'):
        the_tariff = T31A(kva=1)

        assert the_tariff.low_voltage_measure



with description('Getting a tariff by descripion'):

    with it('must return the appropiate tariff and initialize the expected cof'):
        tariffs = [
            ('2.0A', T20A),
            ('2.0DHA', T20DHA),
            ('2.0DHS', T20DHS),
            ('2.1A', T21A),
            ('2.1DHA', T21DHA),
            ('2.1DHS', T21DHS),
            ('3.0A', T30A),
            ('3.1A', T31A),
            ('3.1A LB', T31A),
        ]

        tariff_cof = {
            '2.0A': 'A',
            '2.0DHA': 'B',
            '2.0DHS': 'D',
            '2.1A': 'A',
            '2.1DHA': 'B',
            '2.1DHS': 'D',
            '3.0A': 'C',
            '3.1A': 'C',
            '3.1A LB': 'C',
        }

        for t in tariffs:
            t_obj = get_tariff_by_code(t[0])()
            assert isinstance(t_obj, t[1])
            assert t_obj.cof, "Object doesn't have cof attribute"
            assert t_obj.cof == tariff_cof[t[0]], "Object cof not match with expected one"


    with it('must return None if the code is not in available'):
        t = get_tariff_by_code('NO_EXISTS')
        expect(t).to(be_none)

with description('Correct period for tariff an hour'):
    with before.all:
        self.winter_holiday_day = TIMEZONE.localize(datetime(2014, 11, 1))
        self.summer_holiday_day = TIMEZONE.localize(datetime(2014, 8, 15))
        self.winter_weekend_day = TIMEZONE.localize(datetime(2014, 2, 15))
        self.summer_weekend_day = TIMEZONE.localize(datetime(2014, 6, 21))
        self.winter_laboral_day = TIMEZONE.localize(datetime(2014, 11, 12))
        self.summer_laboral_day = TIMEZONE.localize(datetime(2014, 7, 16))

    with context('2.0DHA'):
        with before.all:
            self.tarifa = T20DHA()
        with it('should have code 2.0DHA'):
            assert self.tarifa.code == '2.0DHA'

        with it('should have correct period on holiday winter data'):
            dia = self.winter_holiday_day
            assert self.tarifa.get_period_by_date(dia).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=1)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=2)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=7)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=8)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=9)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=10)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=11)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=12)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=13)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=14)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=15)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=16)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=17)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=18)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=19)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=22)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=23)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=23, minutes=59)).code == 'P2'

        with it('should have correct period on holiday summer data'):
            dia = self.summer_holiday_day
            assert self.tarifa.get_period_by_date(dia).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=1)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=2)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=7)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=8)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=9)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=10)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=11)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=12)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=13)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=14)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=15)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=16)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=17)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=18)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=19)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=22)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=23)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=24)).code == 'P2'

        with it('should have correct period on laboral winter data'):
            dia = self.winter_laboral_day
            assert self.tarifa.get_period_by_date(dia).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=1)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=2)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=7)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=8)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=9)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=10)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=11)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=12)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=13)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=14)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=15)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=16)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=17)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=18)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=19)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=22)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=23)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=24)).code == 'P2'

        with it('should have correct period on laboral summer data'):
            dia = self.summer_laboral_day
            assert self.tarifa.get_period_by_date(dia).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=1)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=2)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=7)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=8)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=9)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=10)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=11)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=12)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=13)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=14)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=15)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=16)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=17)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=18)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=19)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=22)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=23)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=24)).code == 'P2'

        with it('should have correct period on weekend winter data'):
            dia = self.winter_weekend_day
            assert self.tarifa.get_period_by_date(dia).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=1)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=2)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=7)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=8)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=9)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=10)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=11)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=12)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=13)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=14)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=15)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=16)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=17)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=18)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=19)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=22)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=23)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=24)).code == 'P2'

        with it('should have correct period on weekend summer data'):
            dia = self.summer_weekend_day
            assert self.tarifa.get_period_by_date(dia).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=1)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=2)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=7)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=8)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=9)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=10)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=11)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=12)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=13)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=14)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=15)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=16)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=17)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=18)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=19)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=22)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=23)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=24)).code == 'P2'

    with context('2.0DHS'):
        with before.all:
            self.tarifa = T20DHS()
        with it('should have code 2.0DHS'):
            assert self.tarifa.code == '2.0DHS'

        with it('should have correct period on holiday winter data'):
            dia = self.winter_holiday_day
            assert self.tarifa.get_period_by_date(dia).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=1)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=2)).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=7)).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=8)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=9)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=10)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=11)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=12)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=13)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=14)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=15)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=16)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=17)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=18)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=19)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=22)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=23)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=23, minutes=59)).code == 'P1'

        with it('should have correct period on holiday summer data'):
            dia = self.summer_holiday_day
            assert self.tarifa.get_period_by_date(dia).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=1)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=2)).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=7)).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=8)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=9)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=10)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=11)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=12)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=13)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=14)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=15)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=16)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=17)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=18)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=19)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=22)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=23)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=24)).code == 'P2'

        with it('should have correct period on laboral winter data'):
            dia = self.winter_laboral_day
            assert self.tarifa.get_period_by_date(dia).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=1)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=2)).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=7)).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=8)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=9)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=10)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=11)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=12)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=13)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=14)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=15)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=16)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=17)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=18)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=19)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=22)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=23)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=24)).code == 'P2'

        with it('should have correct period on laboral summer data'):
            dia = self.summer_laboral_day
            assert self.tarifa.get_period_by_date(dia).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=1)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=2)).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=7)).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=8)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=9)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=10)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=11)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=12)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=13)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=14)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=15)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=16)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=17)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=18)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=19)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=22)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=23)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=24)).code == 'P2'

        with it('should have correct period on weekend winter data'):
            dia = self.winter_weekend_day
            assert self.tarifa.get_period_by_date(dia).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=1)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=2)).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=7)).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=8)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=9)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=10)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=11)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=12)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=13)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=14)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=15)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=16)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=17)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=18)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=19)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=22)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=23)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=24)).code == 'P2'

        with it('should have correct period on weekend summer data'):
            dia = self.summer_weekend_day
            assert self.tarifa.get_period_by_date(dia).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=1)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=2)).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=7)).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=8)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=9)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=10)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=11)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=12)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=13)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=14)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=15)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=16)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=17)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=18)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=19)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=22)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=23)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=24)).code == 'P2'

    with context('2.1DHA'):
        with before.all:
            self.tarifa = T21DHA()
        with it('should have code 2.1DHA'):
            assert self.tarifa.code == '2.1DHA'

        with it('should have correct period on holiday winter data'):
            dia = self.winter_holiday_day
            assert self.tarifa.get_period_by_date(dia).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=1)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=2)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=7)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=8)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=9)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=10)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=11)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=12)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=13)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=14)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=15)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=16)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=17)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=18)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=19)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=22)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=23)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=23, minutes=59)).code == 'P2'

        with it('should have correct period on holiday summer data'):
            dia = self.summer_holiday_day
            assert self.tarifa.get_period_by_date(dia).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=1)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=2)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=7)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=8)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=9)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=10)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=11)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=12)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=13)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=14)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=15)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=16)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=17)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=18)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=19)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=22)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=23)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=24)).code == 'P2'

        with it('should have correct period on laboral winter data'):
            dia = self.winter_laboral_day
            assert self.tarifa.get_period_by_date(dia).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=1)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=2)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=7)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=8)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=9)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=10)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=11)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=12)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=13)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=14)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=15)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=16)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=17)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=18)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=19)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=22)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=23)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=24)).code == 'P2'

        with it('should have correct period on laboral summer data'):
            dia = self.summer_laboral_day
            assert self.tarifa.get_period_by_date(dia).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=1)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=2)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=7)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=8)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=9)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=10)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=11)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=12)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=13)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=14)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=15)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=16)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=17)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=18)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=19)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=22)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=23)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=24)).code == 'P2'

        with it('should have correct period on weekend winter data'):
            dia = self.winter_weekend_day
            assert self.tarifa.get_period_by_date(dia).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=1)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=2)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=7)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=8)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=9)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=10)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=11)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=12)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=13)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=14)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=15)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=16)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=17)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=18)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=19)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=22)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=23)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=24)).code == 'P2'

        with it('should have correct period on weekend summer data'):
            dia = self.summer_weekend_day
            assert self.tarifa.get_period_by_date(dia).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=1)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=2)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=7)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=8)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=9)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=10)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=11)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=12)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=13)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=14)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=15)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=16)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=17)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=18)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=19)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=22)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=23)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=24)).code == 'P2'



    with context('2.1DHS'):
        with before.all:
            self.tarifa = T21DHS()
        with it('should have code 2.1DHS'):
            assert self.tarifa.code == '2.1DHS'

        with it('should have correct period on holiday winter data'):
            dia = self.winter_holiday_day
            assert self.tarifa.get_period_by_date(dia).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=1)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=2)).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=7)).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=8)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=9)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=10)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=11)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=12)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=13)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=14)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=15)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=16)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=17)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=18)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=19)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=22)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=23)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=23, minutes=59)).code == 'P1'

        with it('should have correct period on holiday summer data'):
            dia = self.summer_holiday_day
            assert self.tarifa.get_period_by_date(dia).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=1)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=2)).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=7)).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=8)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=9)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=10)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=11)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=12)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=13)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=14)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=15)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=16)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=17)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=18)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=19)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=22)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=23)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=24)).code == 'P2'

        with it('should have correct period on laboral winter data'):
            dia = self.winter_laboral_day
            assert self.tarifa.get_period_by_date(dia).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=1)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=2)).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=7)).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=8)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=9)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=10)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=11)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=12)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=13)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=14)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=15)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=16)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=17)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=18)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=19)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=22)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=23)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=24)).code == 'P2'

        with it('should have correct period on laboral summer data'):
            dia = self.summer_laboral_day
            assert self.tarifa.get_period_by_date(dia).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=1)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=2)).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=7)).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=8)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=9)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=10)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=11)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=12)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=13)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=14)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=15)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=16)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=17)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=18)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=19)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=22)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=23)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=24)).code == 'P2'

        with it('should have correct period on weekend winter data'):
            dia = self.winter_weekend_day
            assert self.tarifa.get_period_by_date(dia).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=1)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=2)).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=7)).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=8)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=9)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=10)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=11)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=12)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=13)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=14)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=15)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=16)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=17)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=18)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=19)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=22)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=23)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=24)).code == 'P2'

        with it('should have correct period on weekend summer data'):
            dia = self.summer_weekend_day
            assert self.tarifa.get_period_by_date(dia).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=1)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=2)).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=7)).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=8)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=9)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=10)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=11)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=12)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=13)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=14)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=15)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=16)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=17)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=18)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=19)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=22)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=23)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=24)).code == 'P2'

    with context('3.0A'):
        with before.all:
            self.tarifa = T30A()
        with it('should have code 3.0A'):
            assert self.tarifa.code == '3.0A'

        with it('should have correct period on holiday winter data'):
            dia = self.winter_holiday_day
            assert self.tarifa.get_period_by_date(dia).code == 'P2'  # points to friday 31/10/17
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=1)).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=2)).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=8)).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=9)).code == 'P5'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=17)).code == 'P5'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=18)).code == 'P5'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=19)).code == 'P4'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=22)).code == 'P4'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=23)).code == 'P5'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=24)).code == 'P5'

        with it('should have correct period on holiday summer data'):
            dia = self.summer_holiday_day
            assert self.tarifa.get_period_by_date(dia).code == 'P2'  # points to thursday 14/08/17
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=1)).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=2)).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=8)).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=9)).code == 'P5'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=10)).code == 'P5'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=11)).code == 'P5'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=12)).code == 'P4'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=15)).code == 'P4'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=16)).code == 'P5'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=17)).code == 'P5'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=23)).code == 'P5'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=24)).code == 'P5'

        with it('should have correct period on laboral winter data'):
            dia = self.winter_laboral_day
            assert self.tarifa.get_period_by_date(dia).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=1)).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=2)).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=8)).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=9)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=17)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=18)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=19)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=22)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=23)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=24)).code == 'P2'

        with it('should have correct period on laboral summer data'):
            dia = self.summer_laboral_day
            assert self.tarifa.get_period_by_date(dia).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=1)).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=2)).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=8)).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=9)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=10)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=11)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=12)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=15)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=16)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=17)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=23)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=24)).code == 'P2'

        with it('should have correct period on weekend winter data'):
            dia = self.winter_weekend_day
            assert self.tarifa.get_period_by_date(dia).code == 'P2' # points to latest hour of friday
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=1)).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=2)).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=8)).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=9)).code == 'P5'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=17)).code == 'P5'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=18)).code == 'P5'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=19)).code == 'P4'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=22)).code == 'P4'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=23)).code == 'P5'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=24)).code == 'P5'

        with it('should have correct period on weekend summer data'):
            dia = self.summer_weekend_day
            assert self.tarifa.get_period_by_date(dia).code == 'P2' # points to latest hour of friday
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=1)).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=2)).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=8)).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=9)).code == 'P5'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=10)).code == 'P5'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=11)).code == 'P5'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=12)).code == 'P4'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=15)).code == 'P4'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=16)).code == 'P5'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=17)).code == 'P5'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=23)).code == 'P5'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=24)).code == 'P5'

        with context("If doesn't have holidays"):
            with before.all:
                self.tarifa = T30ANoFestivos()
            with it('should have code 3.0A'):
                assert self.tarifa.code == '3.0A'

            with it('should have correct period on holiday winter data'):
                dia = self.winter_holiday_day
                assert self.tarifa.get_period_by_date(
                    dia).code == 'P2'  # points to friday 31/10/17
                assert self.tarifa.get_period_by_date(
                    dia + timedelta(hours=1)).code == 'P3'
                assert self.tarifa.get_period_by_date(
                    dia + timedelta(hours=2)).code == 'P3'
                assert self.tarifa.get_period_by_date(
                    dia + timedelta(hours=8)).code == 'P3'
                assert self.tarifa.get_period_by_date(
                    dia + timedelta(hours=9)).code == 'P2'
                assert self.tarifa.get_period_by_date(
                    dia + timedelta(hours=17)).code == 'P2'
                assert self.tarifa.get_period_by_date(
                    dia + timedelta(hours=18)).code == 'P2'
                assert self.tarifa.get_period_by_date(
                    dia + timedelta(hours=19)).code == 'P1'
                assert self.tarifa.get_period_by_date(
                    dia + timedelta(hours=22)).code == 'P1'
                assert self.tarifa.get_period_by_date(
                    dia + timedelta(hours=23)).code == 'P2'
                assert self.tarifa.get_period_by_date(
                    dia + timedelta(hours=24)).code == 'P2'

            with it('should have correct period on holiday summer data'):
                dia = self.summer_holiday_day
                assert self.tarifa.get_period_by_date(
                    dia).code == 'P2'  # points to thursday 14/08/17
                assert self.tarifa.get_period_by_date(
                    dia + timedelta(hours=1)).code == 'P3'
                assert self.tarifa.get_period_by_date(
                    dia + timedelta(hours=2)).code == 'P3'
                assert self.tarifa.get_period_by_date(
                    dia + timedelta(hours=8)).code == 'P3'
                assert self.tarifa.get_period_by_date(
                    dia + timedelta(hours=9)).code == 'P2'
                assert self.tarifa.get_period_by_date(
                    dia + timedelta(hours=10)).code == 'P2'
                assert self.tarifa.get_period_by_date(
                    dia + timedelta(hours=11)).code == 'P2'
                assert self.tarifa.get_period_by_date(
                    dia + timedelta(hours=12)).code == 'P1'
                assert self.tarifa.get_period_by_date(
                    dia + timedelta(hours=15)).code == 'P1'
                assert self.tarifa.get_period_by_date(
                    dia + timedelta(hours=16)).code == 'P2'
                assert self.tarifa.get_period_by_date(
                    dia + timedelta(hours=17)).code == 'P2'
                assert self.tarifa.get_period_by_date(
                    dia + timedelta(hours=23)).code == 'P2'
                assert self.tarifa.get_period_by_date(
                    dia + timedelta(hours=24)).code == 'P2'

            with it('should have correct period on laboral winter data'):
                dia = self.winter_laboral_day
                assert self.tarifa.get_period_by_date(dia).code == 'P2'
                assert self.tarifa.get_period_by_date(
                    dia + timedelta(hours=1)).code == 'P3'
                assert self.tarifa.get_period_by_date(
                    dia + timedelta(hours=2)).code == 'P3'
                assert self.tarifa.get_period_by_date(
                    dia + timedelta(hours=8)).code == 'P3'
                assert self.tarifa.get_period_by_date(
                    dia + timedelta(hours=9)).code == 'P2'
                assert self.tarifa.get_period_by_date(
                    dia + timedelta(hours=17)).code == 'P2'
                assert self.tarifa.get_period_by_date(
                    dia + timedelta(hours=18)).code == 'P2'
                assert self.tarifa.get_period_by_date(
                    dia + timedelta(hours=19)).code == 'P1'
                assert self.tarifa.get_period_by_date(
                    dia + timedelta(hours=22)).code == 'P1'
                assert self.tarifa.get_period_by_date(
                    dia + timedelta(hours=23)).code == 'P2'
                assert self.tarifa.get_period_by_date(
                    dia + timedelta(hours=24)).code == 'P2'

            with it('should have correct period on laboral summer data'):
                dia = self.summer_laboral_day
                assert self.tarifa.get_period_by_date(dia).code == 'P2'
                assert self.tarifa.get_period_by_date(
                    dia + timedelta(hours=1)).code == 'P3'
                assert self.tarifa.get_period_by_date(
                    dia + timedelta(hours=2)).code == 'P3'
                assert self.tarifa.get_period_by_date(
                    dia + timedelta(hours=8)).code == 'P3'
                assert self.tarifa.get_period_by_date(
                    dia + timedelta(hours=9)).code == 'P2'
                assert self.tarifa.get_period_by_date(
                    dia + timedelta(hours=10)).code == 'P2'
                assert self.tarifa.get_period_by_date(
                    dia + timedelta(hours=11)).code == 'P2'
                assert self.tarifa.get_period_by_date(
                    dia + timedelta(hours=12)).code == 'P1'
                assert self.tarifa.get_period_by_date(
                    dia + timedelta(hours=15)).code == 'P1'
                assert self.tarifa.get_period_by_date(
                    dia + timedelta(hours=16)).code == 'P2'
                assert self.tarifa.get_period_by_date(
                    dia + timedelta(hours=17)).code == 'P2'
                assert self.tarifa.get_period_by_date(
                    dia + timedelta(hours=23)).code == 'P2'
                assert self.tarifa.get_period_by_date(
                    dia + timedelta(hours=24)).code == 'P2'

            with it('should have correct period on weekend winter data'):
                dia = self.winter_weekend_day
                assert self.tarifa.get_period_by_date(
                    dia).code == 'P2'  # points to latest hour of friday
                assert self.tarifa.get_period_by_date(
                    dia + timedelta(hours=1)).code == 'P3'
                assert self.tarifa.get_period_by_date(
                    dia + timedelta(hours=2)).code == 'P3'
                assert self.tarifa.get_period_by_date(
                    dia + timedelta(hours=8)).code == 'P3'
                assert self.tarifa.get_period_by_date(
                    dia + timedelta(hours=9)).code == 'P2'
                assert self.tarifa.get_period_by_date(
                    dia + timedelta(hours=17)).code == 'P2'
                assert self.tarifa.get_period_by_date(
                    dia + timedelta(hours=18)).code == 'P2'
                assert self.tarifa.get_period_by_date(
                    dia + timedelta(hours=19)).code == 'P1'
                assert self.tarifa.get_period_by_date(
                    dia + timedelta(hours=22)).code == 'P1'
                assert self.tarifa.get_period_by_date(
                    dia + timedelta(hours=23)).code == 'P2'
                assert self.tarifa.get_period_by_date(
                    dia + timedelta(hours=24)).code == 'P2'

            with it('should have correct period on weekend summer data'):
                dia = self.summer_weekend_day
                assert self.tarifa.get_period_by_date(
                    dia).code == 'P2'  # points to latest hour of friday
                assert self.tarifa.get_period_by_date(
                    dia + timedelta(hours=1)).code == 'P3'
                assert self.tarifa.get_period_by_date(
                    dia + timedelta(hours=2)).code == 'P3'
                assert self.tarifa.get_period_by_date(
                    dia + timedelta(hours=8)).code == 'P3'
                assert self.tarifa.get_period_by_date(
                    dia + timedelta(hours=9)).code == 'P2'
                assert self.tarifa.get_period_by_date(
                    dia + timedelta(hours=10)).code == 'P2'
                assert self.tarifa.get_period_by_date(
                    dia + timedelta(hours=11)).code == 'P2'
                assert self.tarifa.get_period_by_date(
                    dia + timedelta(hours=12)).code == 'P1'
                assert self.tarifa.get_period_by_date(
                    dia + timedelta(hours=15)).code == 'P1'
                assert self.tarifa.get_period_by_date(
                    dia + timedelta(hours=16)).code == 'P2'
                assert self.tarifa.get_period_by_date(
                    dia + timedelta(hours=17)).code == 'P2'
                assert self.tarifa.get_period_by_date(
                    dia + timedelta(hours=23)).code == 'P2'
                assert self.tarifa.get_period_by_date(
                    dia + timedelta(hours=24)).code == 'P2'

    with context('3.0A with just one period'):
        with before.all:
            self.tarifa = T30A_one_period()
        with it('should have code 3.0A'):
            assert self.tarifa.code == '3.0A'

        with it('should have correct period on holiday winter data'):
            dia = self.winter_holiday_day
            for hour in range(1,25):
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=hour)).code == 'P1'

        with it('should have correct period on holiday summer data'):
            dia = self.summer_holiday_day
            for hour in range(1,25):
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=hour)).code == 'P1'

        with it('should have correct period on laboral winter data'):
            dia = self.winter_laboral_day
            for hour in range(1,25):
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=hour)).code == 'P1'

        with it('should have correct period on laboral summer data'):
            dia = self.summer_laboral_day
            for hour in range(1,25):
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=hour)).code == 'P1'

        with it('should have correct period on weekend winter data'):
            dia = self.winter_weekend_day
            for hour in range(1,25):
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=hour)).code == 'P1'

        with it('should have correct period on weekend summer data'):
            dia = self.summer_weekend_day
            for hour in range(1,25):
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=hour)).code == 'P1'


    with context('3.1A'):
        with before.all:
            self.tarifa = T31A()
        with it('should have code 3.1A'):
            assert self.tarifa.code == '3.1A'

        with it('should have correct period on holiday winter data'):
            dia = self.winter_holiday_day
            assert self.tarifa.get_period_by_date(dia).code == 'P2'  # points to friday 31/10/17
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=1)).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=2)).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=8)).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=9)).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=18)).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=19)).code == 'P5'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=22)).code == 'P5'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=23)).code == 'P5'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=24)).code == 'P5'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=25)).code == 'P6'

        with it('should have correct period on holiday summer data'):
            dia = self.summer_holiday_day
            assert self.tarifa.get_period_by_date(dia).code == 'P2'  # points to thursday 14/08/17
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=1)).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=2)).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=8)).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=15)).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=16)).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=17)).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=18)).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=19)).code == 'P5'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=20)).code == 'P5'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=23)).code == 'P5'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=24)).code == 'P5'

        with it('should have correct period on laboral winter data'):
            dia = self.winter_laboral_day
            assert self.tarifa.get_period_by_date(dia).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=1)).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=2)).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=8)).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=9)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=11)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=15)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=17)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=18)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=19)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=22)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=23)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=24)).code == 'P2'

        with it('should have correct period on laboral summer data'):
            dia = self.summer_laboral_day
            assert self.tarifa.get_period_by_date(dia).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=1)).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=2)).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=8)).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=9)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=10)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=11)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=12)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=15)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=16)).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=17)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=20)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=23)).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=24)).code == 'P2'

        with it('should have correct period on weekend winter data'):
            dia = self.winter_weekend_day
            assert self.tarifa.get_period_by_date(dia).code == 'P2' # points to latest hour of friday
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=1)).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=2)).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=8)).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=9)).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=18)).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=19)).code == 'P5'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=22)).code == 'P5'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=23)).code == 'P5'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=24)).code == 'P5'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=25)).code == 'P6'

        with it('should have correct period on weekend summer data'):
            dia = self.summer_weekend_day
            assert self.tarifa.get_period_by_date(dia).code == 'P2' # points to latest hour of friday
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=1)).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=2)).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=8)).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=15)).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=16)).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=17)).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=18)).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=19)).code == 'P5'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=20)).code == 'P5'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=23)).code == 'P5'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=24)).code == 'P5'


    with context('3.1A with just one period'):
        with before.all:
            self.tarifa = T31A_one_period()
        with it('should have code 3.1A'):
            assert self.tarifa.code == '3.1A'

        with it('should have correct period on holiday winter data'):
            dia = self.winter_holiday_day
            for hour in range(1,25):
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=hour)).code == 'P1'

        with it('should have correct period on holiday summer data'):
            dia = self.summer_holiday_day
            for hour in range(1,25):
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=hour)).code == 'P1'

        with it('should have correct period on laboral winter data'):
            dia = self.winter_laboral_day
            for hour in range(1,25):
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=hour)).code == 'P1'

        with it('should have correct period on laboral summer data'):
            dia = self.summer_laboral_day
            for hour in range(1,25):
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=hour)).code == 'P1'

        with it('should have correct period on weekend winter data'):
            dia = self.winter_weekend_day
            for hour in range(1,25):
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=hour)).code == 'P1'

        with it('should have correct period on weekend summer data'):
            dia = self.summer_weekend_day
            for hour in range(1,25):
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=hour)).code == 'P1'

# New TD tariffs
with description("TD tariffs"):
    with before.all:
        self.holidays = [datetime(2021, 1, 1).date(),
                         datetime(2021, 1, 6).date(),
                         datetime(2021, 4, 18).date(),
                         datetime(2021, 5, 1).date(),
                         datetime(2021, 8, 15).date(),
                         datetime(2021, 11, 1).date(),
                         datetime(2021, 12, 6).date(),
                         datetime(2021, 12, 8).date(),
                         datetime(2021, 12, 25).date(),
                         # 2022
                         datetime(2022, 1, 1).date(),
                         datetime(2022, 1, 6).date(),
                         datetime(2022, 4, 18).date(),
                         datetime(2022, 5, 1).date(),
                         datetime(2022, 8, 15).date(),
                         datetime(2022, 11, 1).date(),
                         datetime(2022, 12, 6).date(),
                         datetime(2022, 12, 8).date(),
                         datetime(2022, 12, 25).date()
                         ]

        self.winter_holiday_day = datetime(2022, 1, 6)
        self.summer_holiday_day = datetime(2021, 8, 15)
        self.winter_weekend_day = datetime(2021, 12, 18)
        self.summer_weekend_day = datetime(2021, 6, 20)
        self.winter_laboral_day = datetime(2021, 11, 12)
        self.summer_laboral_day = datetime(2021, 7, 16)

        # different season days to test 6 periods
        self.january_day = datetime(2022, 1, 19)  # "A" in zones 1, 4 and 5. "M" in zones 2 and 3.
        self.march_day = datetime(2022, 3, 15)  # "M" in zones 1, 3 and 4. "B" in zones 2 and 5.
        self.april_day = datetime(2022, 4, 13)  # "B" in all zones.
        self.may_day = datetime(2022, 5, 4)  # "MA" in zone 2. "B" in zones 1 and 3, 4 and 5.
        self.june_day = datetime(2021, 6, 4)  # "A" in zone 2. "M" in zones 1 and 5. "B" in zones 3 and 4.
        self.august_day = datetime(2021, 8, 16)  # "A" in zones 2, 3, 4 and 5. "M" in zone 1.
        self.december_day = datetime(2021, 12, 13)  # "A" in zone 1, "MA" in zones 3 and 5, "M" in zone 2 and 4.
    with context("2.0TD"):
        with before.all:
            self.tarifa = T20TD()

        with it('should have code 2.0TD'):
            assert self.tarifa.code == '2.0TD'

        with it('should have correct power margins and type'):
            assert self.tarifa.type == 'BT'
            assert self.tarifa.min_power == 0
            assert self.tarifa.max_power == 15

        with it('should have correct geom zone'):
            assert self.tarifa.geom_zone == '1'

        with it('should have correct energy and power periods'):
            assert len(self.tarifa.energy_periods) == 3
            assert len(self.tarifa.power_periods) == 2
            assert self.tarifa.get_number_of_periods() == 3
            assert not self.tarifa.has_holidays_periods

        with it('should allow to check if a set of powers is correct'):
            expect(lambda: self.tarifa.evaluate_powers([-10, 5])).to(raise_error(NotPositivePower))
            expect(lambda: self.tarifa.evaluate_powers([0, 5])).to(raise_error(NotPositivePower))
            expect(lambda: self.tarifa.evaluate_powers([5.55, 5])).to(raise_error(NotNormalizedPower))
            expect(lambda: self.tarifa.evaluate_powers([5.5])).to(raise_error(IncorrectPowerNumber, 'Expected 2 power(s) and got 1'))
            expect(lambda: self.tarifa.evaluate_powers([100, 200])).to(raise_error(IncorrectMaxPower))
            assert self.tarifa.evaluate_powers([5, 7])
            expect(lambda: self.tarifa.evaluate_powers([0, 0], allow_zero_power=True)).to(raise_error(IncorrectMaxPower, 'Power 0 is not between 0 and 15'))
            assert self.tarifa.evaluate_powers([0, 10], allow_zero_power=True)
            assert self.tarifa.evaluate_powers([10, 0], allow_zero_power=True)

        with it('should have correct energy period on holiday winter data'):
            dia = self.winter_holiday_day
            assert self.tarifa.get_period_by_date(dia, self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=1), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=2), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=3), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=4), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=5), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=6), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=7), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=8), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=9), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=10), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=11), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=12), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=13), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=14), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=15), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=16), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=17), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=18), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=19), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=20), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=21), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=22), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=23), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=23, minutes=59), self.holidays).code == 'P3'

        with it('should have correct energy period on holiday summer data'):
            dia = self.summer_holiday_day
            assert self.tarifa.get_period_by_date(dia, self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=1), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=2), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=3), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=4), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=5), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=6), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=7), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=8), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=9), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=10), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=11), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=12), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=13), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=14), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=15), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=16), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=17), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=18), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=19), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=20), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=21), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=22), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=23), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=23, minutes=59), self.holidays).code == 'P3'

        with it('should have correct energy period on laboral winter data'):
            dia = self.winter_laboral_day
            assert self.tarifa.get_period_by_date(dia, self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=1), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=2), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=3), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=4), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=5), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=6), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=7), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=8), self.holidays).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=9), self.holidays).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=10), self.holidays).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=11), self.holidays).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=12), self.holidays).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=13), self.holidays).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=14), self.holidays).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=15), self.holidays).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=16), self.holidays).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=17), self.holidays).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=18), self.holidays).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=19), self.holidays).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=20), self.holidays).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=21), self.holidays).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=22), self.holidays).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=23), self.holidays).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=23, minutes=59), self.holidays).code == 'P2'

        with it('should have correct energy period on laboral summer data'):
            dia = self.summer_laboral_day
            assert self.tarifa.get_period_by_date(dia, self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=1), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=2), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=3), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=4), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=5), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=6), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=7), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=8), self.holidays).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=9), self.holidays).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=10), self.holidays).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=11), self.holidays).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=12), self.holidays).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=13), self.holidays).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=14), self.holidays).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=15), self.holidays).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=16), self.holidays).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=17), self.holidays).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=18), self.holidays).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=19), self.holidays).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=20), self.holidays).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=21), self.holidays).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=22), self.holidays).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=23), self.holidays).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=23, minutes=59), self.holidays).code == 'P2'

        with it('should have correct energy period on weekend winter data'):
            dia = self.winter_weekend_day
            assert self.tarifa.get_period_by_date(dia, self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=1), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=2), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=3), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=4), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=5), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=6), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=7), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=8), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=9), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=10), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=11), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=12), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=13), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=14), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=15), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=16), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=17), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=18), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=19), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=20), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=21), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=22), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=23), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=23, minutes=59), self.holidays).code == 'P3'

        with it('should have correct energy period on weekend summer data'):
            dia = self.summer_weekend_day
            assert self.tarifa.get_period_by_date(dia, self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=1), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=2), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=3), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=4), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=5), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=6), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=7), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=8), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=9), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=10), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=11), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=12), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=13), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=14), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=15), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=16), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=17), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=18), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=19), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=20), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=21), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=22), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=23), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=23, minutes=59), self.holidays).code == 'P3'

        with it('must have the correct energy period on time change days'):
            assert self.tarifa.get_period_by_timestamp('2021-03-28 01') == 'P3'
            assert self.tarifa.get_period_by_timestamp('2021-03-28 02') == 'P3'
            assert self.tarifa.get_period_by_timestamp('2021-03-28 03') == 'P3'
            assert self.tarifa.get_period_by_timestamp('2021-03-28 04') == 'P3'
            assert self.tarifa.get_period_by_timestamp('2021-03-28 05') == 'P3'
            assert self.tarifa.get_period_by_timestamp('2021-03-28 06') == 'P3'
            assert self.tarifa.get_period_by_timestamp('2021-03-28 07') == 'P3'
            assert self.tarifa.get_period_by_timestamp('2021-03-28 08') == 'P3'
            assert self.tarifa.get_period_by_timestamp('2021-03-28 09') == 'P3'
            assert self.tarifa.get_period_by_timestamp('2021-03-28 10') == 'P3'
            assert self.tarifa.get_period_by_timestamp('2021-03-28 11') == 'P3'
            assert self.tarifa.get_period_by_timestamp('2021-03-28 12') == 'P3'
            assert self.tarifa.get_period_by_timestamp('2021-03-28 13') == 'P3'
            assert self.tarifa.get_period_by_timestamp('2021-03-28 14') == 'P3'
            assert self.tarifa.get_period_by_timestamp('2021-03-28 15') == 'P3'
            assert self.tarifa.get_period_by_timestamp('2021-03-28 16') == 'P3'
            assert self.tarifa.get_period_by_timestamp('2021-03-28 17') == 'P3'
            assert self.tarifa.get_period_by_timestamp('2021-03-28 18') == 'P3'
            assert self.tarifa.get_period_by_timestamp('2021-03-28 19') == 'P3'
            assert self.tarifa.get_period_by_timestamp('2021-03-28 20') == 'P3'
            assert self.tarifa.get_period_by_timestamp('2021-03-28 21') == 'P3'
            assert self.tarifa.get_period_by_timestamp('2021-03-28 22') == 'P3'
            assert self.tarifa.get_period_by_timestamp('2021-03-28 23') == 'P3'

            assert self.tarifa.get_period_by_timestamp('2021-10-24 01') == 'P3'
            assert self.tarifa.get_period_by_timestamp('2021-10-24 02') == 'P3'
            assert self.tarifa.get_period_by_timestamp('2021-10-24 03') == 'P3'
            assert self.tarifa.get_period_by_timestamp('2021-10-24 04') == 'P3'
            assert self.tarifa.get_period_by_timestamp('2021-10-24 05') == 'P3'
            assert self.tarifa.get_period_by_timestamp('2021-10-24 06') == 'P3'
            assert self.tarifa.get_period_by_timestamp('2021-10-24 07') == 'P3'
            assert self.tarifa.get_period_by_timestamp('2021-10-24 08') == 'P3'
            assert self.tarifa.get_period_by_timestamp('2021-10-24 09') == 'P3'
            assert self.tarifa.get_period_by_timestamp('2021-10-24 10') == 'P3'
            assert self.tarifa.get_period_by_timestamp('2021-10-24 11') == 'P3'
            assert self.tarifa.get_period_by_timestamp('2021-10-24 12') == 'P3'
            assert self.tarifa.get_period_by_timestamp('2021-10-24 13') == 'P3'
            assert self.tarifa.get_period_by_timestamp('2021-10-24 14') == 'P3'
            assert self.tarifa.get_period_by_timestamp('2021-10-24 15') == 'P3'
            assert self.tarifa.get_period_by_timestamp('2021-10-24 16') == 'P3'
            assert self.tarifa.get_period_by_timestamp('2021-10-24 17') == 'P3'
            assert self.tarifa.get_period_by_timestamp('2021-10-24 18') == 'P3'
            assert self.tarifa.get_period_by_timestamp('2021-10-24 19') == 'P3'
            assert self.tarifa.get_period_by_timestamp('2021-10-24 20') == 'P3'
            assert self.tarifa.get_period_by_timestamp('2021-10-24 21') == 'P3'
            assert self.tarifa.get_period_by_timestamp('2021-10-24 22') == 'P3'
            assert self.tarifa.get_period_by_timestamp('2021-10-24 23') == 'P3'
            assert self.tarifa.get_period_by_timestamp('2021-10-24 24') == 'P3'
            assert self.tarifa.get_period_by_timestamp('2021-10-24 25') == 'P3'

        with it('should have correct power period'):
            dia = self.summer_weekend_day
            assert self.tarifa.get_period_by_date(dia, self.holidays, magn='tp').code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=1), self.holidays, magn='tp').code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=2), self.holidays, magn='tp').code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=3), self.holidays, magn='tp').code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=4), self.holidays, magn='tp').code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=5), self.holidays, magn='tp').code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=6), self.holidays, magn='tp').code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=7), self.holidays, magn='tp').code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=8), self.holidays, magn='tp').code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=9), self.holidays, magn='tp').code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=10), self.holidays, magn='tp').code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=11), self.holidays, magn='tp').code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=12), self.holidays, magn='tp').code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=13), self.holidays, magn='tp').code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=14), self.holidays, magn='tp').code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=15), self.holidays, magn='tp').code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=16), self.holidays, magn='tp').code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=17), self.holidays, magn='tp').code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=18), self.holidays, magn='tp').code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=19), self.holidays, magn='tp').code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=20), self.holidays, magn='tp').code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=21), self.holidays, magn='tp').code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=22), self.holidays, magn='tp').code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=23), self.holidays, magn='tp').code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=23, minutes=59), self.holidays,
                                                  magn='tp').code == 'P2'

    with context("3.0TD"):
        with before.all:
            self.tarifa = T30TD()

        with it('should have code 3.0TD'):
            assert self.tarifa.code == '3.0TD'

        with it('should have correct power margins and type'):
            assert self.tarifa.type == 'BT'
            assert self.tarifa.min_power == 15
            assert self.tarifa.max_power == 100000

        with it('should have correct energy and power periods'):
            assert len(self.tarifa.energy_periods) == 6
            assert len(self.tarifa.power_periods) == 6
            assert self.tarifa.get_number_of_periods() == 6
            assert not self.tarifa.has_holidays_periods

        with it('should have correct energy period on holiday winter data'):
            dia = self.winter_holiday_day
            assert self.tarifa.get_period_by_date(dia, self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=1), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=2), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=3), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=4), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=5), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=6), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=7), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=8), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=9), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=10), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=11), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=12), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=13), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=14), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=15), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=16), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=17), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=18), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=19), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=20), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=21), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=22), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=23), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=23, minutes=59), self.holidays).code == 'P6'

        with it('should have correct energy period on holiday summer data'):
            dia = self.summer_holiday_day
            assert self.tarifa.get_period_by_date(dia, self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=1), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=2), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=3), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=4), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=5), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=6), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=7), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=8), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=9), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=10), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=11), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=12), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=13), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=14), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=15), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=16), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=17), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=18), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=19), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=20), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=21), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=22), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=23), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=23, minutes=59), self.holidays).code == 'P6'

        with it('should have correct energy period on laboral winter data'):
            dia = self.winter_laboral_day
            assert self.tarifa.get_period_by_date(dia, self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=1), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=2), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=3), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=4), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=5), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=6), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=7), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=8), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=9), self.holidays).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=10), self.holidays).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=11), self.holidays).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=12), self.holidays).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=13), self.holidays).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=14), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=15), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=16), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=17), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=18), self.holidays).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=19), self.holidays).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=20), self.holidays).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=21), self.holidays).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=22), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=23), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=23, minutes=59), self.holidays).code == 'P3'

        with it('should have correct energy period on laboral summer data'):
            dia = self.summer_laboral_day
            assert self.tarifa.get_period_by_date(dia, self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=1), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=2), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=3), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=4), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=5), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=6), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=7), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=8), self.holidays).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=9), self.holidays).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=10), self.holidays).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=11), self.holidays).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=12), self.holidays).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=13), self.holidays).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=14), self.holidays).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=15), self.holidays).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=16), self.holidays).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=17), self.holidays).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=18), self.holidays).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=19), self.holidays).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=20), self.holidays).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=21), self.holidays).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=22), self.holidays).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=23), self.holidays).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=23, minutes=59), self.holidays).code == 'P2'

        with it('should have correct energy period on weekend winter data'):
            dia = self.winter_weekend_day
            assert self.tarifa.get_period_by_date(dia, self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=1), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=2), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=3), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=4), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=5), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=6), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=7), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=8), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=9), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=10), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=11), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=12), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=13), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=14), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=15), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=16), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=17), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=18), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=19), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=20), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=21), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=22), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=23), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=23, minutes=59), self.holidays).code == 'P6'

        with it('should have correct energy period on weekend summer data'):
            dia = self.summer_weekend_day
            assert self.tarifa.get_period_by_date(dia, self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=1), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=2), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=3), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=4), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=5), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=6), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=7), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=8), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=9), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=10), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=11), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=12), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=13), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=14), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=15), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=16), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=17), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=18), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=19), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=20), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=21), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=22), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=23), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=23, minutes=59), self.holidays).code == 'P6'

        with it('must have the correct energy period on time change days'):
            assert self.tarifa.get_period_by_timestamp('2021-03-28 01') == 'P6'
            assert self.tarifa.get_period_by_timestamp('2021-03-28 02') == 'P6'
            assert self.tarifa.get_period_by_timestamp('2021-03-28 03') == 'P6'
            assert self.tarifa.get_period_by_timestamp('2021-03-28 04') == 'P6'
            assert self.tarifa.get_period_by_timestamp('2021-03-28 05') == 'P6'
            assert self.tarifa.get_period_by_timestamp('2021-03-28 06') == 'P6'
            assert self.tarifa.get_period_by_timestamp('2021-03-28 07') == 'P6'
            assert self.tarifa.get_period_by_timestamp('2021-03-28 08') == 'P6'
            assert self.tarifa.get_period_by_timestamp('2021-03-28 09') == 'P6'
            assert self.tarifa.get_period_by_timestamp('2021-03-28 10') == 'P6'
            assert self.tarifa.get_period_by_timestamp('2021-03-28 11') == 'P6'
            assert self.tarifa.get_period_by_timestamp('2021-03-28 12') == 'P6'
            assert self.tarifa.get_period_by_timestamp('2021-03-28 13') == 'P6'
            assert self.tarifa.get_period_by_timestamp('2021-03-28 14') == 'P6'
            assert self.tarifa.get_period_by_timestamp('2021-03-28 15') == 'P6'
            assert self.tarifa.get_period_by_timestamp('2021-03-28 16') == 'P6'
            assert self.tarifa.get_period_by_timestamp('2021-03-28 17') == 'P6'
            assert self.tarifa.get_period_by_timestamp('2021-03-28 18') == 'P6'
            assert self.tarifa.get_period_by_timestamp('2021-03-28 19') == 'P6'
            assert self.tarifa.get_period_by_timestamp('2021-03-28 20') == 'P6'
            assert self.tarifa.get_period_by_timestamp('2021-03-28 21') == 'P6'
            assert self.tarifa.get_period_by_timestamp('2021-03-28 22') == 'P6'
            assert self.tarifa.get_period_by_timestamp('2021-03-28 23') == 'P6'

            assert self.tarifa.get_period_by_timestamp('2021-10-24 01') == 'P6'
            assert self.tarifa.get_period_by_timestamp('2021-10-24 02') == 'P6'
            assert self.tarifa.get_period_by_timestamp('2021-10-24 03') == 'P6'
            assert self.tarifa.get_period_by_timestamp('2021-10-24 04') == 'P6'
            assert self.tarifa.get_period_by_timestamp('2021-10-24 05') == 'P6'
            assert self.tarifa.get_period_by_timestamp('2021-10-24 06') == 'P6'
            assert self.tarifa.get_period_by_timestamp('2021-10-24 07') == 'P6'
            assert self.tarifa.get_period_by_timestamp('2021-10-24 08') == 'P6'
            assert self.tarifa.get_period_by_timestamp('2021-10-24 09') == 'P6'
            assert self.tarifa.get_period_by_timestamp('2021-10-24 10') == 'P6'
            assert self.tarifa.get_period_by_timestamp('2021-10-24 11') == 'P6'
            assert self.tarifa.get_period_by_timestamp('2021-10-24 12') == 'P6'
            assert self.tarifa.get_period_by_timestamp('2021-10-24 13') == 'P6'
            assert self.tarifa.get_period_by_timestamp('2021-10-24 14') == 'P6'
            assert self.tarifa.get_period_by_timestamp('2021-10-24 15') == 'P6'
            assert self.tarifa.get_period_by_timestamp('2021-10-24 16') == 'P6'
            assert self.tarifa.get_period_by_timestamp('2021-10-24 17') == 'P6'
            assert self.tarifa.get_period_by_timestamp('2021-10-24 18') == 'P6'
            assert self.tarifa.get_period_by_timestamp('2021-10-24 19') == 'P6'
            assert self.tarifa.get_period_by_timestamp('2021-10-24 20') == 'P6'
            assert self.tarifa.get_period_by_timestamp('2021-10-24 21') == 'P6'
            assert self.tarifa.get_period_by_timestamp('2021-10-24 22') == 'P6'
            assert self.tarifa.get_period_by_timestamp('2021-10-24 23') == 'P6'
            assert self.tarifa.get_period_by_timestamp('2021-10-24 24') == 'P6'
            assert self.tarifa.get_period_by_timestamp('2021-10-24 25') == 'P6'

        with it('should have correct power period'):
            dia = self.summer_weekend_day
            assert self.tarifa.get_period_by_date(dia, self.holidays, magn='tp').code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=1), self.holidays, magn='tp').code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=2), self.holidays, magn='tp').code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=3), self.holidays, magn='tp').code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=4), self.holidays, magn='tp').code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=5), self.holidays, magn='tp').code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=6), self.holidays, magn='tp').code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=7), self.holidays, magn='tp').code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=8), self.holidays, magn='tp').code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=9), self.holidays, magn='tp').code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=10), self.holidays, magn='tp').code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=11), self.holidays, magn='tp').code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=12), self.holidays, magn='tp').code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=13), self.holidays, magn='tp').code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=14), self.holidays, magn='tp').code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=15), self.holidays, magn='tp').code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=16), self.holidays, magn='tp').code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=17), self.holidays, magn='tp').code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=18), self.holidays, magn='tp').code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=19), self.holidays, magn='tp').code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=20), self.holidays, magn='tp').code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=21), self.holidays, magn='tp').code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=22), self.holidays, magn='tp').code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=23), self.holidays, magn='tp').code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=23, minutes=59), self.holidays,
                                                  magn='tp').code == 'P6'

    with context("6.1TD"):
        with before.all:
            self.tarifa = T61TD()

        with it('should have code 6.1TD'):
            assert self.tarifa.code == '6.1TD'

        with it('should have correct power margins and type'):
            assert self.tarifa.type == 'AT'
            assert self.tarifa.min_power == 0
            assert self.tarifa.max_power == 100000

        with it('should have correct energy and power periods'):
            assert len(self.tarifa.energy_periods) == 6
            assert len(self.tarifa.power_periods) == 6
            assert self.tarifa.get_number_of_periods() == 6
            assert not self.tarifa.has_holidays_periods

        with it('with losses have a trafo kva and losses_coeff'):
            kwargs = {'kva': 50}
            self.tarifa = T61TD(**kwargs)
            assert self.tarifa.losses == 0.04
            assert self.tarifa.kva == 50
            assert self.tarifa.low_voltage_measure

    # Tariff 6.2TD
    with context("6.2TD"):
        with before.all:
            self.tarifa = T62TD()

        with it('should have code 6.2TD'):
            assert self.tarifa.code == '6.2TD'

        with it('should have correct power margins and type'):
            assert self.tarifa.type == 'AT'
            assert self.tarifa.min_power == 0
            assert self.tarifa.max_power == 100000

        with it('should have correct energy and power periods'):
            assert len(self.tarifa.energy_periods) == 6
            assert len(self.tarifa.power_periods) == 6
            assert self.tarifa.get_number_of_periods() == 6
            assert not self.tarifa.has_holidays_periods

    # Tariff 6.3TD
    with context("6.3TD"):
        with before.all:
            self.tarifa = T63TD()

        with it('should have code 6.3TD'):
            assert self.tarifa.code == '6.3TD'

        with it('should have correct power margins and type'):
            assert self.tarifa.type == 'AT'
            assert self.tarifa.min_power == 0
            assert self.tarifa.max_power == 100000

        with it('should have correct energy and power periods'):
            assert len(self.tarifa.energy_periods) == 6
            assert len(self.tarifa.power_periods) == 6
            assert self.tarifa.get_number_of_periods() == 6
            assert not self.tarifa.has_holidays_periods

        # Tariff 6.4TD
        with context("6.4TD"):
            with before.all:
                self.tarifa = T64TD()

            with it('should have code 6.4TD'):
                assert self.tarifa.code == '6.4TD'

            with it('should have correct power margins and type'):
                assert self.tarifa.type == 'AT'
                assert self.tarifa.min_power == 0
                assert self.tarifa.max_power == 100000

            with it('should have correct energy and power periods'):
                assert len(self.tarifa.energy_periods) == 6
                assert len(self.tarifa.power_periods) == 6
                assert self.tarifa.get_number_of_periods() == 6
                assert not self.tarifa.has_holidays_periods

        with context("3.0TDVE"):
            with before.all:
                self.tarifa = T30TDVE()

            with it('should have code 3.0TDVE'):
                assert self.tarifa.code == '3.0TDVE'

            with it('should have correct power margins and type'):
                assert self.tarifa.type == 'BT'
                assert self.tarifa.min_power == 15
                assert self.tarifa.max_power == 100000

            with it('should have correct energy and power periods'):
                assert len(self.tarifa.energy_periods) == 6
                assert len(self.tarifa.power_periods) == 6
                assert self.tarifa.get_number_of_periods() == 6
                assert not self.tarifa.has_holidays_periods

            with it('should have correct energy period on holiday winter data'):
                dia = self.winter_holiday_day
                assert self.tarifa.get_period_by_date(dia, self.holidays).code == 'P6'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=1), self.holidays).code == 'P6'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=2), self.holidays).code == 'P6'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=3), self.holidays).code == 'P6'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=4), self.holidays).code == 'P6'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=5), self.holidays).code == 'P6'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=6), self.holidays).code == 'P6'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=7), self.holidays).code == 'P6'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=8), self.holidays).code == 'P6'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=9), self.holidays).code == 'P6'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=10), self.holidays).code == 'P6'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=11), self.holidays).code == 'P6'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=12), self.holidays).code == 'P6'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=13), self.holidays).code == 'P6'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=14), self.holidays).code == 'P6'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=15), self.holidays).code == 'P6'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=16), self.holidays).code == 'P6'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=17), self.holidays).code == 'P6'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=18), self.holidays).code == 'P6'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=19), self.holidays).code == 'P6'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=20), self.holidays).code == 'P6'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=21), self.holidays).code == 'P6'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=22), self.holidays).code == 'P6'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=23), self.holidays).code == 'P6'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=23, minutes=59), self.holidays).code == 'P6'

            with it('should have correct energy period on holiday summer data'):
                dia = self.summer_holiday_day
                assert self.tarifa.get_period_by_date(dia, self.holidays).code == 'P6'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=1), self.holidays).code == 'P6'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=2), self.holidays).code == 'P6'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=3), self.holidays).code == 'P6'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=4), self.holidays).code == 'P6'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=5), self.holidays).code == 'P6'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=6), self.holidays).code == 'P6'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=7), self.holidays).code == 'P6'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=8), self.holidays).code == 'P6'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=9), self.holidays).code == 'P6'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=10), self.holidays).code == 'P6'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=11), self.holidays).code == 'P6'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=12), self.holidays).code == 'P6'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=13), self.holidays).code == 'P6'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=14), self.holidays).code == 'P6'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=15), self.holidays).code == 'P6'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=16), self.holidays).code == 'P6'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=17), self.holidays).code == 'P6'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=18), self.holidays).code == 'P6'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=19), self.holidays).code == 'P6'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=20), self.holidays).code == 'P6'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=21), self.holidays).code == 'P6'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=22), self.holidays).code == 'P6'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=23), self.holidays).code == 'P6'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=23, minutes=59), self.holidays).code == 'P6'

            with it('should have correct energy period on laboral winter data'):
                dia = self.winter_laboral_day
                assert self.tarifa.get_period_by_date(dia, self.holidays).code == 'P6'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=1), self.holidays).code == 'P6'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=2), self.holidays).code == 'P6'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=3), self.holidays).code == 'P6'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=4), self.holidays).code == 'P6'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=5), self.holidays).code == 'P6'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=6), self.holidays).code == 'P6'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=7), self.holidays).code == 'P6'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=8), self.holidays).code == 'P3'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=9), self.holidays).code == 'P2'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=10), self.holidays).code == 'P2'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=11), self.holidays).code == 'P2'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=12), self.holidays).code == 'P2'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=13), self.holidays).code == 'P2'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=14), self.holidays).code == 'P3'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=15), self.holidays).code == 'P3'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=16), self.holidays).code == 'P3'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=17), self.holidays).code == 'P3'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=18), self.holidays).code == 'P2'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=19), self.holidays).code == 'P2'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=20), self.holidays).code == 'P2'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=21), self.holidays).code == 'P2'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=22), self.holidays).code == 'P3'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=23), self.holidays).code == 'P3'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=23, minutes=59), self.holidays).code == 'P3'

            with it('should have correct energy period on laboral summer data'):
                dia = self.summer_laboral_day
                assert self.tarifa.get_period_by_date(dia, self.holidays).code == 'P6'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=1), self.holidays).code == 'P6'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=2), self.holidays).code == 'P6'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=3), self.holidays).code == 'P6'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=4), self.holidays).code == 'P6'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=5), self.holidays).code == 'P6'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=6), self.holidays).code == 'P6'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=7), self.holidays).code == 'P6'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=8), self.holidays).code == 'P2'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=9), self.holidays).code == 'P1'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=10), self.holidays).code == 'P1'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=11), self.holidays).code == 'P1'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=12), self.holidays).code == 'P1'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=13), self.holidays).code == 'P1'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=14), self.holidays).code == 'P2'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=15), self.holidays).code == 'P2'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=16), self.holidays).code == 'P2'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=17), self.holidays).code == 'P2'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=18), self.holidays).code == 'P1'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=19), self.holidays).code == 'P1'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=20), self.holidays).code == 'P1'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=21), self.holidays).code == 'P1'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=22), self.holidays).code == 'P2'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=23), self.holidays).code == 'P2'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=23, minutes=59), self.holidays).code == 'P2'

            with it('should have correct energy period on weekend winter data'):
                dia = self.winter_weekend_day
                assert self.tarifa.get_period_by_date(dia, self.holidays).code == 'P6'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=1), self.holidays).code == 'P6'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=2), self.holidays).code == 'P6'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=3), self.holidays).code == 'P6'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=4), self.holidays).code == 'P6'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=5), self.holidays).code == 'P6'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=6), self.holidays).code == 'P6'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=7), self.holidays).code == 'P6'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=8), self.holidays).code == 'P6'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=9), self.holidays).code == 'P6'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=10), self.holidays).code == 'P6'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=11), self.holidays).code == 'P6'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=12), self.holidays).code == 'P6'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=13), self.holidays).code == 'P6'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=14), self.holidays).code == 'P6'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=15), self.holidays).code == 'P6'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=16), self.holidays).code == 'P6'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=17), self.holidays).code == 'P6'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=18), self.holidays).code == 'P6'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=19), self.holidays).code == 'P6'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=20), self.holidays).code == 'P6'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=21), self.holidays).code == 'P6'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=22), self.holidays).code == 'P6'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=23), self.holidays).code == 'P6'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=23, minutes=59), self.holidays).code == 'P6'

            with it('should have correct energy period on weekend summer data'):
                dia = self.summer_weekend_day
                assert self.tarifa.get_period_by_date(dia, self.holidays).code == 'P6'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=1), self.holidays).code == 'P6'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=2), self.holidays).code == 'P6'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=3), self.holidays).code == 'P6'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=4), self.holidays).code == 'P6'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=5), self.holidays).code == 'P6'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=6), self.holidays).code == 'P6'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=7), self.holidays).code == 'P6'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=8), self.holidays).code == 'P6'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=9), self.holidays).code == 'P6'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=10), self.holidays).code == 'P6'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=11), self.holidays).code == 'P6'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=12), self.holidays).code == 'P6'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=13), self.holidays).code == 'P6'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=14), self.holidays).code == 'P6'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=15), self.holidays).code == 'P6'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=16), self.holidays).code == 'P6'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=17), self.holidays).code == 'P6'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=18), self.holidays).code == 'P6'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=19), self.holidays).code == 'P6'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=20), self.holidays).code == 'P6'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=21), self.holidays).code == 'P6'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=22), self.holidays).code == 'P6'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=23), self.holidays).code == 'P6'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=23, minutes=59), self.holidays).code == 'P6'

            with it('must have the correct energy period on time change days'):
                assert self.tarifa.get_period_by_timestamp('2021-03-28 01') == 'P6'
                assert self.tarifa.get_period_by_timestamp('2021-03-28 02') == 'P6'
                assert self.tarifa.get_period_by_timestamp('2021-03-28 03') == 'P6'
                assert self.tarifa.get_period_by_timestamp('2021-03-28 04') == 'P6'
                assert self.tarifa.get_period_by_timestamp('2021-03-28 05') == 'P6'
                assert self.tarifa.get_period_by_timestamp('2021-03-28 06') == 'P6'
                assert self.tarifa.get_period_by_timestamp('2021-03-28 07') == 'P6'
                assert self.tarifa.get_period_by_timestamp('2021-03-28 08') == 'P6'
                assert self.tarifa.get_period_by_timestamp('2021-03-28 09') == 'P6'
                assert self.tarifa.get_period_by_timestamp('2021-03-28 10') == 'P6'
                assert self.tarifa.get_period_by_timestamp('2021-03-28 11') == 'P6'
                assert self.tarifa.get_period_by_timestamp('2021-03-28 12') == 'P6'
                assert self.tarifa.get_period_by_timestamp('2021-03-28 13') == 'P6'
                assert self.tarifa.get_period_by_timestamp('2021-03-28 14') == 'P6'
                assert self.tarifa.get_period_by_timestamp('2021-03-28 15') == 'P6'
                assert self.tarifa.get_period_by_timestamp('2021-03-28 16') == 'P6'
                assert self.tarifa.get_period_by_timestamp('2021-03-28 17') == 'P6'
                assert self.tarifa.get_period_by_timestamp('2021-03-28 18') == 'P6'
                assert self.tarifa.get_period_by_timestamp('2021-03-28 19') == 'P6'
                assert self.tarifa.get_period_by_timestamp('2021-03-28 20') == 'P6'
                assert self.tarifa.get_period_by_timestamp('2021-03-28 21') == 'P6'
                assert self.tarifa.get_period_by_timestamp('2021-03-28 22') == 'P6'
                assert self.tarifa.get_period_by_timestamp('2021-03-28 23') == 'P6'

                assert self.tarifa.get_period_by_timestamp('2021-10-24 01') == 'P6'
                assert self.tarifa.get_period_by_timestamp('2021-10-24 02') == 'P6'
                assert self.tarifa.get_period_by_timestamp('2021-10-24 03') == 'P6'
                assert self.tarifa.get_period_by_timestamp('2021-10-24 04') == 'P6'
                assert self.tarifa.get_period_by_timestamp('2021-10-24 05') == 'P6'
                assert self.tarifa.get_period_by_timestamp('2021-10-24 06') == 'P6'
                assert self.tarifa.get_period_by_timestamp('2021-10-24 07') == 'P6'
                assert self.tarifa.get_period_by_timestamp('2021-10-24 08') == 'P6'
                assert self.tarifa.get_period_by_timestamp('2021-10-24 09') == 'P6'
                assert self.tarifa.get_period_by_timestamp('2021-10-24 10') == 'P6'
                assert self.tarifa.get_period_by_timestamp('2021-10-24 11') == 'P6'
                assert self.tarifa.get_period_by_timestamp('2021-10-24 12') == 'P6'
                assert self.tarifa.get_period_by_timestamp('2021-10-24 13') == 'P6'
                assert self.tarifa.get_period_by_timestamp('2021-10-24 14') == 'P6'
                assert self.tarifa.get_period_by_timestamp('2021-10-24 15') == 'P6'
                assert self.tarifa.get_period_by_timestamp('2021-10-24 16') == 'P6'
                assert self.tarifa.get_period_by_timestamp('2021-10-24 17') == 'P6'
                assert self.tarifa.get_period_by_timestamp('2021-10-24 18') == 'P6'
                assert self.tarifa.get_period_by_timestamp('2021-10-24 19') == 'P6'
                assert self.tarifa.get_period_by_timestamp('2021-10-24 20') == 'P6'
                assert self.tarifa.get_period_by_timestamp('2021-10-24 21') == 'P6'
                assert self.tarifa.get_period_by_timestamp('2021-10-24 22') == 'P6'
                assert self.tarifa.get_period_by_timestamp('2021-10-24 23') == 'P6'
                assert self.tarifa.get_period_by_timestamp('2021-10-24 24') == 'P6'
                assert self.tarifa.get_period_by_timestamp('2021-10-24 25') == 'P6'

            with it('should have correct power period'):
                dia = self.summer_weekend_day
                assert self.tarifa.get_period_by_date(dia, self.holidays, magn='tp').code == 'P6'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=1), self.holidays, magn='tp').code == 'P6'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=2), self.holidays, magn='tp').code == 'P6'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=3), self.holidays, magn='tp').code == 'P6'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=4), self.holidays, magn='tp').code == 'P6'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=5), self.holidays, magn='tp').code == 'P6'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=6), self.holidays, magn='tp').code == 'P6'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=7), self.holidays, magn='tp').code == 'P6'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=8), self.holidays, magn='tp').code == 'P6'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=9), self.holidays, magn='tp').code == 'P6'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=10), self.holidays, magn='tp').code == 'P6'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=11), self.holidays, magn='tp').code == 'P6'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=12), self.holidays, magn='tp').code == 'P6'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=13), self.holidays, magn='tp').code == 'P6'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=14), self.holidays, magn='tp').code == 'P6'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=15), self.holidays, magn='tp').code == 'P6'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=16), self.holidays, magn='tp').code == 'P6'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=17), self.holidays, magn='tp').code == 'P6'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=18), self.holidays, magn='tp').code == 'P6'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=19), self.holidays, magn='tp').code == 'P6'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=20), self.holidays, magn='tp').code == 'P6'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=21), self.holidays, magn='tp').code == 'P6'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=22), self.holidays, magn='tp').code == 'P6'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=23), self.holidays, magn='tp').code == 'P6'
                assert self.tarifa.get_period_by_date(dia + timedelta(hours=23, minutes=59), self.holidays,
                                                      magn='tp').code == 'P6'

        with context("6.1TDVE"):
            with before.all:
                self.tarifa = T61TDVE()

            with it('should have code 6.1TDVE'):
                assert self.tarifa.code == '6.1TDVE'

            with it('should have correct power margins and type'):
                assert self.tarifa.type == 'AT'
                assert self.tarifa.min_power == 0
                assert self.tarifa.max_power == 100000

            with it('should have correct energy and power periods'):
                assert len(self.tarifa.energy_periods) == 6
                assert len(self.tarifa.power_periods) == 6
                assert self.tarifa.get_number_of_periods() == 6
                assert not self.tarifa.has_holidays_periods

    with context("Energy and Power periods depend on day type on geom zone 2"):
        with before.all:
            self.tarifa = T30TD(geom_zone='2')

        with it('should have correct geom zone'):
            assert self.tarifa.geom_zone == '2'  # Balearic Islands

        # demo days used
        # (2021-06-04)  # "A" in zone 2.
        # (2022-05-04)  # "MA" in zone 2.
        # (2022-01-19)  # "M" in zones 2.
        # (2022-03-15)  # "B" in zones 2.

        with it('should have correct energy period on "A" day type'):
            dia = self.june_day
            assert self.tarifa.get_period_by_date(dia, self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=1), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=2), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=3), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=4), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=5), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=6), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=7), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=8), self.holidays).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=9), self.holidays).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=10), self.holidays).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=11), self.holidays).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=12), self.holidays).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=13), self.holidays).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=14), self.holidays).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=15), self.holidays).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=16), self.holidays).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=17), self.holidays).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=18), self.holidays).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=19), self.holidays).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=20), self.holidays).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=21), self.holidays).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=22), self.holidays).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=23), self.holidays).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=23, minutes=59), self.holidays).code == 'P2'

        with it('should have correct energy period on "B" day type'):
            dia = self.may_day
            assert self.tarifa.get_period_by_date(dia, self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=1), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=2), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=3), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=4), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=5), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=6), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=7), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=8), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=9), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=10), self.holidays).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=11), self.holidays).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=12), self.holidays).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=13), self.holidays).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=14), self.holidays).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=15), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=16), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=17), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=18), self.holidays).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=19), self.holidays).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=20), self.holidays).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=21), self.holidays).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=22), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=23), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=23, minutes=59), self.holidays).code == 'P3'

        with it('should have correct energy period on "B1" day type'):
            dia = self.january_day
            assert self.tarifa.get_period_by_date(dia, self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=1), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=2), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=3), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=4), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=5), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=6), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=7), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=8), self.holidays).code == 'P4'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=9), self.holidays).code == 'P4'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=10), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=11), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=12), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=13), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=14), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=15), self.holidays).code == 'P4'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=16), self.holidays).code == 'P4'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=17), self.holidays).code == 'P4'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=18), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=19), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=20), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=21), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=22), self.holidays).code == 'P4'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=23), self.holidays).code == 'P4'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=23, minutes=59), self.holidays).code == 'P4'

        with it('should have correct energy period on "C" day type'):
            dia = self.march_day
            assert self.tarifa.get_period_by_date(dia, self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=1), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=2), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=3), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=4), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=5), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=6), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=7), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=8), self.holidays).code == 'P5'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=9), self.holidays).code == 'P5'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=10), self.holidays).code == 'P4'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=11), self.holidays).code == 'P4'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=12), self.holidays).code == 'P4'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=13), self.holidays).code == 'P4'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=14), self.holidays).code == 'P4'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=15), self.holidays).code == 'P5'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=16), self.holidays).code == 'P5'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=17), self.holidays).code == 'P5'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=18), self.holidays).code == 'P4'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=19), self.holidays).code == 'P4'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=20), self.holidays).code == 'P4'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=21), self.holidays).code == 'P4'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=22), self.holidays).code == 'P5'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=23), self.holidays).code == 'P5'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=23, minutes=59), self.holidays).code == 'P5'

        with it('should have correct energy period on "D" day type'):
            dia = self.winter_weekend_day
            assert self.tarifa.get_period_by_date(dia, self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=1), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=2), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=3), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=4), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=5), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=6), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=7), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=8), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=9), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=10), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=11), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=12), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=13), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=14), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=15), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=16), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=17), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=18), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=19), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=20), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=21), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=22), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=23), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=23, minutes=59), self.holidays).code == 'P6'

    with context("Energy and Power periods depend on day type on geom zone 3 (Canary Islands)"):
        with before.all:
            self.tarifa = T30TD(geom_zone='3')

        with it('should have correct geom zone'):
            assert self.tarifa.geom_zone == '3'  # Canary Islands

        # demo days used
        # (2021-08-16)  # "A" in zone 3.
        # (2021-11-12)  # "MA" in zone 3.
        # (2022-01-19)  # "M" in zones 3.
        # (2022-04-13)  # "B" in zones 3.

        with it('should have correct energy period on "A" day type'):
            dia = self.august_day
            assert self.tarifa.get_period_by_date(dia, self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=1), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=2), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=3), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=4), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=5), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=6), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=7), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=8), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=9), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=10), self.holidays).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=11), self.holidays).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=12), self.holidays).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=13), self.holidays).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=14), self.holidays).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=15), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=16), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=17), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=18), self.holidays).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=19), self.holidays).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=20), self.holidays).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=21), self.holidays).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=22), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=23), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=23, minutes=59), self.holidays).code == 'P3'

        with it('should have correct energy period on "B" day type'):
            dia = self.winter_laboral_day
            assert self.tarifa.get_period_by_date(dia, self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=1), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=2), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=3), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=4), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=5), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=6), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=7), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=8), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=9), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=10), self.holidays).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=11), self.holidays).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=12), self.holidays).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=13), self.holidays).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=14), self.holidays).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=15), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=16), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=17), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=18), self.holidays).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=19), self.holidays).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=20), self.holidays).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=21), self.holidays).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=22), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=23), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=23, minutes=59), self.holidays).code == 'P3'

        with it('should have correct energy period on "B1" day type'):
            dia = self.january_day
            assert self.tarifa.get_period_by_date(dia, self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=1), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=2), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=3), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=4), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=5), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=6), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=7), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=8), self.holidays).code == 'P4'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=9), self.holidays).code == 'P4'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=10), self.holidays).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=11), self.holidays).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=12), self.holidays).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=13), self.holidays).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=14), self.holidays).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=15), self.holidays).code == 'P4'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=16), self.holidays).code == 'P4'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=17), self.holidays).code == 'P4'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=18), self.holidays).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=19), self.holidays).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=20), self.holidays).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=21), self.holidays).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=22), self.holidays).code == 'P4'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=23), self.holidays).code == 'P4'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=23, minutes=59), self.holidays).code == 'P4'

        with it('should have correct energy period on "C" day type'):
            dia = self.april_day
            assert self.tarifa.get_period_by_date(dia, self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=1), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=2), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=3), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=4), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=5), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=6), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=7), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=8), self.holidays).code == 'P5'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=9), self.holidays).code == 'P5'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=10), self.holidays).code == 'P4'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=11), self.holidays).code == 'P4'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=12), self.holidays).code == 'P4'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=13), self.holidays).code == 'P4'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=14), self.holidays).code == 'P4'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=15), self.holidays).code == 'P5'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=16), self.holidays).code == 'P5'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=17), self.holidays).code == 'P5'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=18), self.holidays).code == 'P4'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=19), self.holidays).code == 'P4'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=20), self.holidays).code == 'P4'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=21), self.holidays).code == 'P4'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=22), self.holidays).code == 'P5'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=23), self.holidays).code == 'P5'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=23, minutes=59), self.holidays).code == 'P5'

        with it('should have correct energy period on "D" day type'):
            dia = self.winter_weekend_day
            assert self.tarifa.get_period_by_date(dia, self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=1), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=2), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=3), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=4), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=5), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=6), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=7), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=8), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=9), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=10), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=11), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=12), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=13), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=14), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=15), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=16), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=17), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=18), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=19), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=20), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=21), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=22), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=23), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=23, minutes=59), self.holidays).code == 'P6'

    with context("Energy and Power periods depend on day type on geom zone 4 (Ceuta)"):
        with before.all:
            self.tarifa = T30TD(geom_zone='4')

        with it('should have correct geom zone'):
            assert self.tarifa.geom_zone == '4'  # Ceuta

        # demo days used
        # (2021-08-16)  # "A" in zone 4.
        # (2021-07-16)  # "MA" in zone 4.
        # (2022-03-15)  # "M" in zones 4.
        # (2022-04-13)  # "B" in zones 4.

        with it('should have correct energy period on "A" day type'):
            dia = self.august_day
            assert self.tarifa.get_period_by_date(dia, self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=1), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=2), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=3), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=4), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=5), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=6), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=7), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=8), self.holidays).code == 'P4'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=9), self.holidays).code == 'P4'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=10), self.holidays).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=11), self.holidays).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=12), self.holidays).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=13), self.holidays).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=14), self.holidays).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=15), self.holidays).code == 'P4'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=16), self.holidays).code == 'P4'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=17), self.holidays).code == 'P4'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=18), self.holidays).code == 'P4'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=19), self.holidays).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=20), self.holidays).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=21), self.holidays).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=22), self.holidays).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=23), self.holidays).code == 'P4'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=23, minutes=59), self.holidays).code == 'P4'

        with it('should have correct energy period on "B" day type'):
            dia = self.summer_laboral_day
            assert self.tarifa.get_period_by_date(dia, self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=1), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=2), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=3), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=4), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=5), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=6), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=7), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=8), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=9), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=10), self.holidays).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=11), self.holidays).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=12), self.holidays).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=13), self.holidays).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=14), self.holidays).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=15), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=16), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=17), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=18), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=19), self.holidays).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=20), self.holidays).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=21), self.holidays).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=22), self.holidays).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=23), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=23, minutes=59), self.holidays).code == 'P3'

        with it('should have correct energy period on "B1" day type'):
            dia = self.march_day
            assert self.tarifa.get_period_by_date(dia, self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=1), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=2), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=3), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=4), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=5), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=6), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=7), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=8), self.holidays).code == 'P4'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=9), self.holidays).code == 'P4'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=10), self.holidays).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=11), self.holidays).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=12), self.holidays).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=13), self.holidays).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=14), self.holidays).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=15), self.holidays).code == 'P4'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=16), self.holidays).code == 'P4'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=17), self.holidays).code == 'P4'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=18), self.holidays).code == 'P4'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=19), self.holidays).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=20), self.holidays).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=21), self.holidays).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=22), self.holidays).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=23), self.holidays).code == 'P4'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=23, minutes=59), self.holidays).code == 'P4'

        with it('should have correct energy period on "C" day type'):
            dia = self.april_day
            assert self.tarifa.get_period_by_date(dia, self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=1), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=2), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=3), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=4), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=5), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=6), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=7), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=8), self.holidays).code == 'P5'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=9), self.holidays).code == 'P5'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=10), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=11), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=12), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=13), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=14), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=15), self.holidays).code == 'P5'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=16), self.holidays).code == 'P5'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=17), self.holidays).code == 'P5'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=18), self.holidays).code == 'P5'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=19), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=20), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=21), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=22), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=23), self.holidays).code == 'P5'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=23, minutes=59), self.holidays).code == 'P5'

        with it('should have correct energy period on "D" day type'):
            dia = self.winter_weekend_day
            assert self.tarifa.get_period_by_date(dia, self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=1), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=2), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=3), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=4), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=5), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=6), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=7), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=8), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=9), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=10), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=11), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=12), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=13), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=14), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=15), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=16), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=17), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=18), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=19), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=20), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=21), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=22), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=23), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=23, minutes=59), self.holidays).code == 'P6'

    with context("Energy and Power periods depend on day type on geom zone 5 (Melilla)"):
        with before.all:
            self.tarifa = T30TD(geom_zone='5')

        with it('should have correct geom zone'):
            assert self.tarifa.geom_zone == '5'  # Melilla

        # demo days used
        # (2021-08-16)  # "A" in zone 5.
        # (2021-12-13)  # "MA" in zone 5.
        # (2021-06-04)  # "M" in zones 5.
        # (2022-04-13)  # "B" in zones 5.

        with it('should have correct energy period on "A" day type'):
            dia = self.august_day
            assert self.tarifa.get_period_by_date(dia, self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=1), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=2), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=3), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=4), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=5), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=6), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=7), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=8), self.holidays).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=9), self.holidays).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=10), self.holidays).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=11), self.holidays).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=12), self.holidays).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=13), self.holidays).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=14), self.holidays).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=15), self.holidays).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=16), self.holidays).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=17), self.holidays).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=18), self.holidays).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=19), self.holidays).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=20), self.holidays).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=21), self.holidays).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=22), self.holidays).code == 'P1'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=23), self.holidays).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=23, minutes=59), self.holidays).code == 'P2'

        with it('should have correct energy period on "B" day type'):
            dia = self.december_day
            assert self.tarifa.get_period_by_date(dia, self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=1), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=2), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=3), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=4), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=5), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=6), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=7), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=8), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=9), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=10), self.holidays).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=11), self.holidays).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=12), self.holidays).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=13), self.holidays).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=14), self.holidays).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=15), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=16), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=17), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=18), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=19), self.holidays).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=20), self.holidays).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=21), self.holidays).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=22), self.holidays).code == 'P2'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=23), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=23, minutes=59), self.holidays).code == 'P3'

        with it('should have correct energy period on "B1" day type'):
            dia = self.june_day
            assert self.tarifa.get_period_by_date(dia, self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=1), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=2), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=3), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=4), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=5), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=6), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=7), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=8), self.holidays).code == 'P4'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=9), self.holidays).code == 'P4'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=10), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=11), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=12), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=13), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=14), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=15), self.holidays).code == 'P4'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=16), self.holidays).code == 'P4'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=17), self.holidays).code == 'P4'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=18), self.holidays).code == 'P4'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=19), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=20), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=21), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=22), self.holidays).code == 'P3'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=23), self.holidays).code == 'P4'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=23, minutes=59), self.holidays).code == 'P4'

        with it('should have correct energy period on "C" day type'):
            dia = self.april_day
            assert self.tarifa.get_period_by_date(dia, self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=1), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=2), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=3), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=4), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=5), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=6), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=7), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=8), self.holidays).code == 'P5'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=9), self.holidays).code == 'P5'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=10), self.holidays).code == 'P4'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=11), self.holidays).code == 'P4'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=12), self.holidays).code == 'P4'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=13), self.holidays).code == 'P4'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=14), self.holidays).code == 'P4'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=15), self.holidays).code == 'P5'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=16), self.holidays).code == 'P5'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=17), self.holidays).code == 'P5'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=18), self.holidays).code == 'P5'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=19), self.holidays).code == 'P4'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=20), self.holidays).code == 'P4'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=21), self.holidays).code == 'P4'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=22), self.holidays).code == 'P4'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=23), self.holidays).code == 'P5'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=23, minutes=59), self.holidays).code == 'P5'

        with it('should have correct energy period on "D" day type'):
            dia = self.winter_weekend_day
            assert self.tarifa.get_period_by_date(dia, self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=1), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=2), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=3), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=4), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=5), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=6), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=7), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=8), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=9), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=10), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=11), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=12), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=13), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=14), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=15), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=16), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=17), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=18), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=19), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=20), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=21), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=22), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=23), self.holidays).code == 'P6'
            assert self.tarifa.get_period_by_date(dia + timedelta(hours=23, minutes=59), self.holidays).code == 'P6'
