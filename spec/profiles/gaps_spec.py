from enerdata.profiles.profile import *
from enerdata.contracts.tariff import *
from expects import *

with description('A profile with gaps'):
    with before.all:
        import random
        measures = []
        start = TIMEZONE.localize(datetime(2015, 3, 1, 1))
        end = TIMEZONE.localize(datetime(2015, 4, 1, 1))

        gap_start = TIMEZONE.localize(datetime(2015, 3, 15))
        gap_end = TIMEZONE.localize(datetime(2015, 3, 16))
        start_idx = start
        self.gaps = []
        self.number_invalid_hours = 0
        while start_idx <= end:
            if gap_start < start_idx < gap_end:
                self.gaps.append(start_idx)
                start_idx += timedelta(hours=1)
                continue
            if random.randint(0, 10) > 8:
                valid = False
                self.number_invalid_hours += 1
            else:
                valid = True
            measures.append(ProfileHour(
                TIMEZONE.normalize(start_idx), random.randint(0, 10), valid
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