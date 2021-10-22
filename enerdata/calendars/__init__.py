# coding=utf-8
from datetime import date
from workalendar.europe import Spain


class REECalendar(Spain):
    """Specific calendar for REE in Spain.

    The holidays are the same in Spain but only the ones which are not
    changeble and not fixed in a day.
    """
    include_epiphany = False
    include_good_friday = False

    # Add epiphany
    def get_fixed_holidays(self, year):
        days = super(REECalendar, self).get_fixed_holidays(year)
        if year >= 2022:
            days.append((date(year, 1, 6), "Día de Reyes"))
        return days
