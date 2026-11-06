# Evaluation run log

2026-11-06: 24 cases and matching protocol authored before comparison code. Windows newline serialization initially caused checksum rejection; checksum sidecars corrected to actual frozen bytes before the first evaluation. Manifest content unchanged.

Development pass exposed merged OCR spaces causing false number/negation categories. Added a character-identical-except-whitespace rule: retain a wording finding and review requirement, without alleging a critical token change. This is development tuning. An exploratory development run overlapped code editing and is excluded from canonical results.

Rules frozen after 17 passing tests. Canonical development evaluation will run next, followed by the first held-out evaluation. No changes based on held-out failures are permitted without marking that set inspected and reused.

Canonical development run: 7 TP / 8 FP / 2 FN critical findings. First held-out run: 8 TP / 1 FP / 1 FN critical findings. Results inspected and preserved in evaluation/results. No comparison, extraction, alignment, reporting or normalization code was modified after the first held-out evaluation. Subsequent changes were documentation, packaging compatibility and UI test path correction. The held-out set is now inspected.

The fixed obscuration region conceals quantity text in development but different text in the held-out layout, leaving its quantity readable; this limitation was observed after evaluation and is retained rather than relabelling the case. Development manifest id negation_delete describes a negation insertion for its affirmative source; the manifest's explicit before/after strings are authoritative, and both directions occur across the two splits.

Post-evaluation rule audit: discovered that a regex word boundary after a percent sign failed to detect percentage-unit deletion (12% to 12). Added a focused regression test and changed that boundary to a negative word lookahead, rules version 1.1. This change was not motivated by a held-out case; nevertheless it occurred after holdout inspection. First-run v1.0 metrics/reports remain preserved. The v1.1 evaluation is explicitly an inspected/reused-set confirmation, not a new untouched result.

Rules v1.1 confirmation completed: development 7 TP / 8 FP / 2 FN; reused held-out 8 TP / 1 FP / 1 FN, unchanged from first-run v1.0. Preserved in the explicitly named *-v1.1-reused result directories. Example report exports refreshed to v1.1; original input PDF fingerprints unchanged. Final verification: 19 automated tests passed, documented CLI produced four findings and no extraction issues, Streamlit AppTest comparison/review interaction passed and localhost HTTP smoke test passed.
