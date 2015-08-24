from workalendar.europe import Spain

CALENDAR = Spain()


def get_holidays(year):
    return CALENDAR.holidays_set(year)