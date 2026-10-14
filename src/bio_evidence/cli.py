"""One command line for the package's independent checks."""
import argparse
import hashlib
import importlib
import json
from pathlib import Path

MODULES = {
    'assay-units': 'assay_units',
    'embedding-drift': 'embedding_drift',
    'structures': 'structure_ensemble',
    'perturbation-effects': 'perturbation_effects',
    'batch-shortcuts': 'batch_shortcuts',
    'gene-aliases': 'gene_aliases',
    'claim-scope': 'claim_scope',
    'model-frontier': 'model_frontier',
    'dataset-contract': 'dataset_contract',
}

def main(argv=None):
    parser = argparse.ArgumentParser(prog='bio-evidence', description=__doc__)
    parser.add_argument('check', choices=MODULES)
    parser.add_argument('input', type=Path)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--require-pass', action='store_true', help='Exit 1 when a dataset contract fails; only valid for dataset-contract')
    args = parser.parse_args(argv)
    if args.require_pass and args.check != 'dataset-contract':
        parser.error('--require-pass applies only to dataset-contract')
    try:
        raw = args.input.read_bytes()
        data = json.loads(raw)
        module = importlib.import_module('bio_evidence.' + MODULES[args.check])
        result = module.analyze(data)
        result['input_sha256'] = hashlib.sha256(raw).hexdigest()
        result['data_kind'] = data.get('data_kind', 'user-supplied; provenance unverified')
        text = json.dumps(result, indent=2, allow_nan=False) + '\n'
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(text)
        else:
            print(text, end='')
        return 1 if args.require_pass and not result['passed'] else 0
    except (OSError, ValueError, KeyError, TypeError) as exc:
        parser.error(str(exc))

if __name__ == '__main__':
    raise SystemExit(main())
