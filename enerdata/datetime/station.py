from datetime import datetime
from .timezone import TIMEZONE


def get_station(dt):
    assert isinstance(dt, datetime)
    if not dt.tzinfo:
        dt = TIMEZONE.localize(dt)
    if TIMEZONE.normalize(dt).dst():
        return 'summer'
    else:
        return 'winter'
