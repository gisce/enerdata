from enerdata.datetime import datetime
from enerdata.datetime.timezone import TIMEZONE
from pytz import utc
from dateutil import relativedelta
from enerdata.datetime.station import *


with description('The station module'):
    with it('has to return the station by date'):
        assert get_station(datetime(2014, 1, 1)) == 'winter'
        assert get_station(datetime(2014, 4, 1)) == 'summer'
        assert get_station(datetime(2014, 10, 26, 2)) == 'winter'
        assert get_station(datetime(2014, 3, 30, 2)) == 'summer'
        assert get_station(TIMEZONE.localize(datetime(2014, 10, 26, 2), is_dst=True)) == 'summer'

with description("The civil hour"):
    with it("it's two hours more than solar"):
        dt = datetime.now()
        final_dt = dt + relativedelta(years=2)
        while dt < final_dt:
            civil_hour = dt
            solar_hour = TIMEZONE.localize(civil_hour, is_dst=True) # No daylight saving time
            solar_hour = solar_hour.astimezone(utc)
        assert solar_hour == civil_hour
