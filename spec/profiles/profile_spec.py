from enerdata.profiles.profile import *
from enerdata.contracts.tariff import (T20A, T20DHA, T20DHS, T21A, T21DHA,
                                       T21DHS, T30A, T31A, T30A_one_period,
                                       T31A_one_period, TRE)
from enerdata.datetime.holidays import get_holidays
from enerdata.metering.measure import *
from expects import *
import vcr
import random



with description("A coeficient"):
    with before.all:
        start = TIMEZONE.localize(datetime(2014, 1, 1))
        end = TIMEZONE.localize(datetime(2015, 1, 1))
        cofs = []
        day = start
        while day < end:
            day += timedelta(hours=1)
            cofs.append(Coefficent(TIMEZONE.normalize(day), {'A': 0, 'B': 0}))
        self.cofs = cofs

    with it("must read and sum the hours of the file"):
        # TODO: Move this test to integration test with REE
        with vcr.use_cassette('spec/fixtures/ree/201410.yaml'):
            cofs = REEProfile.get(2014, 10)
            # We have one hour more in October
            assert len(cofs) == (31 * 24) + 1
            # The first second hour in the 26th of October is DST
            assert cofs[(24 * 25) + 1][0].dst() == timedelta(seconds=3600)
            # The second second hour in the 26th of October is not DST
            assert cofs[(24 * 25) + 2][0].dst() == timedelta(0)
            assert REEProfile._CACHE['201410'] == cofs

    with it("must fail if the position does not exist"):
        c = Coefficients(self.cofs)
        def get_range_error():
            c.get_range(date(2015, 1, 1), date(2015, 2, 1))

        expect(get_range_error).to(raise_error(ValueError, 'start date not found in coefficients'))


    with it("must return the sum of coefs for each period"):
        c = Coefficients(self.cofs)
        t = T20DHA()
        t.cof = 'A'
        assert c.get_coefs_by_tariff(t, date(2014, 1, 1), date(2014, 1, 31)) == {'P1': 0, 'P2': 0}


    with it('should insert coeficients if empty'):
        c = Coefficients()
        assert len(c.coefs) == 0
        c.insert_coefs(self.cofs)
        assert len(c.coefs) == (365 * 24)

    with it('should replace the coeficients'):
        c = Coefficients(self.cofs)
        assert len(c.coefs) == (365 * 24)
        c.insert_coefs(self.cofs)
        assert len(c.coefs) == (365 * 24)

    with it('should append the coefficients'):
        c = Coefficients()
        c.insert_coefs(self.cofs)
        start = TIMEZONE.localize(datetime(2015, 1, 1))
        end = TIMEZONE.localize(datetime(2015, 2, 1))
        cofs = []
        day = start
        while day < end:
            cofs.append((TIMEZONE.normalize(day + timedelta(hours=1)), {'A': 0, 'B': 0}))
            day += timedelta(hours=1)
        c.insert_coefs(cofs)
        assert c.coefs[0][0] == TIMEZONE.localize(datetime(2014, 1, 1, 1))
        assert c.coefs[-1][0] == TIMEZONE.localize(datetime(2015, 2, 1))
        assert len(c.coefs) == ((365 * 24) + (31 * 24))

    with it('should return the range of dates'):
        c = Coefficients(self.cofs)
        cofs = c.get_range(date(2014, 10, 26), date(2014, 10, 26))
        assert len(cofs) == 25
        assert cofs[1][0] == TIMEZONE.localize(datetime(2014, 10, 26, 2), is_dst=True)
        assert cofs[2][0] == TIMEZONE.localize(datetime(2014, 10, 26, 2), is_dst=False)

        cofs = c.get_range(date(2014, 3, 30), date(2014, 3, 30))
        assert len(cofs) == 23
        assert cofs[1][0] == TIMEZONE.normalize(TIMEZONE.localize(datetime(2014, 3, 30, 2)))

    with it('should return a coefficent hour'):
        c = Coefficients(self.cofs)
        dt = TIMEZONE.localize(datetime(2014, 12, 23, 0))
        cof = Coefficent(dt, {'A': 0.001, 'B': 0.001})
        c.insert_coefs((cof, ))
        dt = datetime(2014, 12, 23, 0)
        assert c.get(dt) is cof


