# Input schema and interpretation

Each row: unique `id`, `context`, `gene`, `perturbation`, finite numeric `observed_effect` and `predicted_effect`. The caller computes effects versus matched controls. Supply `effect_units` and a nonnegative, preregistered `effect_threshold` in those same units.

Only observed absolute effects strictly above the threshold enter sign accuracy; predictions at or below it are neutral and count as misses. MAE uses all rows. Zero-effect baseline MAE = mean absolute observed effect; skill = 1 - model MAE / zero baseline MAE, null if the baseline error is zero. Context-macro MAE gives each context equal weight. Correlated genes/replicates and unequal context sizes preclude rowwise confidence claims; add replicate/context bootstrap in a real study. Training, control selection and split provenance are not verified by this evaluator.
