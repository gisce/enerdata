# coding=utf-8
from workalendar.europe import Spain


class REECalendar(Spain):
    """Specific calendar for REE in Spain.

    The holidays are the same in Spain but only the ones which are not
    changeble and not fixed in a day.
    """
    include_epiphany = False
    include_good_friday = False


