from datetime import date, timedelta


CONTRACT_STATES = [
    'draft',
    'validate',
    'pending',
    'active',
    'contract',
    'new_contract',
    'modcontract',
    'unpayed',
    'off',
    'down'
]


class Interval(object):
    def __init__(self, start, end, modification, changes):
        self.start = start
        self.end = end
        self.modification = modification
        self.changes = changes


class Contract(object):
    """Contract object.
    """
    def __init__(self):
        self.code = None
        self.state = 'draft'
        self.modifications = []
        self.contracted_power = 0

    def modify(self, modcontract, overwrite=False):
        assert isinstance(modcontract, Modification)
        if overwrite:
            self.modifications[-1] = modcontract
        else:
            if self.modifications:
                old_mod = self.modifications[-1]
                assert modcontract.start_date > old_mod.start_date
                old_mod.end_date = modcontract.start_date - timedelta(days=1)
                old_mod.next = modcontract
                modcontract.previous = old_mod
                old_mod.state = 'down'
                modcontract.version = old_mod.version + 1
            self.modifications.append(modcontract)
        self.apply_modification(modcontract)

    def get_modifications(self, start_date, end_date):
        mods = []
        # Get the modifications between dates
        for m in self.modifications:
            if m.start_date <= start_date and (
                    m.end_date is None or m.end_date >= end_date):
                mods.append(m)
            elif start_date <= m.start_date <= end_date:
                mods.append(m)
        return mods

    def get_intervals(self, start_date, end_date, changes=None):
        intervals = []
        previous_mod = None
        for m in self.get_modifications(start_date, end_date):
            diff = {}
            if previous_mod:
                diff = previous_mod.diff(m, changes)
            if diff or previous_mod is None:
                mod_end_date = m.end_date or end_date
                interval = Interval(
                    start=max(start_date, m.start_date),
                    end=min(mod_end_date, end_date),
                    changes=diff,
                    modification=m
                )
                intervals.append(interval)
            else:
                intervals[-1].end = min(m.end_date, end_date)
            previous_mod = m
        return intervals

    def get_changes(self, modification):
        changes = {}
        local_vals = vars(self)
        mod_vals = vars(modification)
        for attr, value in mod_vals.iteritems():
            if attr in local_vals:
                if value != local_vals[attr]:
                    changes[attr] = {'old': local_vals[attr], 'new': value}
        return changes

    def apply_changes(self, changes):
        for attr, value in changes.iteritems():
            setattr(self, attr, value['new'])

    def apply_modification(self, modification):
        changes = self.get_changes(modification)
        self.apply_changes(changes)


class Modification(object):
    def __init__(self, start_date=None):
        if start_date is None:
            start_date = date.today()
        self.start_date = start_date
        self.end_date = None
        self.previous = None
        self.next = None
        self.contracted_power = 0
        self.state = 'draft'
        self.version = 1

    def diff(self, modification, filter=None):
        changes = {}
        local_vals = vars(self)
        if modification is None:
            mod_vals = local_vals.copy()
        else:
            mod_vals = vars(modification)
        if filter is not None:
            mod_vals = dict((k, v) for k, v in mod_vals.items() if k in filter)
        for attr, value in mod_vals.iteritems():
            if attr in local_vals:
                if value != local_vals[attr]:
                    changes[attr] = {'old': local_vals[attr], 'new': value}
        return changes