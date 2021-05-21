# -*- coding: utf-8 -*-
import copy

ELECTRIC_ZONES = {
    '1': 'Peninsular',
    '2': 'Balearic Islands',
    '3': 'Canary Islands',
    '4': 'Ceuta',
    '5': 'Melilla',
}

# Tariffs from BOE-A-2020-1066 (https://www.boe.es/eli/es/cir/2020/01/15/3)
TARIFFS_START_DATE_STR = '2021-06-01'

# month/day
DAYTYPE_BY_ELECTRIC_ZONE_CIR03_2020 = {
    # Península
    '1': {
        'A': [('01/01', '02/29'), ('07/01', '07/31'), ('12/01', '12/31')],  # Alta: enero, febrero, julio y diciembre
        'B': [('03/01', '03/31'), ('11/01', '11/30')],  # Media Alta: marzo y noviembre
        'B1': [('06/01', '06/30'), ('08/01', '09/30')],  # Media: junio, agosto y septiembre
        'C': [('04/01', '05/31'), ('10/01', '10/31')],  # Baja: abril, mayo y octubre
        'D': []
    },
    # Balearic Islands
    '2': {
        'A': [('06/01', '09/30')],  # Alta: junio, julio, agosto y septiembre
        'B': [('05/01', '05/31'),  ('10/01', '10/31')],  # Media Alta: mayo y octubre
        'B1': [('01/01', '02/29'), ('12/01', '12/31')],  # Media: enero, febrero y diciembre
        'C': [('03/01', '04/30'), ('11/01', '11/30')],  # Baja: marzo, abril y noviembre
        'D': []
    },
    # Canary Islands
    '3': {
        'A': [('07/01', '10/31')],  # Alta: julio, agosto, septiembre y octubre
        'B': [('11/01', '12/31')],  # Media Alta: noviembre y diciembre
        'B1': [('01/01', '03/31')],  # Media: enero, febrero y marzo
        'C': [('04/01', '06/30')],  # Baja: abril, mayo y junio
        'D': []
    },
    # Ceuta
    '4': {
        'A': [('01/01', '02/29'), ('08/01', '08/31'), ('09/01', '09/30')],  # Alta: enero, febrero, agosto y septiembre
        'B': [('07/01', '07/31'), ('10/01', '10/31')],  # Media Alta: julio y octubre
        'B1': [('03/01', '03/31'), ('11/01', '12/31')],  # Media: marzo, noviembre y diciembre
        'C': [('04/01', '06/30')],  # Baja: abril, mayo y junio
        'D': []
    },
    # Melilla
    '5': {
        'A': [('01/01', '01/31'), ('07/01', '09/30')],  # Alta: enero, julio, agosto y septiembre
        'B': [('02/01', '02/29'), ('12/01', '12/31')],  # Media Alta: febrero y diciembre
        'B1': [('06/01', '06/30'), ('10/01', '11/30')],  # Media: junio, octubre y noviembre
        'C': [('03/01', '05/31')],  # Baja: marzo, abril y mayo
        'D': []
    }
}

# 2 period discrimination for Zone
PERIODS_2x_BY_ELECTRIC_ZONE_CIR03_2020 = {
    # Zone 1: Península
    '1': {
        'A': [
                [(8, 24)],                      # P1
                [(0, 8)]                        # P2
            ],
        'D': [
                [],                             # P1
                [(0, 24)]                         # P2
            ]
        }
    }

# All day types are the same
PERIODS_2x_BY_ELECTRIC_ZONE_CIR03_2020['1'].update(
    {'B': copy.deepcopy(PERIODS_2x_BY_ELECTRIC_ZONE_CIR03_2020['1']['A']),
     'B1': copy.deepcopy(PERIODS_2x_BY_ELECTRIC_ZONE_CIR03_2020['1']['A']),
     'C': copy.deepcopy(PERIODS_2x_BY_ELECTRIC_ZONE_CIR03_2020['1']['A'])}
)
# All 5 Zones are the same
PERIODS_2x_BY_ELECTRIC_ZONE_CIR03_2020.update(
    {'2': copy.deepcopy(PERIODS_2x_BY_ELECTRIC_ZONE_CIR03_2020['1']),
     '3': copy.deepcopy(PERIODS_2x_BY_ELECTRIC_ZONE_CIR03_2020['1']),
     '4': copy.deepcopy(PERIODS_2x_BY_ELECTRIC_ZONE_CIR03_2020['1']),
     '5': copy.deepcopy(PERIODS_2x_BY_ELECTRIC_ZONE_CIR03_2020['1'])}
)

