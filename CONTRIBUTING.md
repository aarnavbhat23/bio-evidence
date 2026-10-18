# Contributing

Start with a failure case: a source row, an expected interpretation, and the output that violates it. Include the source version and redistribution terms. Small examples are more useful than broad feature requests.

Run `python -m unittest discover -s tests -v` after `python -m pip install -e .`. The suite includes synthetic boundary cases and real public-data regressions. An expected contract failure is not a failed software test.

For new studies, declare the endpoint, exclusions, split unit and baseline before fitting a model. Keep raw model outputs and source hashes. Do not turn an inequality into an exact concentration, interpret a verified quotation as entailment, or report accuracy for gene queries without contextual gold labels.

Aarnav Bhat is the maintainer. External datasets, annotations and model weights are credited in `studies/README.md` and retain their own licenses. No independent reviewer or downstream adoption is claimed.
