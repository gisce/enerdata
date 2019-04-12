import calendar
from datetime import timedelta


def get_num_of_workdays_holidays(init_date, end_date, holidays_list):
    workdays = 0
    holidays = 0

    _date = init_date
    while _date <= end_date:
        if (calendar.weekday(_date.year, _date.month, _date.day) in (5, 6)
        ) or (_date.date() in holidays_list):
            holidays += 1
        else:
            workdays += 1
        _date += timedelta(days=1)

    return workdays, holidays
