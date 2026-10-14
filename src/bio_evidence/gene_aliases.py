"""Conservative dictionary resolver; no guessed gene identifiers."""
from collections import defaultdict
from ._validation import need, unique_ids

def build_index(genes):
    index = defaultdict(set)
    for gene in genes:
        need(gene, 'id', 'species', 'symbol', 'aliases')
        if not isinstance(gene['aliases'],list) or any(not isinstance(a,str) or not a.strip() for a in [gene['species'],gene['symbol']]+gene['aliases']):
            raise ValueError('Require nonempty species/symbol and a list of nonempty alias strings')
        for alias in [gene['symbol']] + gene['aliases']:
            index[(gene['species'], alias.casefold())].add(gene['id'])
    unique_ids(genes)
    return index

def analyze(data):
    """Resolve only unique species/alias matches and score selective coverage."""
    need(data, 'genes', 'queries', 'dictionary_version')
    index = build_index(data['genes'])
    output = []
    for q in data['queries']:
        need(q, 'id', 'mention', 'species')
        if any(not isinstance(q[k],str) or not q[k].strip() for k in ('mention','species')):
            raise ValueError('Mention and species must be nonempty strings')
        candidates = sorted(index.get((q['species'], q['mention'].casefold()), set()))
        prediction = candidates[0] if len(candidates) == 1 else None
        item = {'id': q['id'], 'candidates': candidates, 'prediction': prediction,
                'status': 'resolved' if prediction else ('ambiguous' if candidates else 'unknown')}
        if 'gold_id' in q:
            item['correct'] = prediction == q['gold_id']
            item['gold_id'] = q['gold_id']
        output.append(item)
    unique_ids(data['queries'])
    labeled = [o for o in output if 'correct' in o]
    answered = [o for o in labeled if o['prediction'] is not None]
    return {'dictionary_version': data['dictionary_version'], 'queries': output,
            'coverage': sum(o['prediction'] is not None for o in output)/len(output) if output else None,
            'n_labeled': len(labeled), 'n_labeled_answered': len(answered),
            'selective_accuracy': sum(o['correct'] for o in answered)/len(answered) if answered else None,
            'including_abstention_accuracy': sum(o['correct'] for o in labeled)/len(labeled) if labeled else None,
            'collisions': [{'species': s, 'alias': a, 'ids': sorted(v)} for (s,a),v in sorted(index.items()) if len(v)>1],
            'interpretation': 'Exact case-folded dictionary lookup, with required species. Abstention is not disambiguation; dictionary currency and contextual mention annotation require independent review.'}

