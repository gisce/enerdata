from enerdata.contracts import Tariff


class ProfileTariff(Tariff):

    def sum_cofs(self, start, end):
        sum_cofs = dict.fromkeys(self.energy_periods.keys(), 0)
        return sum_cofs