from enerdata.datetime import datetime
from enerdata.datetime.solar_hour import convert_to_solar_hour
from dateutil.relativedelta import relativedelta

with description("The civil hour"):
    with it("it's two hours more than solar"):
        dt = datetime.now()
        final_dt = dt + relativedelta(years=25)
        while dt < final_dt:
            dt = dt + relativedelta(days=1)
            res = convert_to_solar_hour(dt)
            assert dt != res

