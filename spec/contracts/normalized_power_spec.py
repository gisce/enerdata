# coding=utf-8

NORMALIZED_POWERS = {
    '0,330': ('220v', 1.5)
}

with description('A normalized power class'):
    with context('if the power is normalized'):
        with _it('must return the voltage and the intesity of this normalized power'):
            pass
    with context('if the power is not normalized'):
        with it('must raise an ValueError Exception'):
            pass
    with _it('must have a method to check if is a normalized power'):
        pass
