from enerdata.datetime import datetime
from dateutil.relativedelta import relativedelta
from enerdata.profiles.profile import *
from enerdata.datetime.station import *


with description('Downloading coefficients '):
    with it('it should not include the final month'):
        coeff = REEProfile.get_range(
            datetime(2018, 3, 24, 0, 0),
            datetime(2018, 5, 1, 0, 0) - relativedelta(days=1)
        )
        assert coeff[-1].hour.month == 5