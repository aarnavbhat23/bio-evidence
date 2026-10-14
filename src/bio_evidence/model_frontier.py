"""Measured frontiers with explicit comparability contracts."""
from collections import defaultdict
from statistics import mean
from ._validation import need, number, unique_ids

def dominates(a, b):
    costs = ('latency_ms', 'peak_memory_mb', 'cost_usd')
    weak = a['quality'] >= b['quality'] and all(a[k] <= b[k] for k in costs)
    strict = a['quality'] > b['quality'] or any(a[k] < b[k] for k in costs)
    return weak and strict

def analyze(data):
    """Filter measured configurations by resource constraints and compute comparable frontiers."""
    need(data, 'runs')
    groups = defaultdict(list)
    limits = data.get('limits', {})
    for key in limits:
        if key not in ('latency_ms', 'peak_memory_mb', 'cost_usd', 'min_quality'):
            raise ValueError('Unknown limit: ' + key)
        number(limits[key])
    for r in data['runs']:
        need(r, 'id', 'task', 'dataset_sha256', 'hardware', 'measurement_protocol', 'metric', 'quality', 'latencies_ms', 'peak_memory_mb', 'cost_usd')
        if not r['latencies_ms']:
            raise ValueError('Require measured latency samples')
        values = [number(x) for x in r['latencies_ms']]
        if any(x <= 0 for x in values):
            raise ValueError('Latencies must be positive')
        if number(r['peak_memory_mb']) < 0 or number(r['cost_usd']) < 0:
            raise ValueError('Resource use cannot be negative')
        quality = number(r['quality'])
        row = {'id': r['id'], 'quality':quality, 'latency_ms': mean(values),
               'n_latency_samples': len(values), 'peak_memory_mb': number(r['peak_memory_mb']),
               'cost_usd': number(r['cost_usd'])}
        row['eligible'] = all(row[k] <= number(v) for k,v in limits.items() if k != 'min_quality') and quality >= number(limits.get('min_quality', quality))
        key = tuple(r[k] for k in ('task','dataset_sha256','hardware','measurement_protocol','metric'))
        if not all(isinstance(x,str) and x.strip() for x in key):
            raise ValueError('Comparability metadata must be nonempty strings')
        groups[key].append(row)
    unique_ids(data['runs'])
    reports = []
    for key, rows in sorted(groups.items()):
        eligible = [r for r in rows if r['eligible']]
        for row in rows:
            row['on_frontier'] = row['eligible'] and not any(dominates(other,row) for other in eligible)
        reports.append({'comparison_contract': dict(zip(('task','dataset_sha256','hardware','measurement_protocol','metric'),key)),
                        'runs':rows, 'frontier_ids':[r['id'] for r in rows if r['on_frontier']]})
    return {'groups': reports, 'limits': limits,
            'interpretation': 'Quality must be higher-is-better. Different contracts are never ranked together. Sample means alone do not establish statistical dominance; repeat runs and quantify uncertainty before claiming a winner.'}