# 3 period discrimination for Zone
PERIODS_3x_BY_ELECTRIC_ZONE_CIR03_2020 = {
    # Zone 1: Península
    '1': {
        'A': [
                [(10, 14), (18, 22)],           # P1
                [(8, 10), (14, 18), (22, 24)],  # P2
                [(0, 8)]                        # P3
            ],
        'D': [
                [],                             # P1
                [],                             # P2
                [(0, 24)]                         # P3

            ]
        },
    '4': {
        'A': [
                [(11, 15), (19, 23)],            # P1
                [(8, 11), (15, 19), (23, 24)],   # P2
                [(0, 8)]                         # P3
            ],
        'D': [
                [],                             # P1
                [],                             # P2
                [(0, 24)]                         # P3

            ]
        }
    }

# All day types are the same
PERIODS_3x_BY_ELECTRIC_ZONE_CIR03_2020['1'].update(
    {'B': copy.deepcopy(PERIODS_3x_BY_ELECTRIC_ZONE_CIR03_2020['1']['A']),
     'B1': copy.deepcopy(PERIODS_3x_BY_ELECTRIC_ZONE_CIR03_2020['1']['A']),
     'C': copy.deepcopy(PERIODS_3x_BY_ELECTRIC_ZONE_CIR03_2020['1']['A'])}
)
PERIODS_3x_BY_ELECTRIC_ZONE_CIR03_2020['4'].update(
    {'B': copy.deepcopy(PERIODS_3x_BY_ELECTRIC_ZONE_CIR03_2020['1']['A']),
     'B1': copy.deepcopy(PERIODS_3x_BY_ELECTRIC_ZONE_CIR03_2020['1']['A']),
     'C': copy.deepcopy(PERIODS_3x_BY_ELECTRIC_ZONE_CIR03_2020['1']['A'])}
)
# Zones 1, 2 and 3 are the same
PERIODS_3x_BY_ELECTRIC_ZONE_CIR03_2020.update(
    {'2': copy.deepcopy(PERIODS_3x_BY_ELECTRIC_ZONE_CIR03_2020['1']),
     '3': copy.deepcopy(PERIODS_3x_BY_ELECTRIC_ZONE_CIR03_2020['1'])}
)
# Zones 4 and 5 are the same
PERIODS_3x_BY_ELECTRIC_ZONE_CIR03_2020.update(
    {'5': copy.deepcopy(PERIODS_3x_BY_ELECTRIC_ZONE_CIR03_2020['4'])}
)

# 6 period discrimination for Zone/dayType
PERIODS_6x_BY_ELECTRIC_ZONE_CIR03_2020 = {
    # Zone 1: Península
    '1': {
        'A': [
            [(9, 14), (18, 22)],            # P1
            [(8, 9), (14, 18), (22, 24)],   # P2
            [],                             # P3
            [],                             # P4
            [],                             # P5
            [(0, 8)]                        # P6
        ],
        'B': [
            [],                             # P1
            [(9, 14), (18, 22)],            # P2
            [(8, 9), (14, 18), (22, 24)],   # P3
            [],                             # P4
            [],                             # P5
            [(0, 8)]                        # P6
        ],
        'B1': [
            [],                             # P1
            [],                             # P2
            [(9, 14), (18, 22)],            # P3
            [(8, 9), (14, 18), (22, 24)],   # P4
            [],                             # P5
            [(0, 8)]                        # P6
        ],
        'C': [
            [],                             # P1
            [],                             # P2
            [],                             # P3
            [(9, 14), (18, 22)],            # P4
            [(8, 9), (14, 18), (22, 24)],   # P5
            [(0, 8)]                        # P6
        ],
        'D': [
            [],                             # P1
            [],                             # P2
            [],                             # P3
            [],                             # P4
            [],                             # P5
            [(0, 24)]                       # P6
        ],
    },
}

# Zone 2: Balearic Islands
PERIODS_6x_BY_ELECTRIC_ZONE_CIR03_2020.update(
    {'2': copy.deepcopy(PERIODS_6x_BY_ELECTRIC_ZONE_CIR03_2020['1'].copy())}
)
# A: P1 and P2 are different from Zone 1
PERIODS_6x_BY_ELECTRIC_ZONE_CIR03_2020['2']['A'][0] = [(10, 15), (18, 22)]
PERIODS_6x_BY_ELECTRIC_ZONE_CIR03_2020['2']['A'][1] = [(8, 10), (15, 18), (22, 24)]
# B: P2 and P3 are different from Zone 1
PERIODS_6x_BY_ELECTRIC_ZONE_CIR03_2020['2']['B'][1] = [(10, 15), (18, 22)]
PERIODS_6x_BY_ELECTRIC_ZONE_CIR03_2020['2']['B'][2] = [(8, 10), (15, 18), (22, 24)]
# B1: P3 and P4 are different from Zone 1
PERIODS_6x_BY_ELECTRIC_ZONE_CIR03_2020['2']['B1'][2] = [(10, 15), (18, 22)]
PERIODS_6x_BY_ELECTRIC_ZONE_CIR03_2020['2']['B1'][3] = [(8, 10), (15, 18), (22, 24)]
# C: P4 and P5 are different from Zone 1
PERIODS_6x_BY_ELECTRIC_ZONE_CIR03_2020['2']['C'][3] = [(10, 15), (18, 22)]
PERIODS_6x_BY_ELECTRIC_ZONE_CIR03_2020['2']['C'][4] = [(8, 10), (15, 18), (22, 24)]

