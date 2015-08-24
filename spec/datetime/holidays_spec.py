from datetime import date

from enerdata.datetime.holidays import get_holidays
from expects import *

with description('The holidays modules'):
    with it('Has to return the Spain holidays of 2015'):
        holidays = get_holidays(2015)
        expect(list(holidays)).to(contain_only(*[
            date(2015, 1, 1),
            date(2015, 1, 6),
            date(2015, 4, 3),
            date(2015, 5, 1),
            date(2015, 8, 15),
            date(2015, 10, 12),
            date(2015, 12, 8),
            date(2015, 12, 25)
        ]))