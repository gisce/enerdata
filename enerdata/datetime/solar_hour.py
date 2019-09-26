from enerdata.datetime import datetime
from enerdata.datetime.timezone import TIMEZONE
from pytz import utc


def convert_to_solar_hour(civil_hour):
    """
    Convert datetime to equivalent datetime solar hour
    :param civil_hour: datetimed
    :return: datetime equivalent solar hour
    """
    if not isinstance(civil_hour, datetime):
        raise ValueError('datetime was expected, found {}'.format(civil_hour))
    if not civil_hour.tzinfo:
        raise ValueError('datetime must be located: {}'.format(civil_hour))
    solar_hour = civil_hour.astimezone(utc)

    return solar_hour
