CHECKSUM_TABLE = 'TRWAGMYFPDXBNJZSQVHLCKE'


def checksum(number):
    try:
        rest0 = int(number) % 529
    except ValueError:
        raise
    cof = int(rest0 / 23)
    rest1 = rest0 % 23
    return CHECKSUM_TABLE[cof] + CHECKSUM_TABLE[rest1]


def check_cups_number(cups_number):
    tmp = cups_number[2:18]
    cs = checksum(tmp)
    check = 'ES%s%s' % (tmp, cs)
    if check != cups_number[:20]:
        return False
    return True


class CUPS(object):
    """CUPS object.
    """
    def __init__(self, number):
        if not check_cups_number(number):
            raise ValueError()
        self.number = number