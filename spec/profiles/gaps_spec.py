from enerdata.profiles.profile import *
from enerdata.contracts.tariff import *
from expects import *

with description('A profile with gaps'):
    with before.all:
        import random
        measures = []
        start = TIMEZONE.localize(datetime(2015, 3, 1, 1))
        end = TIMEZONE.localize(datetime(2015, 4, 1, 0))

        gap_start = TIMEZONE.localize(datetime(2015, 3, 15))
        gap_end = TIMEZONE.localize(datetime(2015, 3, 16))
        start_idx = start
        self.gaps = []
        self.number_invalid_hours = 0
        self.complete_profile = []
        while start_idx <= end:
            energy = random.randint(0, 10)
            self.complete_profile.append(ProfileHour(start_idx, energy, True))
            if gap_start < start_idx < gap_end:
                self.gaps.append(start_idx)
                start_idx += timedelta(hours=1)
                continue
            if random.randint(0, 10) > 8:
                valid = False
                self.number_invalid_hours += 1
                self.gaps.append(start_idx)
            else:
                valid = True
            measures.append(ProfileHour(
                TIMEZONE.normalize(start_idx), energy, valid
            ))
            start_idx += timedelta(hours=1)
        self.profile = Profile(start, end, measures)

    with it('has to known the gaps'):
        expect(self.profile.gaps).to(contain_exactly(*self.gaps))


    with it('has sum hours per period the same as total hours'):
        hours_per_period = self.profile.get_hours_per_period(T20DHA())
        assert sum(hours_per_period.values()) == self.profile.n_hours

    with it('has sum valid hours per period from measures'):
        hours_per_period = self.profile.get_hours_per_period(
            T20DHA(), only_valid=True
        )
        total_hours = self.profile.n_hours_measures - self.number_invalid_hours
        assert sum(hours_per_period.values()) == total_hours

    with it('shouldn\'t have estimable hours'):
        estimable_hours = self.profile.get_estimable_hours(T20DHA())
        expect(sum(estimable_hours.values())).to(be_above(0))

    with it('has to be the same the balance and the consumption + estimable'):
        tariff = T20DHA()
        balance = Counter()
        for ph in self.complete_profile:
            period = tariff.get_period_by_date(ph.date)
            balance[period.code] += ph.measure

        total = sum(balance.values())
        consumption = self.profile.get_consumption_per_period(tariff)
        estimable = self.profile.get_estimable_consumption(tariff, balance)
        for period in consumption:
            energy = consumption[period] + estimable[period]
            expect(energy).to(equal(balance[period]))


    with it('has to estimate energy for the gaps'):
        # Calculate the balance
        balance = Counter()
        tariff = T20DHA()
        tariff.cof = 'A'
        for ph in self.complete_profile:
            period = tariff.get_period_by_date(ph.date)
            balance[period.code] += ph.measure
        profile_estimated = self.profile.estimate(tariff, balance)

        total_energy = sum(balance.values())
        expect(profile_estimated.total_consumption).to(equal(total_energy))


    with context('Is an empty profile'):
        with it('has to generate all the profile estimating'):
            balance = Counter()
            tariff = T20DHA()
            tariff.cof = 'A'
            profile = Profile(
                self.profile.start_date, self.profile.end_date, []
            )
            for ph in self.complete_profile:
                period = tariff.get_period_by_date(ph.date)
                balance[period.code] += ph.measure
            profile_estimated = profile.estimate(tariff, balance)

            total_energy = sum(balance.values())
            expect(profile_estimated.total_consumption).to(equal(total_energy))
