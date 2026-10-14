"""Explicitly mapped C-alpha ensembles; no implicit residue intersection."""
import itertools
import numpy as np
from ._validation import need, unique_ids

def superpose(moving, target):
    x, y = np.asarray(moving, dtype=float), np.asarray(target, dtype=float)
    if x.shape != y.shape or x.ndim != 2 or x.shape[1] != 3 or len(x) < 3:
        raise ValueError('Coordinates must be corresponding N x 3 arrays with N >= 3')
    if not np.isfinite(x).all() or not np.isfinite(y).all():
        raise ValueError('Coordinates must be finite')
    xc, yc = x-x.mean(0), y-y.mean(0)
    u, _, vt = np.linalg.svd(xc.T @ yc)
    correction = np.diag([1,1, np.linalg.det(u @ vt)])
    rotation = u @ correction @ vt
    aligned = xc @ rotation + y.mean(0)
    return aligned, np.linalg.norm(aligned-y, axis=1)

def analyze(data):
    """Report pairwise aligned displacement for exactly corresponding residue maps."""
    need(data, 'models')
    models = data['models']
    if len(models) < 2:
        raise ValueError('At least two models of the same input are required')
    for m in models:
        need(m, 'id', 'residue_keys', 'residue_names', 'coordinates')
        if len(m['residue_keys']) != len(m['coordinates']) or len(m['residue_names']) != len(m['coordinates']):
            raise ValueError('Residue map/name/coordinate length mismatch')
        if len(set(m['residue_keys'])) != len(m['residue_keys']):
            raise ValueError('Residue keys must be unique, including chain and insertion code')
    unique_ids(models)
    ref = models[0]
    if any(m['residue_keys'] != ref['residue_keys'] or m['residue_names'] != ref['residue_names'] for m in models):
        raise ValueError('Residue maps or names differ; supply an explicit verified correspondence')
    pairs, displacement = [], []
    for a, b in itertools.combinations(models, 2):
        _, d = superpose(a['coordinates'], b['coordinates'])
        pairs.append({'left': a['id'], 'right': b['id'], 'ca_rmsd_angstrom': float(np.sqrt(np.mean(d*d)))})
        displacement.append(d)
    mean_displacement = np.mean(displacement, axis=0)
    return {'n_models': len(models), 'n_residues': len(ref['coordinates']),
            'pairs': pairs, 'residues': [dict(key=k, mean_pair_displacement_angstrom=float(d))
                                          for k,d in zip(ref['residue_keys'], mean_displacement)],
            'interpretation': 'Global rigid alignment over all supplied chains. Fixed chain correspondence; symmetry permutations and domainwise alignment are not attempted. Consistency is not accuracy or thermodynamic flexibility.'}

