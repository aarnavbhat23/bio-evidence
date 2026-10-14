"""Offline JSON dataset contract validator."""
import hashlib
import json
from collections import defaultdict
from ._validation import need

def content_hash(rows):
    return hashlib.sha256(json.dumps(rows, sort_keys=True, separators=(',',':'), allow_nan=False).encode()).hexdigest()

def analyze(data):
    """Validate declared provenance, row identity and cross-split biological groups."""
    need(data, 'contract', 'rows')
    contract, rows = data['contract'], data['rows']
    need(contract, 'source_uri', 'license', 'version', 'citation', 'sha256', 'required_columns', 'id_column', 'split_column', 'group_columns')
    issues = []
    for key in ('source_uri','license','version','citation'):
        if not isinstance(contract[key],str) or not contract[key].strip():
            issues.append({'type':'missing_provenance', 'field':key})
    digest = content_hash(rows)
    if digest != contract['sha256']:
        issues.append({'type':'hash_mismatch', 'expected':contract['sha256'], 'actual':digest})
    columns = set(contract['required_columns']) | {contract['id_column'],contract['split_column']} | set(contract['group_columns'])
    seen, groups = {}, defaultdict(set)
    for i,row in enumerate(rows):
        missing = sorted(k for k in columns if k not in row or row[k] is None or row[k] == '')
        if missing:
            issues.append({'type':'missing_required_fields','row_index':i,'fields':missing})
            continue
        row_id = row[contract['id_column']]
        if not isinstance(row_id,str) or not row_id.strip():
            issues.append({'type':'invalid_id','row_index':i})
            continue
        if row_id in seen:
            issues.append({'type':'duplicate_id','id':row_id,'rows':[seen[row_id],i]})
        seen[row_id] = i
        # Each named grouping field is enforced independently, never only as a tuple.
        for column in contract['group_columns']:
            value, split = row[column], row[contract['split_column']]
            if not isinstance(value,(str,int)) or isinstance(value,bool) or not isinstance(split,str) or not split.strip():
                issues.append({'type':'invalid_group_or_split','row_index':i,'column':column})
                continue
            groups[(column,value)].add(split)
    for (column,value),splits in sorted(groups.items(), key=lambda x:str(x[0])):
        if len(splits)>1:
            issues.append({'type':'cross_split_group','column':column,'group':value,'splits':sorted(splits)})
    return {'passed':not issues, 'n_rows':len(rows), 'content_sha256':digest, 'issues':issues,
            'interpretation': 'Checks declared metadata and supplied grouping IDs. It cannot validate license rights, establish homology clusters or detect unknown source overlap. Content hash covers canonical JSON rows, not original file bytes.'}

