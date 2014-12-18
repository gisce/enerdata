from enerdata.metering.measure import *

class Meter(object):
    def __init__(self, serial):
        self.serial = serial
        self.energy_measures = []
        self.power_measures = []

    def add_energy_measure(self, measure):
        assert isinstance(measure, EnergyMeasure)
        self.energy_measures.append(measure)

    def add_power_measure(self, measure):
        assert isinstance(measure, PowerMeasure)
