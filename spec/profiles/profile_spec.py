from enerdata.profiles.profile import *
from enerdata.contracts.tariff import T20DHA



with description("A coeficient"):
    with before.all:
        start = TIMEZONE.localize(datetime(2014, 1, 1))
        end = TIMEZONE.localize(datetime(2015, 1, 1))
        cofs = []
        day = start
        while day < end:
            day += timedelta(hours=1)
            cofs.append((TIMEZONE.normalize(day), {'A': 0, 'B': 0}))
        self.cofs = cofs

    with it("must read and sum the hours of the file"):
        cofs = REEProfile.get(2014, 10)
        # We have one hour more in October
        assert len(cofs) == (31 * 24) + 1
        # The first second hour in the 26th of October is DST
        assert cofs[(24 * 25) + 1][0].dst() == timedelta(seconds=3600)
        # The second second hour in the 26th of October is not DST
        assert cofs[(24 * 25) + 2][0].dst() == timedelta(0)


    with it("must return the sum of coefs for each period"):
        c = Coefficients(self.cofs)
        t = T20DHA()
        t.cof = 'A'
        assert c.get_coefs_by_tariff(t, date(2014, 1, 1), date(2014, 1, 31)) == {'P1': 0, 'P2': 0}


    with it('should insert coeficients if empty'):
        c = Coefficients()
        assert len(c.coefs) == 0
        c.insert_coefs(self.cofs)
        assert len(c.coefs) == (365 * 24)

    with it('should replace the coeficients'):
        c = Coefficients(self.cofs)
        assert len(c.coefs) == (365 * 24)
        c.insert_coefs(self.cofs)
        assert len(c.coefs) == (365 * 24)

    with it('should append the coefficients'):
        c = Coefficients()
        c.insert_coefs(self.cofs)
        start = TIMEZONE.localize(datetime(2015, 1, 1))
        end = TIMEZONE.localize(datetime(2015, 2, 1))
        cofs = []
        day = start
        while day < end:
            cofs.append((TIMEZONE.normalize(day + timedelta(hours=1)), {'A': 0, 'B': 0}))
            day += timedelta(hours=1)
        c.insert_coefs(cofs)
        assert c.coefs[0][0] == TIMEZONE.localize(datetime(2014, 1, 1, 1))
        assert c.coefs[-1][0] == TIMEZONE.localize(datetime(2015, 2, 1))
        assert len(c.coefs) == ((365 * 24) + (31 * 24))

    with it('should return the range of dates'):
        c = Coefficients(self.cofs)
        cofs = c.get_range(date(2014, 10, 26), date(2014, 10, 26))
        assert len(cofs) == 25
        assert cofs[1][0] == TIMEZONE.localize(datetime(2014, 10, 26, 2), is_dst=True)
        assert cofs[2][0] == TIMEZONE.localize(datetime(2014, 10, 26, 2), is_dst=False)

        cofs = c.get_range(date(2014, 3, 30), date(2014, 3, 30))
        assert len(cofs) == 23
        assert cofs[1][0] == TIMEZONE.normalize(TIMEZONE.localize(datetime(2014, 3, 30, 2)))
