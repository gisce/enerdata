from expects import *
from enerdata.cups.cups import *


with description('Validating checksums'):
    with it('has to be 2 length'):
        ch = checksum('291000000000001')
        assert len(ch) == 2
    with it('has to return the checksum'):
        ch = checksum('291000000000001')
        assert ch == 'DN'
    with it('has to return True if CUPS number is valid'):
        assert check_cups_number('ES0291000000000001DN0F') is True
    with it('has to return False if CUPS number is invalid'):
        assert check_cups_number('ES0291000000000001DX0F') is False
    with it('has to accept cups number with 20 digits'):
        assert check_cups_number('ES0291000000000001DN') is True

with description('Creating a CUPS'):
    with it('should fail if CUPS number is invalid'):
        expect(lambda: CUPS('ES0291000000000001DX0F')).to(raise_error(ValueError))

