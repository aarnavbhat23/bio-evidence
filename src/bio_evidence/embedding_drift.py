"""Paired neighborhood audit of protein representations."""
import numpy as np
from ._validation import need, unique_ids

def neighbors(vectors, k):
    x = np.asarray(vectors, dtype=float)
    if x.ndim != 2 or not np.isfinite(x).all() or np.any(np.linalg.norm(x, axis=1) == 0):
        raise ValueError('Embeddings must be finite nonzero vectors in a rectangular matrix')
    x = x / np.linalg.norm(x, axis=1, keepdims=True)
    sim = x @ x.T
    np.fill_diagonal(sim, -np.inf)
    # Input order deterministically breaks exact cosine ties.
    return np.argsort(-sim, axis=1, kind='stable')[:, :k]

def analyze(data):
    """Compare cosine neighbors after aligning two representations by sequence ID."""
    need(data, 'rows', 'k')
    rows, k = data['rows'], data['k']
    if isinstance(k, bool) or not isinstance(k, int) or not 1 <= k < len(rows):
        raise ValueError('k must be an integer from 1 to n-1')
    for row in rows:
        need(row, 'id', 'reference', 'candidate')
    unique_ids(rows)
    a = neighbors([r['reference'] for r in rows], k)
    b = neighbors([r['candidate'] for r in rows], k)
    records = []
    for i, r in enumerate(rows):
        item = {'id': r['id'], 'neighbor_overlap': len(set(a[i]) & set(b[i])) / k,
                'reference_neighbors': [rows[j]['id'] for j in a[i]],
                'candidate_neighbors': [rows[j]['id'] for j in b[i]]}
        if all('family' in row for row in rows):
            item.update({name+'_family_precision': sum(rows[j]['family'] == r['family'] for j in indices)/k
                         for name, indices in [('reference',a[i]),('candidate',b[i])]})
        records.append(item)
    return {'n_sequences': len(rows), 'k': k, 'records': records,
            'mean_neighbor_overlap': float(np.mean([r['neighbor_overlap'] for r in records])),
            'interpretation': 'Neighbor turnover measures representation sensitivity; family precision requires trusted labels and is not activity prediction.'}

