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
            self.modifications.append(modcontract)
        self.contracted_power = modcontract.contracted_power

    def get_changes(self, modification):
        changes = {}
        local_vals = vars(self)
        mod_vals = vars(modification)
        for attr, value in mod_vals.iteritems():
            if attr in local_vals:
                if value != local_vals[attr]:
                    changes[attr] = {'old': local_vals[attr], 'new': value}
        return changes


class Modification(Contract):
    def __init__(self, start_date=None):
        if start_date is None:
            start_date = date.today()
        self.start_date = start_date
        self.end_date = None
        self.previous = None
        self.next = None
        self.contracted_power = 0
        self.state = 'draft'
