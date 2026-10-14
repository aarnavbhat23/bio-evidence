"""Concentration normalization preserves inequality signs and chemistry metadata."""
import re
from collections import defaultdict
from ._validation import need, number, unique_ids

MEASUREMENT = re.compile(r'^\s*(<=|>=|<|>|=)?\s*([0-9]+(?:\.[0-9]*)?(?:[eE][+-]?[0-9]+)?)\s*([^\s]+)\s*$')

def parse_measurement(text):
    """Parse a concentration with its unit; retain the direction of censoring."""
    if text is None or str(text).strip() in ('','NA','ND'):
        return None
    match = MEASUREMENT.fullmatch(str(text).replace('≤','<=').replace('≥','>='))
    if not match:
        return None
    operator, value, unit = match.groups()
    unit = unit.replace('μ','u').replace('µ','u')
    value = number(value)
    return {'operator':operator or '=', 'value':value, 'unit':unit}

def threshold_label(text, threshold=16.0, unit='uM'):
    """Label C <= threshold only when a reported exact value/bound decides it.

    Return None for missing, unsupported units, or bounds spanning the threshold.
    No molecular weight is inferred from a peptide's letter sequence.
    """
    measurement = parse_measurement(text)
    if measurement is None:
        return None
    threshold = number(threshold)
    if threshold < 0:
        raise ValueError('Threshold must be nonnegative')
    families = {'uM':{'uM':1,'nM':.001,'mM':1000,'M':1e6},
                'ug/mL':{'ug/mL':1,'mg/L':1,'ng/mL':.001,'g/L':1000}}
    factors = families.get(unit, {})
    if measurement['unit'] not in factors:
        return None
    value = measurement['value'] * factors[measurement['unit']]
    op = measurement['operator']
    if op == '=':
        return int(value <= threshold)
    if op in ('<','<=') and value <= threshold:
        return 1
    if (op == '>' and value >= threshold) or (op == '>=' and value > threshold):
        return 0
    return None

VALUE = re.compile(r'^\s*(<=|>=|<|>|=)?\s*([0-9]+(?:\.[0-9]*)?(?:[eE][+-]?[0-9]+)?)\s*$')

def normalize(row):
    need(row, 'id', 'value', 'unit', 'sequence', 'chemistry', 'source', 'organism', 'condition')
    value = row['value']
    if value is None or str(value).strip() in ('', 'NA', 'ND'):
        return {'id': row['id'], 'status': 'missing', 'mg_per_L': None, 'operator': None}
    match = VALUE.fullmatch(str(value))
    if not match:
        return {'id': row['id'], 'status': 'manual_review', 'reason': 'Unrecognized value or range'}
    op, raw = match.groups()
    amount = number(raw)
    unit = row['unit'].replace('μ', 'u').replace('µ', 'u').strip()
    factors = {'mg/L': 1, 'ug/mL': 1, 'ng/mL': .001, 'g/L': 1000}
    if unit in ('uM', 'nM', 'mM', 'M'):
        if row.get('molecular_weight_g_mol') is None:
            return {'id': row['id'], 'status': 'manual_review', 'reason': 'Molar unit needs chemistry-specific molecular weight'}
        mw = number(row['molecular_weight_g_mol'])
        if mw <= 0:
            raise ValueError('Molecular weight must be positive')
        factor = {'uM': .001, 'nM': .000001, 'mM': 1, 'M': 1000}[unit] * mw
    elif unit in factors:
        factor = factors[unit]
    else:
        return {'id': row['id'], 'status': 'manual_review', 'reason': 'Unsupported unit'}
    return {'id': row['id'], 'status': 'exact' if op in (None, '=') else 'censored',
            'mg_per_L': amount * factor, 'operator': op or '=',
            'chemistry': row['chemistry'], 'source': row['source']}

def analyze(data):
    """Normalize assay units and flag repeated source/chemistry/organism/condition keys."""
    need(data, 'rows')
    out = [normalize(r) for r in data['rows']]
    unique_ids(data['rows'])
    groups = defaultdict(list)
    for row in data['rows']:
        key = tuple(row[k] for k in ('sequence','chemistry','source','organism','condition'))
        groups[key].append(row['id'])
    return {'records': out,
            'counts': {s: sum(r['status'] == s for r in out) for s in ('exact','censored','missing','manual_review')},
            'repeated_assay_keys': [ids for ids in groups.values() if len(ids)>1],
            'interpretation': 'Repeated keys need review; biological replicates may be valid. A censored value is a bound, never an exact concentration.'}

