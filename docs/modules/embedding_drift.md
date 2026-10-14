# Input schema and interpretation

Input `rows`: unique `id`, `reference` vector, `candidate` vector, optional `family`. `k`: integer in [1,n-1]. Each representation must be a finite nonzero rectangular matrix; the two representations may have different dimensions. Rows align the same sequence by ID, so never merge by position across separately ordered files.

Cosine top-k excludes the query itself. Exact ties follow input order. `neighbor_overlap` is set intersection / k, not Jaccard. Optional family precision uses family equality only, with trusted labels required. There is no fitted classifier, activity prediction, train/test claim or calibration. Query/gallery family frequency affects retrieval. The optional ESM script supplies actual embeddings, separately from the synthetic example.
