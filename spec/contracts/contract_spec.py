from expects.testing import failure

from enerdata.contracts.contract import *


with description('Creating a contract'):
    with it('should be in draft state'):
        c = Contract()
        assert c.state == 'draft'

    with it('should have a list for modifications empty'):
        c = Contract()
        assert len(c.modifications) == 0

with description('Creating a modification'):
    with context('If no start date is given'):
        with it('should be today'):
            m = Modification()
            assert m.start_date == date.today()

    with context('If a start date is given'):
        with it('should be assigned'):
            m = Modification(date(2014, 1, 1))
            assert m.start_date == date(2014, 1, 1)


with description('Modifying a contract'):
    with it('should fail if is not a Modification instance'):
        c = Contract()
        m = Modification()
        c.modify(m)

    with it('should update contract values'):
        c = Contract()
        c.contracted_power = 1
        m = Modification()
        m.contracted_power = 10
        c.modify(m)
        assert c.contracted_power == m.contracted_power

    with it('should detect changes'):
        c = Contract()
        c.contracted_power = 1
        m = Modification()
        m.contracted_power = 10
        changes = {'contracted_power': {'old': 1, 'new': 10}}
        assert c.get_changes(m) == changes

    with it('should create in draft state'):
        m = Modification()
        assert m.state == 'draft'

    with context('If overwrite is False'):
        with it('should append the modification'):
            c = Contract()
            m = Modification()
            c.modify(m)
            assert c.modifications[-1] == m

        with it('should assign end date of before modification one day before start date'):
            c = Contract()
            m1 = Modification(date(2014, 1, 1))
            c.modify(m1)
            m2 = Modification(date(2014, 2, 1))
            c.modify(m2)
            assert c.modifications[0].end_date == date(2014, 1, 31)

        with it('should link the two modification'):
            c = Contract()
            m1 = Modification(date(2014, 1, 1))
            c.modify(m1)
            m2 = Modification(date(2014, 2, 1))
            c.modify(m2)
            assert m2.previous == m1
            assert m1.next == m2

        with it('should fail if the start date is before start date of last'):
                c = Contract()
                m = Modification(date(2014, 2, 1))
                c.modify(m)
                m2 = Modification(date(2014, 1, 1))
                with failure:
                    c.modify(m2)

        with it('should get down the current modification'):
            c = Contract()
            m = Modification(date(2014, 1, 1))
            c.modify(m)
            m2 = Modification(date(2015, 1, 1))
            c.modify(m2)
            assert m2.previous.state == 'down'

    with context('If overwrite is True'):
        with it('should overwrite the last modification'):
            c = Contract()
            m1 = Modification()
            c.modify(m1)
            m2 = Modification()
            c.modify(m2, overwrite=True)
            assert len(c.modifications) == 1
            assert c.modifications[-1] == m2
