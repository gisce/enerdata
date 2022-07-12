# -*- coding: utf-8 -*-
from datetime import date
from enerdata.calendars import REECalendar
from expects import *
from mamba import description, it
from workalendar.europe import Spain


with description('REE Calendar'):
    with it('must be inherit from Spain Calendar'):
        ree_cal = REECalendar()
        expect(ree_cal).to(be_a(Spain))

    with it('must have the same holidays in Spain '
            'without epiphany and good friday'):
        cal = REECalendar()
        expect(cal.is_holiday(date(2017, 1, 6))).to(be_false)
        expect(cal.is_holiday(date(2017, 4, 14))).to(be_false)

    with it('must have epiphany as holiday from 2022'):
        cal = REECalendar()
        expect(cal.is_holiday(date(2022, 1, 6))).to(be_true)
        expect(cal.is_holiday(date(2021, 1, 6))).to(be_false)
