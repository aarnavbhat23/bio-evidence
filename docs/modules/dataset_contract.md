# Input schema and interpretation

Input `rows` is a JSON list of row objects; `contract` requires source_uri, license, version, citation, sha256, required_columns (list), id_column, split_column and group_columns (list). The content hash is SHA-256 of UTF-8 json.dumps(rows, sort_keys=True, separators=(',',':'), allow_nan=False); the CLI input hash separately covers original bytes.

The checker flags absent/empty provenance, content-hash mismatch, missing required values, duplicate IDs and groups crossing splits. Each group column is checked independently (for example family AND paper), not as a composite key. IDs must be nonempty strings. `passed=false` in the report is a contract failure; the CLI still exits successfully when it produced a valid diagnostic report. It cannot verify licensing, sequence clustering, source correctness or pretraining overlap. The fixture intentionally contains a family crossing train/test so the expected report fails that contract.
