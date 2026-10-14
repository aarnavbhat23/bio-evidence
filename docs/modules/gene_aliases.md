# Input schema and interpretation

Input `genes`: unique `id`, `species`, `symbol`, list `aliases`. Input `queries`: unique `id`, `mention`, exact species string and optional `gold_id` (null means expected abstention). Supply `dictionary_version`. Species naming must match between dictionary and queries. The fixture uses invented gene IDs.

Aliases and symbols are case-folded; species is not. A single dictionary match is resolved, multiple matches abstain, no match is unknown. Official-symbol collisions also abstain conservatively. Coverage includes all queries; selective accuracy includes only labeled answered queries. Overall accuracy includes labeled abstentions; always report it beside coverage to avoid rewarding an all-abstain system. Gold contextual IDs may differ from dictionary candidates, which is counted as an error. No fuzzy matching, LLM guesses or ontology updates are performed.
