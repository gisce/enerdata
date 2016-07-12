try:
    from collections import Counter
except ImportError:
    from backport_collections import Counter

from decimal import Decimal, ROUND_HALF_UP


class Dragger(Counter):

    def drag(self, number, key='default'):
        if number == 0 and abs(self[key]) == Decimal('0.5'):
            # Avoid oscillation between -1 and 1 and dragging 0.5 and -0.5
            return number

        number = Decimal(str(number)) + self[key]
        aprox = int(round(number))

        aprox = int(number.quantize(Decimal('1'), rounding=ROUND_HALF_UP))

        self[key] = number - aprox
        return aprox  + 0
