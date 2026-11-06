# Application evidence

Defensible claims below are scoped to the checked-in implementation and synthetic results. This is a navigation map; inspect the linked code/tests/results before reusing a claim.

|Claim|Implementation evidence|Verification evidence|
|---|---|---|
|Built a local OCR comparison and review workflow for reference/scanned PDF pairs|[extraction](../leaflet_compare/extraction.py), [comparison](../leaflet_compare/comparison.py), [UI](../app.py)|[image-only PDF integration test](../tests/test_integration.py), [example source evidence](../examples/dev-quantity/review.html)|
|Implemented deterministic rules for quantity/unit, negation, warning and paragraph omissions while preserving punctuation and critical tokens|[text rules](../leaflet_compare/text.py), [alignment](../leaflet_compare/alignment.py)|[core tests](../tests/test_core.py), [category results](../evaluation/results/heldout/RESULTS.md)|
|Linked findings to document fingerprints, extracted paragraphs, page coordinates and review decisions|[models](../leaflet_compare/model.py), [report exports](../leaflet_compare/reporting.py)|[report integrity tests](../tests/test_core.py), [complete example JSON](../examples/dev-quantity/report.json)|
|Evaluated on frozen synthetic development and held-out templates with separate detection and review-coverage measures|[manifests and protocol](../evaluation/PROTOCOL.md), [evaluator](../tools/evaluate.py)|[held-out raw metrics](../evaluation/results/heldout/metrics.json), [development metrics](../evaluation/results/dev/metrics.json), [run log](../evaluation/RUN_LOG.md)|
|Measured 8/9 held-out critical detections, with one false critical finding and one miss, under exact category/paragraph matching|[matching code](../tools/evaluate.py)|[first held-out result](../evaluation/results/heldout/RESULTS.md); 12 cases, 9 labelled critical changes, two control cases|
|Made extraction uncertainty and review workload explicit|[failure routing](../leaflet_compare/comparison.py), [extraction issues](../leaflet_compare/extraction.py)|[obscured report](../examples/dev-ambiguous/review.html), 12/12 held-out cases routed to review, 6 wording alarms on two controls|

Measured 19 passing local automated tests (18 offline and one OCR integration). A separate AppTest interaction ran the built-in example, rendered evidence and persisted a reviewer decision. This is not browser screenshot testing or evidence of deployment.

Do not claim calibrated OCR confidence, real-world safety, clinical/regulatory suitability, TVT compatibility, employer affiliation, multilingual comparison, deployment or unattended verification. Held-out failures have been inspected. An independent later audit fixed percentage-unit deletion in rules v1.1; reruns are reused-set confirmations, not untouched evaluations. Any future reuse must retain that disclosure. Results describe synthetic English prose only; the control false alarms and 100% review routing are material limitations. No causal claim about job application outcomes is supported.
