# -*- coding: utf-8 -*-
from enerdata.contracts.contract import *
from expects.testing import failure
from mamba import description, it, before, context


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

    with it('should create with code 1'):
        m = Modification()
        assert m.version == 1

    with it('should create in draft state'):
        m = Modification()
        assert m.state == 'draft'

with description('A contract'):
    with it('should return the modifications of intervals'):
        c = Contract()
        m1 = Modification(date(2014, 1, 1))
        m1.contracted_power = 10
        c.modify(m1)
        m2 = Modification(date(2014, 2, 1))
        m2.contracted_power = 11.5
        c.modify(m2)
        m3 = Modification(date(2014, 3, 1))
        m3.contracted_pwoer = 11.5
        c.modify(m3)
        assert len(c.modifications) == 3
        mods = c.get_modifications(date(2013, 1, 1), date(2014, 1, 6))
        assert len(mods) == 1
        assert mods == [m1]
        mods = c.get_modifications(date(2014, 1, 1), date(2014, 1, 31))
        assert len(mods) == 1
        assert mods == [m1]
        mods = c.get_modifications(date(2014, 1, 1), date(2014, 2, 1))
        assert len(mods) == 2
        assert mods == [m1, m2]
        mods = c.get_modifications(date(2014, 1, 1), date(2014, 3, 1))
        assert len(mods) == 3
        assert mods == [m1, m2, m3]
        mods = c.get_modifications(date(2014, 3, 3), date(2014, 3, 7))
        assert len(mods) == 1
        assert mods == [m3]
        mods = c.get_modifications(date(2020, 1, 1), date(2020, 1, 31))
        assert len(mods) == 1
        assert mods == [m3]
        mods = c.get_modifications(date(2013, 1, 1), date(2013, 1, 31))
        assert len(mods) == 0
        assert mods == []

    with context('Getting intervals of modificatins'):
        with before.all:
            self.c = Contract()
            m1 = Modification(date(2014, 1, 1))
            m1.contracted_power = 10
            self.c.modify(m1)
            m2 = Modification(date(2014, 2, 1))
            m2.contracted_power = 11.5
            self.c.modify(m2)
            m3 = Modification(date(2014, 3, 1))
            m3.contracted_power = 11.5
            self.c.modify(m3)
            m4 = Modification(date(2015, 1, 3))
            m4.contracted_power = 15
            self.c.modify(m4)
        with context('If not filter of changes is passed'):
            with it('should return the intervals of modifications between dates'):
                assert len(self.c.modifications) == 4
                mods = self.c.get_intervals(date(2013, 12, 1), date(2014, 1, 6))
                assert len(mods) == 1
                mods = self.c.get_intervals(date(2013, 12, 1), date(2014, 2, 26))
                assert len(mods) == 2
                assert mods[0].start == date(2014, 1, 1)
                assert mods[-1].end == date(2014, 2, 26)
        with context('If filter of changes is passed'):
            with it('should return only the intervals of modifcations which changes wiht filter'):
                assert len(self.c.modifications) == 4
                mods = self.c.get_intervals(date(2013, 12, 1), date(2014, 3, 26), ['contracted_power'])
                assert len(mods) == 2
                assert mods[0].start == date(2014, 1, 1)
                assert mods[-1].end == date(2014, 3, 26)

            with it('shouldn\'t have gaps between dates'):
                assert len(self.c.modifications) == 4
                mods = self.c.get_intervals(date(2013, 12, 1), date(2015, 12, 1), ['contracted_power'])
                assert len(mods) == 3
                assert mods[0].start == date(2014, 1, 1)
                assert mods[0].end == date(2014, 1, 31)
                assert mods[1].start == date(2014, 2, 1)
                assert mods[1].end == date(2015, 1, 2)
                assert mods[2].start == date(2015, 1, 3)
                assert mods[2].end == date(2015, 12, 1)

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

    with it('should apply changes'):
        c = Contract()
        c.contracted_power = 1
        m = Modification()
        m.contracted_power = 10
        changes = c.get_changes(m)
        c.apply_changes(changes)
        assert c.contracted_power == 10

    with it('should apply a modification'):
        c = Contract()
        c.contracted_power = 1
        m = Modification()
        m.contracted_power = 10
        c.apply_modification(m)
        assert c.contracted_power == 10

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

        with it('should increment the code of the modcontractual if has a previous modification'):
            c = Contract()
            m = Modification(date(2014, 1, 1))
            c.modify(m)
            m2 = Modification(date(2015, 1, 1))
            c.modify(m2)
            assert m2.version == m.version + 1

    with context('If overwrite is True'):
        with it('should overwrite the last modification'):
            c = Contract()
            m1 = Modification()
            c.modify(m1)
            m2 = Modification()
            c.modify(m2, overwrite=True)
            assert len(c.modifications) == 1
            assert c.modifications[-1] == m2

with description('A modification'):
    with it('should detectect the diferences'):
        m = Modification(date(2014, 1, 1))
        m.contracted_power = 10
        m2 = Modification(date(2015, 1, 1))
        m2.contracted_power = 14
        diff = m.diff(m2)
        result = {
            'contracted_power': {'old': 10, 'new': 14},
            'start_date': {'old': date(2014, 1, 1), 'new': date(2015, 1, 1)}}
        assert diff == result
    with it('not should return differences if modifcation is None'):
        m = Modification(date(2014, 1, 1))
        m.contracted_power = 10
        diff = m.diff(None)
        assert diff == {}
