from enerdata.datetime import datetime
from dateutil.relativedelta import relativedelta
from enerdata.profiles.profile import *
from enerdata.datetime.station import *

ONE_MONTH_DATE_SET = ['1/2018']
DATE_SET = ['3/2018', '4/2018', '5/2018']

def get_data_ranges(start, end):
    from datetime import datetime
    from dateutil.relativedelta import relativedelta
    cofs = []
    start = datetime(start.year, start.month, 1)
    end = datetime(end.year, end.month, 1)
    while start <= end:
        cof = '{0}/{1}'.format(start.month, start.year)
        cofs.append(cof)
        start += relativedelta(months=1)
    return cofs


with description('Downloading coefficients '):
    with it('it should not include the final month'):
        coeff = REEProfile.get_range(
            datetime(2018, 3, 24, 0, 0),
            datetime(2018, 5, 1, 0, 0) - relativedelta(days=1)
        )
        assert coeff[-1].hour.month == 5

    with it('Final date end of month'):
        di = datetime(2018, 3, 24, 0, 0)
        df = datetime(2018, 6, 1, 0, 0)
        assert get_data_ranges(di, df - relativedelta(days=1)) == DATE_SET

    with it('Final date between month'):
        di = datetime(2018, 3, 24, 0, 0)
        df = datetime(2018, 5, 15, 0, 0)
        assert get_data_ranges(di, df - relativedelta(days=1)) == DATE_SET

    with it('One month invoice'):
        di = datetime(2018, 1, 1, 1, 0)
        df = datetime(2018, 1, 31, 0, 0)
        assert get_data_ranges(
            di, df - relativedelta(days=1)) == ONE_MONTH_DATE_SET

    with it('One day invoice'):
        di = datetime(2018, 1, 1, 1, 0)
        df = datetime(2018, 1, 2, 0, 0)
        assert get_data_ranges(
            di, df - relativedelta(days=1)) == ONE_MONTH_DATE_SET
