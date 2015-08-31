from enerdata.profiles.profile import *

from expects import *


def localize_season(dt, season):
    dst = bool(season == 'S')
    return TIMEZONE.normalize(TIMEZONE.localize(dt, is_dst=dst))


def convert_to_profilehour(measure):
    ph = ProfileHour(
        localize_season(measure['timestamp'], measure['season']),
        measure['ai'],
        measure['valid']
    )
    return ph


with description('Profiles integration with third party data'):
    with context('Data from MongoDB tg_profile'):
        with before.all:
            import random
            item_tmpl = {
                u'ae': u'0',
                u'ai': u'17',
                u'create_date': datetime(2013, 8, 6, 10, 43, 6, 252000),
                u'create_uid': 1,
                u'id': 9,
                u'magn': u'1000',
                u'name': u'CUR3781013700',
                u'r1': u'0',
                u'r2': u'0',
                u'r3': u'0',
                u'r4': u'24',
                u'season': u'S',
                u'timestamp': datetime(2013, 7, 24, 12, 0),
                u'valid': False,
                u'valid_date': False
            }
            self.measures = []
            start = datetime(2015, 5, 1, 1)
            end = datetime(2015, 6, 1, 0)

            gap_start = datetime(2015, 5, 15)
            gap_end = datetime(2015, 5, 16)
            start_idx = start
            item_id = 1
            self.gaps = []
            self.number_invalid_hours = 0
            self.complete_profile = []
            while start_idx <= end:
                energy = random.randint(0, 10)
                profile_hour = item_tmpl.copy()
                profile_hour['timestamp'] = start_idx
                profile_hour['ai'] = energy
                profile_hour['id'] = item_id
                self.complete_profile.append(profile_hour)
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
                profile_hour['valid'] = valid
                self.measures.append(profile_hour)
                start_idx += timedelta(hours=1)
                item_id += 1

        with it('has to localize the timestamp'):

            data = [
                {'timestamp': datetime(2015, 3, 29, 0), 'season': 'W'},
                {'timestamp': datetime(2015, 3, 29, 1), 'season': 'W'},
                {'timestamp': datetime(2015, 3, 29, 3), 'season': 'S'},
                {'timestamp': datetime(2015, 3, 29, 4), 'season': 'S'},
            ]
            data_localized = [
                TIMEZONE.normalize(TIMEZONE.localize(datetime(2015, 3, 29, 0))),
                TIMEZONE.normalize(TIMEZONE.localize(datetime(2015, 3, 29, 1))),
                TIMEZONE.normalize(TIMEZONE.localize(datetime(2015, 3, 29, 3))),
                TIMEZONE.normalize(TIMEZONE.localize(datetime(2015, 3, 29, 4)))
            ]
            for localized, to_localize in zip(data_localized, data):
                 test = localize_season(
                     to_localize['timestamp'], to_localize['season']
                 )
                 expect(test).to(equal(localized))

        with it('has to detect the gaps'):
            ph_measures = []
            start = TIMEZONE.localize(datetime(2015, 5, 1, 1))
            end = TIMEZONE.localize(datetime(2015, 6, 1, 0))
            for measure in self.measures:
                ph = convert_to_profilehour(measure)
                ph_measures.append(ph)

            profile = Profile(start, end, ph_measures)
            expect(profile.gaps).to(contain(*[
                TIMEZONE.localize(x) for x in self.gaps
            ]))