with description("When profiling"):
    with before.all:
        measures = []
        start = TIMEZONE.localize(datetime(2015, 3, 1, 1))
        end = TIMEZONE.localize(datetime(2015, 4, 1, 0))
        start_idx = start
        while start_idx <= end:
            measures.append(ProfileHour(
                TIMEZONE.normalize(start_idx), random.randint(0, 10), True, 0.0
            ))
            start_idx += timedelta(hours=1)
        self.profile = Profile(start, end, measures)
        self.start_date = start
        self.end_date = end

    with it('the total energy must be the sum of the profiled energy'):
        c = Coefficients(REEProfile.get(2014, 10))
        profiler = Profiler(c)
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
                date(2014, 10, 31),
                TariffPeriod('P1', 'te'), 540, consumption=233
            ),
            EnergyMeasure(
                date(2014, 10, 31),
                TariffPeriod('P2', 'te'), 150, consumption=42
            )
        ]
        t = T20DHA()
        t.cof = 'A'
        prof = list(profiler.profile(t, measures))
        assert len(prof) == (31 * 24) + 1
        consum = sum([i[1]['aprox'] for i in prof])
        assert consum == 233 + 42

        c = Coefficients(REEProfile.get(2016, 4))
        profiler = Profiler(c)
        measures = [
            EnergyMeasure(
                date(2016, 4, 1),
                TariffPeriod('P1', 'te'), 135134, consumption=0
            ),
            EnergyMeasure(
                date(2016, 4, 1),
                TariffPeriod('P2', 'te'), 261635, consumption=0
            ),
            EnergyMeasure(
                date(2016, 4, 1),
                TariffPeriod('P3', 'te'), 251742, consumption=0
            ),
            EnergyMeasure(
                date(2016, 4, 30),
                TariffPeriod('P1', 'te'), 138529, consumption=3395
            ),
            EnergyMeasure(
                date(2016, 4, 30),
                TariffPeriod('P2', 'te'), 267881, consumption=6246
            ),
            EnergyMeasure(
                date(2016, 4, 30),
                TariffPeriod('P3', 'te'), 258091, consumption=6349
            ),
        ]
        t = T31A()
        prof = list(profiler.profile(t, measures, drag_method='period'))
        assert len(prof) == (30 * 24)
        consum = sum([i[1]['aprox'] for i in prof])
        group = Counter()
        for p in prof:
            per = t.get_period_by_date(p[0]).code
            group[per] += p[1]['aprox']
        consums = {'P1': 3395, 'P2': 6246, 'P3': 6349}
        for p in consums:
            assert group[p] == consums[p]


    with it('the total energy must be the sum of the profiled energy (more than one measures)'):
        c = Coefficients(REEProfile.get(2014, 10))
        profiler = Profiler(c)
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
        t = T20DHA()
        t.cof = 'A'
        prof = list(profiler.profile(t, measures))
        expect(len(prof)).to(equal((31 * 24) +1))
        consum = sum([i[1]['aprox'] for i in prof])
        expect(consum).to(equal(103 + 22 + 130 + 20))


    with it('should be the same per period if drag per period is used'):
        c = Coefficients()
        with vcr.use_cassette('spec/fixtures/ree/201502.yaml'):
            c.insert_coefs(REEProfile.get(2015, 2))
        with vcr.use_cassette('spec/fixtures/ree/201503.yaml'):
            c.insert_coefs(REEProfile.get(2015, 3))
        profiler = Profiler(c)
        measures = [
            EnergyMeasure(
                date(2015, 2, 17),
                TariffPeriod('P1', 'te'), 0, consumption=0
            ),
            EnergyMeasure(
                date(2015, 2, 17),
                TariffPeriod('P2', 'te'), 0, consumption=0
            ),
            EnergyMeasure(
                date(2015, 2, 17),
                TariffPeriod('P3', 'te'), 0, consumption=0
            ),
            EnergyMeasure(
                date(2015, 2, 17),
                TariffPeriod('P4', 'te'), 0, consumption=0
            ),
            EnergyMeasure(
                date(2015, 2, 17),
                TariffPeriod('P5', 'te'), 0, consumption=0
            ),
            EnergyMeasure(
                date(2015, 2, 17),
                TariffPeriod('P6', 'te'), 0, consumption=0
            ),
            EnergyMeasure(
                date(2015, 3, 18),
                TariffPeriod('P1', 'te'), 0, consumption=282
            ),
            EnergyMeasure(
                date(2015, 3, 18),
                TariffPeriod('P2', 'te'), 0, consumption=156
            ),
            EnergyMeasure(
                date(2015, 3, 18),
                TariffPeriod('P3', 'te'), 0, consumption=325
            ),
            EnergyMeasure(
                date(2015, 3, 18),
                TariffPeriod('P4', 'te'), 0, consumption=56
            ),
            EnergyMeasure(
                date(2015, 3, 18),
                TariffPeriod('P5', 'te'), 0, consumption=643
            ),
            EnergyMeasure(
                date(2015, 3, 18),
                TariffPeriod('P6', 'te'), 0, consumption=32
            )
        ]
        t = T30A()
        t.cof = 'C'
        prof = list(profiler.profile(t, measures, drag_method='period'))
        cons = Counter()
        for p in prof:
            period = p[1]['period']
            cons[period] += p[1]['aprox']

        assert cons['P1'] == 282
        assert cons['P2'] == 156
        assert cons['P3'] == 325
        assert cons['P4'] == 56
        assert cons['P5'] == 643
        assert cons['P6'] == 32

        t = T31A()
        prof = list(profiler.profile(t, measures, drag_method='period'))
        cons = Counter()
        for p in prof:
            period = p[1]['period']
            cons[period] += p[1]['aprox']

        assert cons['P1'] == 282
        assert cons['P2'] == 156
        assert cons['P3'] == 325
        assert cons['P4'] == 0
        assert cons['P5'] == 643
        assert cons['P6'] == 32


    with context('If a period is not in measures'):
        with it('must use 0 as its consumption'):

            c = Coefficients()
            with vcr.use_cassette('spec/fixtures/ree/201502.yaml'):
                c.insert_coefs(REEProfile.get(2015, 2))
            with vcr.use_cassette('spec/fixtures/ree/201503.yaml'):
                c.insert_coefs(REEProfile.get(2015, 3))
            profiler = Profiler(c)
            measures = [
                EnergyMeasure(
                    date(2015, 2, 17),
                    TariffPeriod('P1', 'te'), 0, consumption=0
                ),
                EnergyMeasure(
                    date(2015, 2, 17),
                    TariffPeriod('P2', 'te'), 0, consumption=0
                ),
                EnergyMeasure(
                    date(2015, 2, 17),
                    TariffPeriod('P3', 'te'), 0, consumption=0
                ),
                EnergyMeasure(
                    date(2015, 2, 17),
                    TariffPeriod('P4', 'te'), 0, consumption=0
                ),
                EnergyMeasure(
                    date(2015, 2, 17),
                    TariffPeriod('P5', 'te'), 0, consumption=0
                ),
                EnergyMeasure(
                    date(2015, 2, 17),
                    TariffPeriod('P6', 'te'), 0, consumption=0
                ),
                EnergyMeasure(
                    date(2015, 3, 18),
                    TariffPeriod('P1', 'te'), 0, consumption=282
                ),
                EnergyMeasure(
                    date(2015, 3, 18),
                    TariffPeriod('P2', 'te'), 0, consumption=156
                ),
                EnergyMeasure(
                    date(2015, 3, 18),
                    TariffPeriod('P3', 'te'), 0, consumption=325
                )
            ]
            t = T30A()
            t.cof = 'C'
            prof = list(profiler.profile(t, measures, drag_method='period'))
            cons = Counter()
            for p in prof:
                period = p[1]['period']
                cons[period] += p[1]['aprox']

            assert cons['P1'] == 282
            assert cons['P2'] == 156
            assert cons['P3'] == 325
            assert cons['P4'] == 0
            assert cons['P5'] == 0
            assert cons['P6'] == 0

        with it('must use 0 as its consumption when only 3 periods'):

            c = Coefficients()
            with vcr.use_cassette('spec/fixtures/ree/201502.yaml'):
                c.insert_coefs(REEProfile.get(2015, 2))
            with vcr.use_cassette('spec/fixtures/ree/201503.yaml'):
                c.insert_coefs(REEProfile.get(2015, 3))
            profiler = Profiler(c)
            measures = [
                EnergyMeasure(
                    date(2015, 2, 17),
                    TariffPeriod('P1', 'te'), 0, consumption=0
                ),
                EnergyMeasure(
                    date(2015, 2, 17),
                    TariffPeriod('P2', 'te'), 0, consumption=0
                ),
                EnergyMeasure(
                    date(2015, 2, 17),
                    TariffPeriod('P3', 'te'), 0, consumption=0
                ),
                EnergyMeasure(
                    date(2015, 3, 18),
                    TariffPeriod('P1', 'te'), 0, consumption=282
                ),
                EnergyMeasure(
                    date(2015, 3, 18),
                    TariffPeriod('P2', 'te'), 0, consumption=156
                ),
                EnergyMeasure(
                    date(2015, 3, 18),
                    TariffPeriod('P3', 'te'), 0, consumption=325
                )
            ]
            t = T30A()
            t.cof = 'C'
            prof = list(profiler.profile(t, measures, drag_method='period'))
            cons = Counter()
            for p in prof:
                period = p[1]['period']
                cons[period] += p[1]['aprox']

            assert cons['P1'] == 282
            assert cons['P2'] == 156
            assert cons['P3'] == 325
            assert cons['P4'] == 0
            assert cons['P5'] == 0
            assert cons['P6'] == 0

        with context('And the tariff is RE'):
            with it('zero values for sun coefficient should not cause problems '):
                di = '2019-01-01 01:00:00'
                df = '2019-01-01 02:00:00'
                measures = []
                start = TIMEZONE.localize(datetime.strptime(di, '%Y-%m-%d %H:%M:%S'))
                end = TIMEZONE.localize(datetime.strptime(df, '%Y-%m-%d %H:%M:%S'))
                profile = Profile(start, end, measures)
                profile.profile_class = REProfileZone5
                tariff = TRE()
                climatic_zone = 5
                balance = {
                    'P0': 0
                }
                total_expected = 0
                # This test only checks try/except for ZeroDivisionError works
                estimation = profile.estimate(tariff, balance)
                total_estimated = sum([x.measure for x in estimation.measures])
                assert total_estimated == total_expected

            with it('zero values for sun coefficient should have zero energy value or show a warning'):
                # set dates
                d1 = '2019-01-01 01:00:00'
                d2 = '2019-01-01 02:00:00'
                d3 = '2019-01-01 03:00:00'
                start = TIMEZONE.localize(datetime.strptime(d1, '%Y-%m-%d %H:%M:%S'))
                middle = TIMEZONE.localize(datetime.strptime(d2, '%Y-%m-%d %H:%M:%S'))
                end = TIMEZONE.localize(datetime.strptime(d3, '%Y-%m-%d %H:%M:%S'))
                # INVALID PROFILES CASE
                # set measures
                measures1 = [
                    ProfileHour(start, 1, True, 0),  # invalid profile
                    ProfileHour(middle, 0, True, 0),  # valid profile
                    ProfileHour(end, 1, True, 0)  # invalid profile
                ]
                # validate profiles
                valid, measures1 = REProfileZone5.validate_exported_energy(start, end, measures1)
                # test
                expected_valid = False
                expected_invalid_profiles = [
                    ProfileHour(start, 1, True, 0),  # invalid profile
                    ProfileHour(end, 1, True, 0)  # invalid profile
                ]
                # invalid profiles must be detected
                assert valid == expected_valid and measures1 == expected_invalid_profiles

                # VALID PROFILES CASE
                measures2 = [
                    ProfileHour(start, 0, True, 0),  # valid profile
                    ProfileHour(middle, 0, True, 0),  # valid profile
                    ProfileHour(end, 0, True, 0)  # valid profile
                ]
                # validate profiles
                valid, measures2 = REProfileZone5.validate_exported_energy(start, end, measures2)
                # test
                expected_valid = True
                # valid profiles must pass the test
                assert valid == expected_valid and measures2 == []


    with context('A 3.1A LB Tariff'):
        with it('must the initial_balance be different to result balance'):
            kva = 1
            the_tariff = T31A(kva=kva)
            initial_balance = {
                'P1': 100,
                'P2': 80,
                'P3': 60,
                'P4': 12,
                'P5': 15,
                'P6': 15,
            }
            res = the_tariff.apply_31A_LB_cof(
                initial_balance, self.start_date, self.end_date
            )

            assert res != initial_balance

    with context('A 3.1A Tariff with 6 periods'):
        with it('must take into account P4 in the result balance'):
            measures = []
            start = TIMEZONE.localize(datetime(2017, 9, 1))
            end = TIMEZONE.localize(datetime(2017, 9, 5))
            profile = Profile(start, end, measures)
            tariff = T31A()
            balance = {
                'P1': 10,
                'P2': 10,
                'P3': 10,
                'P4': 10,
                'P5': 10,
                'P6': 10,
            }
            total_expected = sum([x for x in balance.values()])
            estimation = profile.estimate(tariff, balance)
            total_estimated = sum([x.measure for x in estimation.measures])
            assert total_estimated == total_expected