# Zone 3: Canary Islands
PERIODS_6x_BY_ELECTRIC_ZONE_CIR03_2020.update(
    {'3': copy.deepcopy(PERIODS_6x_BY_ELECTRIC_ZONE_CIR03_2020['2'])}
)
# A: P2 and P3 are different from Zone 2
PERIODS_6x_BY_ELECTRIC_ZONE_CIR03_2020['3']['A'][1] = []
PERIODS_6x_BY_ELECTRIC_ZONE_CIR03_2020['3']['A'][2] = [(8, 10), (15, 18), (22, 24)]
# B1: P2 and P3 are different from Zone 2
PERIODS_6x_BY_ELECTRIC_ZONE_CIR03_2020['3']['B1'][1] = [(10, 15), (18, 22)]
PERIODS_6x_BY_ELECTRIC_ZONE_CIR03_2020['3']['B1'][2] = []

# Zone 4: Ceuta
PERIODS_6x_BY_ELECTRIC_ZONE_CIR03_2020.update(
    {'4': copy.deepcopy(PERIODS_6x_BY_ELECTRIC_ZONE_CIR03_2020['3'])}
)
# A: P1, P3 and P4 are different from Zone 3
PERIODS_6x_BY_ELECTRIC_ZONE_CIR03_2020['4']['A'][0] = [(10, 15), (19, 23)]
PERIODS_6x_BY_ELECTRIC_ZONE_CIR03_2020['4']['A'][2] = []
PERIODS_6x_BY_ELECTRIC_ZONE_CIR03_2020['4']['A'][3] = [(8, 10), (15, 19), (23, 24)]
# B: P2 and P3 are different from Zone 3
PERIODS_6x_BY_ELECTRIC_ZONE_CIR03_2020['4']['B'][1] = [(10, 15), (19, 23)]
PERIODS_6x_BY_ELECTRIC_ZONE_CIR03_2020['4']['B'][2] = [(8, 10), (15, 19), (23, 24)]
# B1: P2 and P4 are different from Zone 3
PERIODS_6x_BY_ELECTRIC_ZONE_CIR03_2020['4']['B1'][1] = [(10, 15), (19, 23)]
PERIODS_6x_BY_ELECTRIC_ZONE_CIR03_2020['4']['B1'][3] = [(8, 10), (15, 19), (23, 24)]
# C: P3, P4 and P5 are different from Zone 3
PERIODS_6x_BY_ELECTRIC_ZONE_CIR03_2020['4']['C'][2] = [(10, 15), (19, 23)]
PERIODS_6x_BY_ELECTRIC_ZONE_CIR03_2020['4']['C'][3] = []
PERIODS_6x_BY_ELECTRIC_ZONE_CIR03_2020['4']['C'][4] = [(8, 10), (15, 19), (23, 24)]

# Zone 5: Melilla
PERIODS_6x_BY_ELECTRIC_ZONE_CIR03_2020.update(
    {'5': copy.deepcopy(PERIODS_6x_BY_ELECTRIC_ZONE_CIR03_2020['4'])}
)
# A: P2 and P4 are different from Zone 4
PERIODS_6x_BY_ELECTRIC_ZONE_CIR03_2020['5']['A'][1] = [(8, 10), (15, 19), (23, 24)]
PERIODS_6x_BY_ELECTRIC_ZONE_CIR03_2020['5']['A'][3] = []
# B1: P2 and P3 are different from Zone 4
PERIODS_6x_BY_ELECTRIC_ZONE_CIR03_2020['5']['B1'][1] = []
PERIODS_6x_BY_ELECTRIC_ZONE_CIR03_2020['5']['B1'][2] = [(10, 15), (19, 23)]
# C: P3 and P4 are different from Zone 4
PERIODS_6x_BY_ELECTRIC_ZONE_CIR03_2020['5']['C'][2] = []
PERIODS_6x_BY_ELECTRIC_ZONE_CIR03_2020['5']['C'][3] = [(10, 15), (19, 23)]

