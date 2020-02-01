player = {'name': 'T. Ross', 'min': '31', 'fg': '8-17', '3pt': '6-13', 'ft': '4-4', 'oreb': '0', 'dreb': '4', 'reb': '4', 'ast': '0', 'stl': '1', 'blk': '0', 'to': '0', 'pf': '0', 'plusminus': '+11', 'pts': '26'}

values = {
    'pts': {
        'mean': 15.7,
        'std': 5.97
    },
    'reb': {
        'mean': 6.29,
        'std': 2.68
    },
    'ast': {
        'mean': 3.31,
        'std': 2.16
    },
    'stl': {
        'mean': 0.99,
        'std': 0.39
    },
    'blk': {
        'mean': 0.7,
        'std': 0.56
    },
    '3pt': {
        'mean': 1.59,
        'std': 1.02
    }
}

def value_cat(cat, stat):
    mean = values[cat]['mean']
    std = values[cat]['std']
    if cat == '3pt': stat = float(stat.split('-')[0])
    else: stat = float(stat)
    return (stat - mean) / std


def value_log(log):
    val = 0
    for i in log:
        try:
            #print('i: ', i)
            #print('log[i]: ', log[i])
            #print(value_cat(str(i), log[i]))
            val += value_cat(i, log[i])
            #print(i, ": ", val)
        except Exception as ex:
            #print(ex)
            pass
    return val
