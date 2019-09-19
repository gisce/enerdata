from enerdata.datetime import datetime
from enerdata.datetime.timezone import TIMEZONE
from enerdata.datetime.station import *


with description('The station module'):
    with it('has to return the station by date'):
        assert get_station(datetime(2014, 1, 1)) == 'winter'
        assert get_station(datetime(2014, 4, 1)) == 'summer'
        assert get_station(datetime(2014, 10, 26, 2)) == 'winter'
        assert get_station(datetime(2014, 3, 30, 2)) == 'summer'
        assert get_station(TIMEZONE.localize(datetime(2014, 10, 26, 2), is_dst=True)) == 'summer'