# Old tariffs from BOE-A-2001-20850 (https://www.boe.es/eli/es/rd/2001/10/26/1164)
# month/day
DAYTYPE_BY_ELECTRIC_ZONE = {
    # Península
    '1': {
        'A': [('01/01', '02/29'), ('12/01', '12/31')],
        'A1': [('06/16', '07/31')],
        'B': [('06/01', '06/15'), ('09/01', '09/30')],
        'B1': [('03/01', '03/31'), ('11/01', '11/30')],
        'C': [('04/01', '05/31'), ('10/01', '10/31')],
        'D': [('08/01', '08/31')]
    },
    # Balearic Islands
    '2': {
        'A': [('06/01', '09/30')],
        'B1': [('01/01', '02/29'), ('05/01', '05/31'), ('10/01', '10/31')],
        'C': [('03/01', '03/31'), ('11/01', '12/31')],
        'D': [('04/01', '04/30')]
    },
    # Canary Islands
    '3': {
        'A': [('09/01', '12/31')],
        'B': [('07/01', '08/31')],
        'B1': [('01/01', '02/29')],
        'C': [('03/01', '04/30'), ('06/01', '06/30')],
        'D': [('05/01', '05/31')]
    },
    # Ceuta
    '4': {
        'A': [('01/01', '02/29'), ('08/01', '08/31'), ('12/01', '12/31')],
        'B': [('07/01', '07/31'), ('09/01', '09/30')],
        'B1': [('03/01', '03/31'), ('11/01', '11/30')],
        'C': [('04/01', '04/30'), ('06/01', '06/30'), ('10/01', '10/31')],
        'D': [('05/01', '05/31')]
    },
    # Melilla
    '5': {
        'A': [('01/01', '02/29')],
        'A1': [('07/01', '08/31')],
        'B': [('06/01', '06/30'), ('09/01', '09/30')],
        'B1': [('03/01', '03/31'), ('12/01', '12/31')],
        'C': [('04/01', '04/30'), ('10/01', '11/30')],
        'D': [('05/01', '05/31')]
    }
}

# 6 periods for Zone/dayType
PERIODS_6x_BY_ELECTRIC_ZONE = {
    # Zone 1: Península
    '1': {
        'A': [
            [(10, 13), (18, 21)],               # P1
            [(8, 10), (13, 18), (21, 24)],      # P2
            [],                                 # P3
            [],                                 # P4
            [],                                 # P5
            [(0, 8)],                           # P6
        ],
        'A1': [
            [(11, 19)],
            [(8, 11), (19, 24)],
            [],
            [],
            [],
            [(0, 8)],
        ],
        'B': [
            [],
            [],
            [(9, 15)],
            [(8, 9), (15, 24)],
            [],
            [(0, 8)],
        ],
        'B1': [
            [],
            [],
            [(16, 22)],
            [(8, 16), (22, 24)],
            [],
            [(0, 8)],
        ],
        'C': [
            [],
            [],
            [],
            [],
            [(8, 24)],
            [(0, 8)],
        ],
        'D': [
            [],
            [],
            [],
            [],
            [],
            [(0, 24)],
        ],
    },
}

# Zone 2 and 3: Balearic and Canary Islands
PERIODS_6x_BY_ELECTRIC_ZONE.update(
    {'2': copy.deepcopy(PERIODS_6x_BY_ELECTRIC_ZONE['1'].copy())}
)
# A:P1 and A:P2
PERIODS_6x_BY_ELECTRIC_ZONE['2']['A'][0] = [(11, 14), (18, 21)]
PERIODS_6x_BY_ELECTRIC_ZONE['2']['A'][1] = [(8, 11), (14, 18), (21, 24)]
# Zone 3 == Zone 2
PERIODS_6x_BY_ELECTRIC_ZONE.update(
    {'3': copy.deepcopy(PERIODS_6x_BY_ELECTRIC_ZONE['2'])}
)

# Zone 4: Ceuta
PERIODS_6x_BY_ELECTRIC_ZONE.update(
    {'4': copy.deepcopy(PERIODS_6x_BY_ELECTRIC_ZONE['1'])}
)
# A:P1 and A:P2
PERIODS_6x_BY_ELECTRIC_ZONE['4']['A'][0] = [(12, 15), (20, 23)]
PERIODS_6x_BY_ELECTRIC_ZONE['4']['A'][1] = [(8, 12), (15, 20), (23, 24)]

# B1:P3 and B1:P4
PERIODS_6x_BY_ELECTRIC_ZONE['4']['B1'][2] = [(17, 23)]
PERIODS_6x_BY_ELECTRIC_ZONE['4']['B1'][3] = [(8, 17), (23, 24)]

# Zone 5: Melilla
PERIODS_6x_BY_ELECTRIC_ZONE.update(
    {'5': copy.deepcopy(PERIODS_6x_BY_ELECTRIC_ZONE['4'])}
)
