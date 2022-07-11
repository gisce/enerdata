try:
    from collections import Counter
except ImportError:
    from backport_collections import Counter
from decimal import Decimal

import math


def my_round(x, d=0):
    x = float(x)
    p = 10 ** d
    if x > 0:
        return float(math.floor((x * p) + 0.5))/p
    else:
        return float(math.ceil((x * p) - 0.5))/p


class Dragger(Counter):

    def drag(self, number, key='default'):
        if number == 0 and abs(self[key]) == Decimal('0.5'):
            # Avoid oscillation between -1 and 1 and dragging 0.5 and -0.5
            return number

        number = Decimal(str(number)) + self[key]
        aprox = int(my_round(number))
        self[key] = number - aprox
        return aprox