with description('A profile'):
    with before.all:
        measures = []
        start = TIMEZONE.localize(datetime(2015, 3, 1, 1))
        end = TIMEZONE.localize(datetime(2015, 4, 1, 0))
        start_idx = start
        while start_idx <= end:
            measures.append(ProfileHour(
                TIMEZONE.normalize(start_idx), random.randint(0, 10), True, 0.0
            ))
            start_idx += timedelta(hours=1)
        self.profile = Profile(start, end, measures)

    with it('has to known the number of hours'):
        n_hours = self.profile.n_hours
        # See https://github.com/jaimegildesagredo/expects/issues/34
        # expect(n_hours).to(be(743))
        assert n_hours == 743


    with it('has to be displayed with useful information'):
        expr = (
            '<Profile \(2015-03-01 01:00:00\+\d{2}:\d{2} - '
            '2015-04-01 00:00:00\+\d{2}:\d{2}\) \d+h \d+kWh>'
        )
        expect(self.profile.__repr__()).to(match(expr))


    with it('has to sum hours per period the same as total hours'):
        hours_per_period = self.profile.get_hours_per_period(T20DHA())
        assert sum(hours_per_period.values()) == self.profile.n_hours

        hours_per_period = self.profile.get_hours_per_period(
            T20DHA(), only_valid=True
        )
        assert sum(hours_per_period.values()) == self.profile.n_hours

    with it('has to sum the consumption per period equal as total consumption'):
        consumption_per_period = self.profile.get_consumption_per_period(T20DHA())
        assert sum(consumption_per_period.values()) == self.profile.total_consumption

    with it('shouldn\'t have estimable hours'):
        estimable_hours = self.profile.get_estimable_hours(T20DHA())
        expect(sum(estimable_hours.values())).to(equal(0))


