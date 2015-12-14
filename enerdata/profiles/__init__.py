try:
    from collections import Counter
except ImportError:
    from backport_collections import Counter
from decimal import Decimal


class Dragger(Counter):

    def drag(self, number, key='default'):
        if number == 0 and abs(self[key]) == Decimal('0.5'):
            # Avoid oscillation between -1 and 1 and dragging 0.5 and -0.5
            return number

        number = Decimal(str(number)) + self[key]
        aprox = int(round(number))
        self[key] = number - aprox
        return aprox
