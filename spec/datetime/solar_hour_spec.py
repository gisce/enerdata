from enerdata.datetime import datetime
from enerdata.datetime.station import get_station
from enerdata.datetime.solar_hour import convert_to_solar_hour
from enerdata.datetime.timezone import TIMEZONE
from dateutil.relativedelta import relativedelta
from expects import expect, equal

DIFFERENCE_HOURS = {'summer': 2, 'winter': 1}

with description("The solar hour"):

    with context("in Summer"):
        with it("is the civil time plus 2"):
            dt = TIMEZONE.localize(datetime(2019, 4, 1, 1))
            final_dt = dt + relativedelta(months=3)
            hours = DIFFERENCE_HOURS['summer']
            while dt < final_dt:
                dt = dt + relativedelta(hours=1)
                solar_hour = convert_to_solar_hour(dt)
                civil_hour_to_expect = dt - relativedelta(hours=hours)
                assert civil_hour_to_expect.hour == solar_hour.hour
        with it("is the civil time plus 1"):
            dt = TIMEZONE.localize(datetime(2019, 11, 1, 1))
            final_dt = dt + relativedelta(months=3)
            hours = DIFFERENCE_HOURS['winter']
            while dt < final_dt:
                dt = dt + relativedelta(hours=1)
                solar_hour = convert_to_solar_hour(dt)
                civil_hour_to_expect = dt - relativedelta(hours=hours)
                assert civil_hour_to_expect.hour == solar_hour.hour

    with context("when it's random"):
        with it("must meet the difference of hours with the civil"):
            dtc = TIMEZONE.localize(datetime.now())
            station = get_station(dtc)
            hours = DIFFERENCE_HOURS[station]
            solar_hour = convert_to_solar_hour(dtc)
            civil_hour_to_expect = dtc - relativedelta(hours=hours)
            expect(civil_hour_to_expect.hour).to(equal(solar_hour.hour))
