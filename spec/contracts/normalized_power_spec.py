# coding=utf-8
from expects import expect, raise_error

from enerdata.contracts.normalized_power import NormalizedPower
from enerdata.contracts.normalized_power import NORMALIZED_POWERS as OFFICIAL_NP

NORMALIZED_POWERS = {
    330: ('1x220', '1.5')
}

NOT_NORMALIZED_POWERS = [111]

NOT_NORMALIZED_100 = list(range(100, 15001, 100))
NORMALIZED_100 = []
for power in OFFICIAL_NP:
    try:
        NOT_NORMALIZED_100.remove(power)
    except ValueError:
        continue

with description('A normalized power class'):
    with context('if the power is normalized'):
        with it('must return the voltage and the '
                 'intesity of this normalized power'):
            n_p = NormalizedPower()
            for normal in NORMALIZED_POWERS:
                assert n_p.get_volt_int(normal) == NORMALIZED_POWERS[normal]
    with context('if the power is not normalized'):
        with it('must raise an ValueError Exception'):
            n_p = NormalizedPower()
            for not_normal in NOT_NORMALIZED_POWERS:
                expect(
                    lambda: n_p.get_volt_int(not_normal)
                ).to(
                    raise_error(ValueError)
                )
    with it('must have a method to check if is a normalized power'):
        n_p = NormalizedPower()
        for normal in NORMALIZED_POWERS:
            assert n_p.is_normalized(normal)

        for not_normal in NOT_NORMALIZED_POWERS:
            assert not n_p.is_normalized(not_normal)
    with it('must return all the normalized powers between two values in '
            'ascending order (the first one shouldn\'t included)'):
        n_p = NormalizedPower()
        norm_power_01 = [100, 191, 200, 300, 330, 345, 381, 399, 400, 445, 466,
                         500, 572, 598, 600, 635, 660, 665, 690, 700, 770, 800,
                         805, 900, 953, 987, 998, 1000]

        norm_power_02 = [2300, 2304, 2400, 2425, 2500, 2540, 2600, 2660, 2700,
                         2800, 2858, 2900, 2988, 3000, 3100, 3175, 3200, 3291,
                         3300]

        assert list(n_p.get_norm_powers(0, 1000)) == norm_power_01
        assert list(n_p.get_norm_powers(2200, 3300)) == norm_power_02

    with context('if the power is multiple of 100 W and not normalized'):
        with it('must no return voltage'):
            n_p = NormalizedPower()
            for power in NOT_NORMALIZED_100:
                assert n_p.get_volt_int(power) == (None, None)

        with it('must not raise a ValueError Exception'):
            n_p = NormalizedPower()
            for normal in NOT_NORMALIZED_100:
                assert n_p.is_normalized(normal)
