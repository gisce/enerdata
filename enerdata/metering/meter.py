import bisect

from enerdata.metering.measure import *


class Meter(object):
    def __init__(self, serial):
        self.serial = serial
        self.energy_measures = []
        self.power_measures = []

    def add_energy_measure(self, measure):
        assert isinstance(measure, EnergyMeasure)
        pos = bisect.bisect_right(self.energy_measures, measure)
        self.energy_measures.insert(pos, measure)

    def add_power_measure(self, measure):
        assert isinstance(measure, PowerMeasure)
        pos = bisect.bisect_right(self.power_measures, measure)
        self.power_measures.insert(pos, measure)
