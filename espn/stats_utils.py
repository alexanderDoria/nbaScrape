import numpy as np

values = {
    'pts': {
        'mean': 15.7,
        'sd': 5.97
    },
    'reb': {
        'mean': 6.29,
        'sd': 2.68
    },
    'ast': {
        'mean': 3.31,
        'sd': 2.16
    },
    'stl': {
        'mean': 0.99,
        'sd': 0.39
    },
    'blk': {
        'mean': 0.7,
        'sd': 0.56
    },
    'threepm': {
        'mean': 1.59,
        'sd': 1.02
    },
    'to': {
        'mean': -1.92,
        'sd': 0.917
    },
    'fgm/a': {
        'pct': 0.469,
        'mean': 0.000454,
        'sd': 0.054213,
        'a': 12.2
    },
    'ftm/a': {
        'pct': 0.794,
        'mean': -0.000951,
        'sd': 0.107100,
        'a': 3.357
    }
}

def value_pct(cat, stat):
    m = float(stat.split('/')[0])
    a = float(stat.split('/')[1])
    return ((m / a) - values[cat]['pct']) * (a / values[cat]['a'])
    

def value_cat(cat, stat):
    mean = values[cat]['mean']
    sd = values[cat]['sd']
    if '/' in cat: 
        stat = value_pct(cat, stat)
    elif cat == 'threepm': 
        stat = float(stat.split('-')[0])
    elif cat == 'to':
        stat = float(stat) * -1
    else: 
        stat = float(stat)
    return (stat - mean) / sd


def value_log(log):
    val = 0
    for i in log:
        try:
            v = value_cat(i, log[i])
            if i in ('pts', 'reb', 'ast'):
                v *= 1.15
            elif i in ('stl', 'blk'):
                v *= 0.85
            elif i in ('fgm/a', 'ftm/a', 'to'):
                v *= 0.7
            val += v
            #print('i: ', i)
            #print('log[i]: ', log[i])
            #print("z", ": ", v)
            #print()
        except Exception as ex:
            #print(ex)
            pass
    return round(val, 3)
