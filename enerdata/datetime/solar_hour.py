from enerdata.datetime import datetime
from enerdata.datetime.timezone import TIMEZONE
from pytz import utc


def convert_to_solar_hour(civil_hour=False):
    """
    Convert datetime to equivalent datetime solar hour
    :param civil_hour: datetime
    :return: datetime equivalent solar hour
    """
    if not civil_hour:
        civil_hour = datetime.now()
    if not isinstance(civil_hour, datetime):
        raise ValueError('% date is not a datetime' % civil_hour)
    solar_hour = TIMEZONE.localize(civil_hour, is_dst=True)  # No daylight saving time
    solar_hour = solar_hour.astimezone(utc)

    return solar_hour
