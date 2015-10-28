try:
    from collections import Counter
except ImportError:
    from backport_collections import Counter
from decimal import Decimal


class Dragger(Counter):

    def drag(self, number, key='default'):
        number = Decimal(str(number)) + self[key]
        aprox = int(round(number))
        self[key] = number - aprox
        return aprox
