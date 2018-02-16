from expects.testing import failure
from expects import *
from enerdata.contracts.tariff import *
from datetime import datetime, timedelta
from enerdata.datetime.timezone import TIMEZONE


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
        expect(lambda: tari_T20A.evaluate_powers([5])).to(
            raise_error(NotNormalizedPower))
        assert tari_T20A.evaluate_powers([5.5])
        expect(lambda: tari_T20A.evaluate_powers([5, 7])).to(
            raise_error(IncorrectPowerNumber, 'Expected 1 power(s) and got 2'))
        expect(lambda: tari_T20A.evaluate_powers([100])).to(
            raise_error(IncorrectMaxPower))

        tari_T30A = T30A()
        expect(lambda: tari_T30A.evaluate_powers([-10, -5, 0])).to(
            raise_error(NotPositivePower))
        expect(lambda: tari_T30A.evaluate_powers([10, 13, 15])).to(
            raise_error(IncorrectMaxPower))
        expect(lambda: tari_T30A.evaluate_powers([10, 13, 16])).to(
            raise_error(NotNormalizedPower))
        assert tari_T30A.evaluate_powers([2.304, 2.304, 16.454])
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

        self.winter_holiday_day = TIMEZONE.localize(datetime(2014, 1, 6))
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


    with context('3.1A'):
        with before.all:
            self.tarifa = T31A()
        with it('should have code 3.1A'):
            assert self.tarifa.code == '3.1A'


        with it('should have correct period on weekend winter data'):
            dia = self.winter_weekend_day
            assert self.tarifa.get_period_by_date(dia).code == 'P5'
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
            assert self.tarifa.get_period_by_date(dia).code == 'P5'
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
