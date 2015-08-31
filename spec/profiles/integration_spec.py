from enerdata.profiles.profile import *

from expects import *


with description('Profiles integration with third party data'):
    with context('Data from MongoDB tg_profile'):
        
        with it('has to localize the timestamp'):

            def localize_season(dt, season):
                dst = bool(season == 'S')
                return TIMEZONE.normalize(TIMEZONE.localize(dt, is_dst=dst))

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
