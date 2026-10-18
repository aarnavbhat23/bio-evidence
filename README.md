# bio-evidence

Checks for biological assay tables and saved model predictions. The package keeps concentration bounds intact, refuses ambiguous identifier mappings, and makes evaluation assumptions visible in the output.

This grew out of peptide work where an inequality could become a training label, a publication could leak across folds, and a good-looking cross-validation score could fail on a new population. Nine small tools now share one package and one test suite. Each has a worked case on public data; small synthetic fixtures remain for boundary tests.

## Run a check

```bash
python -m pip install -e .
bio-evidence assay-units studies/assay_units/input.json --output assay-report.json
bio-evidence claim-scope studies/claim_scope/input.json --output claim-report.json
python -m unittest discover -s tests -v
```

The supplied study inputs run offline. A failing dataset contract can stop a pipeline with `--require-pass`; diagnostic reports otherwise exit successfully. Model downloads are optional and never occur when running the checks above.

## What has actually been run

| Check | Public-data case | What the output can establish |
|---|---|---|
| [Assay units](docs/modules/assay_units.md) | 6,448 extracted MIC rows | Exact values, censored bounds and conversions requiring missing molecular weight remain distinct |
| [Embedding drift](docs/modules/embedding_drift.md) | ESM-2 embeddings for 100 peptide candidates | Which top-10 neighbors change relative to composition vectors |
| [Structure ensemble](docs/modules/structure_ensemble.md) | 38 experimental Trp-cage NMR conformers, PDB 1L2Y | Pairwise C-alpha displacement with complete residue correspondence |
| [Perturbation effects](docs/modules/perturbation_effects.md) | Kang/scGen IFN-beta data, 7 cell types and 200 genes | Error of a held-out-cell-type mean-delta baseline; only 8 effects exceed the preset sign threshold |
| [Plate shortcuts](docs/modules/batch_shortcuts.md) | 520 treated wells from two JUMP pilot plates | Cross-plate replicate retrieval and held-out-compound plate predictability; within-plate retrieval is ineligible |
| [Gene aliases](docs/modules/gene_aliases.md) | Approved HGNC records | 2,331 colliding case-folded dictionary keys; contextual accuracy is undefined without gold labels |
| [Claim scope](docs/modules/claim_scope.md) | 60 expert-annotated SciFact development pairs | Actual frozen NLI and small instruction-model behavior, with raw responses retained |
| [Resource frontier](docs/modules/model_frontier.md) | Actual retrieval timings after embedding quantization | A measured fidelity/resource frontier for this small saved-embedding workload |
| [Dataset contract](docs/modules/dataset_contract.md) | A deliberately unsafe row split of the real MIC table | Rejection of declared paper/sequence separation violations; it does not allege an upstream split error |

[Read the case methods, licenses and results](studies/README.md). Each case retains its input and report. Source URLs, byte counts and SHA-256 values are in [`studies/sources.json`](studies/sources.json). Tests exercise the public cases as well as numerical and parser boundaries.

## A result worth inspecting

The NLI model correctly labels **23 of 60** balanced scientific claim/abstract pairs (macro-F1 **0.337**). This is a general-domain model transferred without fitting to a small development subset, using whole abstracts and 512-token truncation. It is a weak baseline, not a new claim-verification system. Quote occurrence checks cannot rescue a semantically wrong label.

For a fitted protein-model experiment, see the separate [Peptide Leakage Lens split study](https://github.com/aarnavbhat23/peptide-leakage-lens). Keeping that study separate gives the experimental question, exclusions and predictions a clear home.

## API

Checks are ordinary functions returning JSON-serializable reports:

```python
from bio_evidence.assay_units import threshold_label

assert threshold_label('>64 µM', threshold=16) == 0
assert threshold_label('>8 µM', threshold=16) is None
```

Here `0` means definitely above the chosen MIC threshold; it does **not** mean biologically inactive. Mass and molar units cannot be compared without the molecular weight of the tested chemistry.

The nine CLI names are listed by `bio-evidence --help`. Model inference adapters are separate from evaluation: `python -m bio_evidence.ollama` runs an already-installed local model, while the study scripts document the actual CPU runs included here.

## Boundaries

These are established checks and evaluation methods implemented for a focused workflow. They do not replace experimental validation, homology clustering, prospective clinical studies or expert adjudication. There is no claim of a field-first algorithm, independent review, production deployment or downstream adoption. Timings, small development-set scores and selected candidate sets should not be generalized to other workloads.

MIT applies to the package code. External data, annotations and weights retain their own terms and attribution. Provenance and contribution expectations are in [CONTRIBUTING.md](CONTRIBUTING.md). The original repositories remain inspectable through the [migration record](docs/MIGRATION.md).
