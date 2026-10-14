"""Metrics over precomputed, independently split perturbation predictions."""
from collections import defaultdict
import numpy as np
from ._validation import need, number, unique_ids

def metrics(rows, threshold):
    true = np.array([r['observed_effect'] for r in rows], dtype=float)
    pred = np.array([r['predicted_effect'] for r in rows], dtype=float)
    eligible = np.abs(true) > threshold
    observed_sign = np.sign(true[eligible])
    predicted_sign = np.where(np.abs(pred[eligible]) > threshold, np.sign(pred[eligible]), 0)
    zero_mae = float(np.mean(np.abs(true)))
    mae = float(np.mean(np.abs(pred-true)))
    return {'n': len(rows), 'mae': mae, 'zero_effect_mae': zero_mae,
            'mae_skill_vs_zero': 1-mae/zero_mae if zero_mae else None,
            'n_observed_above_threshold': int(eligible.sum()),
            'sign_accuracy_on_observed_effects': float(np.mean(predicted_sign == observed_sign)) if eligible.any() else None,
            'predicted_neutral_on_observed_effects': int((predicted_sign == 0).sum())}

def analyze(data):
    """Measure sign recovery by context and error relative to predicting no effect."""
    need(data, 'rows', 'effect_threshold', 'effect_units')
    threshold = number(data['effect_threshold'])
    if threshold < 0 or not data['effect_units']:
        raise ValueError('Require nonnegative threshold and explicit effect units')
    rows = data['rows']
    if not rows:
        raise ValueError('At least one observed/predicted effect is required')
    for r in rows:
        need(r, 'id', 'context', 'gene', 'perturbation', 'observed_effect', 'predicted_effect')
        number(r['observed_effect']); number(r['predicted_effect'])
    unique_ids(rows)
    contexts = defaultdict(list)
    for r in rows:
        contexts[r['context']].append(r)
    macro = [metrics(group, threshold) for group in contexts.values()]
    return {'effect_units': data['effect_units'], 'effect_threshold': threshold,
            'pooled': metrics(rows, threshold),
            'by_context': {k: metrics(v, threshold) for k,v in sorted(contexts.items())},
            'context_macro_mae': float(np.mean([m['mae'] for m in macro])),
            'interpretation': 'Threshold must be fixed before evaluation in these effect units. Input rows can be correlated; no rowwise significance claims. Precomputed effects and independent train/test separation are caller responsibilities.'}

