import bisect
from datetime import date

from enerdata.metering.measure import *


class Meter(object):
    def __init__(self, serial, start_date=None):
        self.serial = serial
        self.energy_measures = []
        self.power_measures = []
        if not start_date:
            start_date = date.today()
        self.start_date = start_date
        self.end_date = None

    def add_measure(self, measure):
        assert isinstance(measure, (EnergyMeasure, PowerMeasure))
        assert measure.date >= self.start_date
        if self.end_date:
            assert measure.date <= self.end_date
        if isinstance(measure, EnergyMeasure):
            dst = self.energy_measures
        elif isinstance(measure, PowerMeasure):
            dst = self.power_measures
        pos = bisect.bisect_right(dst, measure)
        dst.insert(pos, measure)
