# Input schema and interpretation

Each row requires `id`, `sequence`, `chemistry`, `source`, `organism`, `condition`, `value` and `unit`. Values may be exact numbers, strings prefixed by <, <=, >, >=, or =, or null/NA/ND for missing. Ranges are sent to manual review. Accepted units: mg/L, ug/mL, ng/mL, g/L, M, mM, uM and nM (Unicode micro accepted).

Molar conversion requires positive `molecular_weight_g_mol` for the actual tested chemistry. It is never computed from a bare sequence. Output `mg_per_L` is a threshold when `status=censored`; preserve `operator` downstream. Unsupported units, ranges and missing molecular weights remain unresolved. Repeated source/chemistry/organism/condition keys may be valid replicates. MIC values alone do not classify a peptide as antimicrobial.
