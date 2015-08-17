from enerdata.profiles.profile import *
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
        while start_idx <= end:
            if gap_start < start_idx < gap_end:
                self.gaps.append(start_idx)
                start_idx += timedelta(hours=1)
                continue
            measures.append(ProfileHour(
                TIMEZONE.normalize(start_idx), random.randint(0, 10), True
            ))
            start_idx += timedelta(hours=1)
        self.profile = Profile(start, end, measures)

    with it('has to known the gaps'):
        expect(self.profile.gaps).to(contain_exactly(*self.gaps))

