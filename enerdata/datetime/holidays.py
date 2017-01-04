from enerdata.calendars import REECalendar

CALENDAR = REECalendar()


def get_holidays(year):
    return CALENDAR.holidays_set(year)
