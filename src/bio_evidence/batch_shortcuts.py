"""Diagnostic replicate retrieval and compound-held-out batch classification."""
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from ._validation import need, unique_ids

def retrieval(rows, x, cross_batch):
    norm = np.linalg.norm(x, axis=1)
    xn = x / norm[:,None]
    similarity = xn @ xn.T
    hits, chance, ledger = [], [], []
    for i, row in enumerate(rows):
        candidates = [j for j,r in enumerate(rows) if j != i and
                      ((r['batch'] != row['batch']) if cross_batch else (r['batch'] == row['batch']))]
        if not candidates or not any(rows[j]['perturbation'] == row['perturbation'] for j in candidates):
            continue  # report eligibility explicitly; never count impossible queries as misses
        winner = max(candidates, key=lambda j: similarity[i,j])
        hit = rows[winner]['perturbation'] == row['perturbation']
        baseline = sum(rows[j]['perturbation'] == row['perturbation'] for j in candidates)/len(candidates)
        hits.append(hit); chance.append(baseline)
        ledger.append({'id': row['id'], 'nearest_id': rows[winner]['id'], 'hit': hit, 'random_candidate_hit_rate': baseline})
    return {'n_eligible': len(hits), 'n_ineligible': len(rows)-len(hits),
            'top1_hit_rate': float(np.mean(hits)) if hits else None,
            'random_candidate_hit_rate': float(np.mean(chance)) if chance else None,
            'queries': ledger}

def analyze(data):
    """Contrast within/cross-batch replicate retrieval and held-out-compound batch prediction."""
    need(data, 'rows')
    rows = data['rows']
    for r in rows:
        need(r, 'id', 'batch', 'perturbation', 'features')
        if any(not isinstance(r[k],str) or not r[k].strip() for k in ('batch','perturbation')):
            raise ValueError('Batch and perturbation labels must be nonempty strings')
    unique_ids(rows)
    x = np.asarray([r['features'] for r in rows], dtype=float)
    if x.ndim != 2 or len(rows)<3 or x.shape[1]<1 or not np.isfinite(x).all() or np.any(np.linalg.norm(x,axis=1) == 0):
        raise ValueError('Require >=3 rows with finite nonzero feature vectors')
    batches = np.array([r['batch'] for r in rows])
    groups = np.array([r['perturbation'] for r in rows])
    warning = []
    per_group = {g: sorted(set(batches[groups == g])) for g in set(groups)}
    if any(len(v) == 1 for v in per_group.values()):
        warning.append('Some perturbations occur in only one batch; batch and biological identity may be confounded.')
    predictions, truths, baselines, folds = [], [], [], []
    if len(set(groups)) >= 2 and len(set(batches)) >= 2:
        cv = GroupKFold(n_splits=min(3, len(set(groups))))
        for train, test in cv.split(x, batches, groups):
            if len(set(batches[train])) < 2:
                warning.append('Skipped batch-classifier fold: training contains only one batch.')
                continue
            model = make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000, random_state=0))
            model.fit(x[train], batches[train])
            predictions.extend(model.predict(x[test])); truths.extend(batches[test])
            labels, counts = np.unique(batches[train], return_counts=True)
            baselines.extend([labels[np.argmax(counts)]] * len(test))
            folds.append({'train_perturbations': sorted(set(groups[train])), 'test_perturbations': sorted(set(groups[test]))})
    return {'within_batch': retrieval(rows,x,False), 'cross_batch': retrieval(rows,x,True),
            'batch_classifier': {'n_evaluated': len(truths), 'n_unevaluated': len(rows)-len(truths),
                                 'accuracy': float(np.mean(np.array(predictions)==truths)) if truths else None,
                                 'majority_baseline_accuracy': float(np.mean(np.array(baselines)==truths)) if truths else None,
                                 'folds': folds}, 'warnings': sorted(set(warning)),
            'interpretation': 'Cosine retrieval; no global data normalization is learned. StandardScaler is fitted inside each classifier training fold. High batch predictability suggests a shortcut, not proof of artifact.'}

