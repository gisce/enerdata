from enerdata.profiles.profile import *
from enerdata.datetime.station import *
from enerdata.contracts.tariff import T20A


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

def final_day_of_month(end):
    return end.day == 1 and end.hour >= 1

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
        if final_day_of_month(df):
            assert get_data_ranges(di, df) == DATE_SET
        else:
            assert get_data_ranges(di, df - relativedelta(days=1)) == DATE_SET

    with it('Final date start of month'):
        di = datetime(2018, 3, 24, 0, 0)
        df = datetime(2018, 5, 1, 1, 0)
        if final_day_of_month(df):
            assert get_data_ranges(di, df) == DATE_SET
        else:
            assert get_data_ranges(di, df - relativedelta(days=1)) == DATE_SET

    with it('Final date between month'):
        di = datetime(2018, 3, 24, 0, 0)
        df = datetime(2018, 5, 15, 0, 0)
        if final_day_of_month(df):
            assert get_data_ranges(di, df) == DATE_SET
        else:
            assert get_data_ranges(di, df - relativedelta(days=1)) == DATE_SET

    with it('One month invoice'):
        di = datetime(2018, 1, 1, 1, 0)
        df = datetime(2018, 2, 1, 0, 0)
        if final_day_of_month(df):
            assert get_data_ranges(di, df) == ONE_MONTH_DATE_SET
        else:
            assert get_data_ranges(
                di, df - relativedelta(days=1)) == ONE_MONTH_DATE_SET

    with it('One day invoice'):
        di = datetime(2018, 1, 1, 1, 0)
        df = datetime(2018, 1, 2, 0, 0)
        if final_day_of_month(df):
            assert get_data_ranges(di, df) == ONE_MONTH_DATE_SET
        else:
            assert get_data_ranges(
                di, df - relativedelta(days=1)) == ONE_MONTH_DATE_SET

with description('Profiling...'):
    with before.all:
        # Check that the get_coefs changes do not break the profiling"
        self.measures = []
        self.expected_hours = 744

    with it("Profile a full month"):
        start = TIMEZONE.localize(datetime(2018, 5, 1, 1))
        end = TIMEZONE.localize(datetime(2018, 6, 1, 0))
        tariff = T20A()
        accumulated = 0
        balance = {
            'P1': 6.8,
            'P2': 3,
            'P3': 3.5,
        }

        profile = Profile(start, end, self.measures, accumulated)
        estimation = profile.estimate(tariff, balance)

        assert self.expected_hours == len(estimation.measures)
        assert start == estimation.start_date
        assert end == estimation.end_date

    with it("Profile with current date to download REE coefficients last month"):
        end_year = datetime.now().year
        end_month = datetime.now().month
        start = TIMEZONE.localize(datetime(2018, 5, 1, 1))
        end = TIMEZONE.localize(datetime(end_year, end_month, 1, 0))

        tariff = T20A()
        accumulated = 0
        balance = {
            'P1': 6.8,
            'P2': 3,
            'P3': 3.5,
        }

        profile = Profile(start, end, self.measures, accumulated)
        try:
            estimation = profile.estimate(tariff, balance)
        except Exception as err:
            assert err.message != "Profiles from REE not found"
