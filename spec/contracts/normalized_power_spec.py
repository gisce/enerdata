# coding=utf-8
from expects import expect, raise_error

from enerdata.contracts.normalized_power import NormalizedPower

NORMALIZED_POWERS = {
    330: ('220', '1.5')
}

NOT_NORMALIZED_POWERS = [100]

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
        norm_power_01 = [330, 345, 660, 690, 770, 805, 987]
        norm_power_02 = [2300, 2304, 2425, 3291, 3300]
        assert n_p.get_norm_powers(0, 1000) == norm_power_01
        assert n_p.get_norm_powers(2200, 3300) == norm_power_02
