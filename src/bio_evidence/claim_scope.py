"""Human-labeled scope evaluation; quote validation is separate from entailment."""
from collections import Counter
from ._validation import need, unique_ids

LABELS = ('supported', 'contradicted', 'insufficient')

def score(gold, predicted):
    confusion = Counter(zip(gold, predicted))
    f1 = {}
    for label in LABELS:
        tp = confusion[(label,label)]
        fp = sum(g != label and p == label for g,p in zip(gold,predicted))
        fn = sum(g == label and p != label for g,p in zip(gold,predicted))
        f1[label] = 2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else 0.0
    return {'n': len(gold), 'accuracy': sum(g == p for g,p in zip(gold,predicted))/len(gold),
            'macro_f1_fixed_three_labels': sum(f1.values())/3,
            'per_label_f1': f1, 'gold_label_counts': dict(Counter(gold)),
            'confusion': [{'gold':g,'prediction':p,'n':n} for (g,p),n in sorted(confusion.items())]}

def analyze(data):
    """Score claim labels, verified quote occurrence and per-scope errors."""
    need(data, 'cases', 'predictions')
    cases, predictions = data['cases'], data['predictions']
    if not cases:
        raise ValueError('At least one labeled case is required')
    for c in cases:
        need(c, 'id', 'claim', 'evidence', 'source_id', 'scope', 'gold')
        if c['gold'] not in LABELS:
            raise ValueError('gold must be supported, contradicted or insufficient')
    for p in predictions:
        need(p, 'id', 'label', 'quote')
        if p['label'] not in LABELS + ('abstain',) or not isinstance(p['quote'],str):
            raise ValueError('Invalid prediction label or quote')
    unique_ids(cases); unique_ids(predictions)
    by_id = {p['id']:p for p in predictions}
    if set(by_id) != {c['id'] for c in cases}:
        raise ValueError('Prediction IDs must cover the cases exactly')
    ledger = []
    for c in cases:
        p = by_id[c['id']]
        occurs = bool(p['quote'].strip()) and p['quote'] in c['evidence']
        # Requiring a valid quote reduces unsupported confident outputs, but does
        # not certify that a real quote supports the predicted classification.
        guarded = p['label'] if occurs or p['label'] == 'abstain' else 'abstain'
        ledger.append({'id': c['id'], 'scope': c['scope'], 'gold':c['gold'],
                       'raw_label':p['label'], 'quote_occurs':occurs, 'guarded_label':guarded,
                       'quote':p['quote'], 'source_id':c['source_id']})
    gold = [r['gold'] for r in ledger]
    return {'raw_metrics': score(gold,[r['raw_label'] for r in ledger]),
            'quote_guarded_metrics': score(gold,[r['guarded_label'] for r in ledger]),
            'guarded_coverage': sum(r['guarded_label'] != 'abstain' for r in ledger)/len(ledger),
            'invalid_or_empty_quote_rate': sum(not r['quote_occurs'] for r in ledger)/len(ledger),
            'by_scope': {s: score([r['gold'] for r in ledger if r['scope']==s],
                                  [r['guarded_label'] for r in ledger if r['scope']==s]) for s in sorted({r['scope'] for r in ledger})},
            'ledger': ledger,
            'interpretation': 'Gold labels must be reviewed by humans. Exact substring occurrence confirms provenance only. Fixed three-label macro-F1 includes absent classes as zero; report class counts.'}