with description("An estimation"):
    with before.all:

        self.measures = []
        self.start = TIMEZONE.localize(datetime(2017, 9, 1))
        self.end = TIMEZONE.localize(datetime(2017, 9, 5))

        dates_difference_seconds = (self.end - self.start).total_seconds()
        # Invoice hours with fixed first hour (timedelta performs natural substraction, so first hour must be handled)
        self.expected_number_of_hours = (dates_difference_seconds / 3600) + 1
        self.profile = Profile(self.start, self.end, self.measures)


    with it("must analyze all hours if empty measures is provided"):
        tariffs_list = [
            {
                "tariff": T20A,
                "balance": {
                    'P1': 20,
                },
            },
            {
                "tariff": T20DHA,
                "balance": {
                    'P1': 20,
                    'P2': 10,
                },
            },
            {
                "tariff": T20DHS,
                "balance": {
                    'P1': 20,
                    'P2': 10,
                    'P3': 5,
                },
            },
            {
                "tariff": T21A,
                "balance": {
                    'P1': 20,
                },
            },
            {
                "tariff": T21DHA,
                "balance": {
                    'P1': 20,
                    'P2': 10,
                },
            },
            {
                "tariff": T21DHS,
                "balance": {
                    'P1': 20,
                    'P2': 10,
                    'P3': 5,
                },
            },
            {
                "tariff": T30A,
                "balance": {
                    'P1': 100,
                    'P2': 80,
                    'P3': 60,
                    'P4': 10,
                    'P5': 10,
                    'P6': 10,
                },
            },
            {
                "tariff": T30A_one_period,
                "balance": {
                    'P1': 100,
                    'P2': 80,
                    'P3': 60,
                },
            },
            {
                "tariff": T31A,
                "balance": {
                    'P1': 100,
                    'P2': 80,
                    'P3': 60,
                    'P5': 15,
                    'P6': 15,
                },
            },
            {
                "tariff": T31A_one_period,
                "balance": {
                    'P1': 100,
                    'P2': 80,
                    'P3': 60,
                },
            },
        ]

        for a_tariff in tariffs_list:
            tariff = a_tariff["tariff"]()
            periods = tariff.energy_periods
            balance = a_tariff["balance"]
            total_expected = sum(balance.values())

            estimation = self.profile.estimate(tariff, balance)
            total_estimated = sum([x.measure for x in estimation.measures])

            # [!] Number of hours must match
            assert self.expected_number_of_hours == len(estimation.measures), "Number of hours '{}' must match the expected '{}'".format(len(estimation.measures), self.expected_number_of_hours)

            # [!] Energy must match
            assert total_expected == total_estimated, "For tariff '{}' Total energy '{}' must match the expected '{}'".format(a_tariff["tariff"], total_estimated, total_expected)

    with it("must apply the penalty in 3.1A LB Tariffs"):
        fake_contract = {
            'start': TIMEZONE.localize(datetime(2017, 11, 1, 1, 0, 0)),
            'end': TIMEZONE.localize(datetime(2017, 12, 1, 0, 0, 0)),
            'kva': 50,
            'expected_profiled': 1244,
            'expected_hours': 720
        }
        measures = []
        profile = Profile(fake_contract['start'], fake_contract['end'], measures)

        the_tariff = T31A(kva=fake_contract['kva'])
        initial_balance = {
            'P1': 56,
            'P2': 231,
            'P3': 348,
            'P4': 0,
            'P5': 10,
            'P6': 205
        }

        estimation = profile.estimate(the_tariff, initial_balance)

        # by total
        total = sum([x.measure for x in estimation.measures])
        total_hours = len([x.date for x in estimation.measures])

        # by period
        res = the_tariff.apply_31A_LB_cof(
            initial_balance, fake_contract['start'], fake_contract['end']
        )
        sum_periods = sum([x for x in res.values()])

        assert fake_contract['expected_hours'] == total_hours, "has not profiled all hours"
        assert int(total) == fake_contract['expected_profiled'], "total not profiled correctly"
        assert int(sum_periods) == fake_contract['expected_profiled'], "total per period correctly profiled"

    with context("with accumulated energy"):
        with it("must handle accumulated values"):
            accumulated = Decimal(0.136)
            drag_by_perdiod = True
            self.profile = Profile(self.start, self.end, self.measures, accumulated, drag_by_perdiod)
            tariff = T21DHS()
            periods = tariff.energy_periods

            # This scenario, with an initial accumulated of 0.636 will raise a -1 total energy with an ending accumulated of 0.333962070125
            total_expected = 0
            balance = {
                'P1': 6.8,
                'P2': 3,
                'P3': 3.5,
            }
            total_expected = round(sum(balance.values()))
            expected_last_accumulated = Decimal(0.3000000000036)

            estimation = self.profile.estimate(tariff, balance)
            total_estimated = sum([x.measure for x in estimation.measures])

            # [!] Number of hours must match
            assert self.expected_number_of_hours == len(estimation.measures), "Number of hours '{}' must match the expected '{}'".format(len(estimation.measures), self.expected_number_of_hours)

            # [!] Energy must match
            assert total_expected == total_estimated, "Total energy '{}' must match the expected '{}'".format(total_estimated, total_expected)

            # [!] Last accumulated
            last_accumulated = estimation.measures[-1].accumulated
            assert float(last_accumulated) == float(expected_last_accumulated), "Last accumulated '{}' must match the expected '{}'".format(last_accumulated, expected_last_accumulated)

            # [!] Now estimate it using a by hour dragging
            # total energy will be +1kWh!
            drag_by_perdiod = False
            total_expected += 1
            expected_last_accumulated = Decimal(2.2E-12)

            self.profile = Profile(self.start, self.end, self.measures, accumulated, drag_by_perdiod)
            estimation = self.profile.estimate(tariff, balance)
            total_estimated_by_hour = sum([x.measure for x in estimation.measures])
            last_accumulated_by_hour = estimation.measures[-1].accumulated
            assert total_expected == total_estimated_by_hour, "Total energy dragged by hour '{}' must match the expected +1 '{}'".format(total_estimated_by_hour, total_expected)
            assert float(last_accumulated_by_hour) == float(expected_last_accumulated), "Last accumulated by hour '{}' must match the expected '{}'".format(last_accumulated_by_hour, expected_last_accumulated)


        with it("must handle incorrect accumulated values"):
            it_breaks = False
            accumulated = 2
            try:
                self.profile = Profile(self.start, self.end, self.measures, accumulated)
            except:
                it_breaks = True

            assert it_breaks, "A >1 accumulated must not work"

            it_breaks = False
            accumulated = -5
            try:
                self.profile = Profile(self.start, self.end, self.measures, accumulated)
            except:
                it_breaks = True

            assert it_breaks, "A <-1 accumulated must not work"

            it_breaks = False
            accumulated = "x"
            try:
                self.profile = Profile(self.start, self.end, self.measures, accumulated)
            except:
                it_breaks = True

            assert it_breaks, "A non numeric accumulated must not work"

        with it("must profile just regim especial"):
            di = '2019-01-01 01:00:00'
            df = '2019-02-01 00:00:00'
            start = TIMEZONE.localize(datetime.strptime(di, '%Y-%m-%d %H:%M:%S'))
            end = TIMEZONE.localize(datetime.strptime(df, '%Y-%m-%d %H:%M:%S'))

            measures = []
            drag_by_perdiod = True
            profile = Profile(start, end, measures, 0.0)
            profile.profile_class = REProfileZone2
            tariff = TRE()

            climatic_zone = 2
            re_balance = {
                'P0': 252
            }

            estimation = profile.estimate(tariff, re_balance)
            total_estimated = estimation.total_consumption
            assert total_estimated == re_balance['P0'], "RE not profiled correctly"
