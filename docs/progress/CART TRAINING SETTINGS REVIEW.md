# CART Training Settings Review

Reviewed 2026-10-27 for Task 18. This records the current software settings and a verified threshold-selection correction. It is not a completed model-training run or proof that the final dataset is ready.

## Current defaults

| Setting | Current implementation |
| --- | --- |
| Training source | Baseline data rows with receiver-reconciled label provenance |
| Inputs | RSSI in dBm, SNR in dB, verified neighbour battery percent, and neighbour data-backoff count |
| Scaling | Original units; no Min-Max scaling step |
| Algorithm | CART decision tree using Gini impurity |
| Maximum depth | 5 |
| Minimum samples to split | 10 |
| Class weighting | Balanced |
| Training seed | 42 by default; save the actual value used |
| Outer test split | Approximately 20% of rows, assigned by whole sessions |
| Internal validation | A separate session split within the outer training portion |
| Outcome convention | Safe 0, Danger 1; Danger is the positive class |
| Threshold candidates | 0.05 through 0.95 in increments of 0.05 |
| Threshold selection | Highest validation Danger F1; equal-F1 ties prefer higher Danger Recall |
| Remaining exact-score ties | Nearest 0.5, then lower threshold, for deterministic selection |
| Final fitting | Fit on the outer training portion after threshold selection; leave outer held-out sessions unused for fitting/tuning |
| Failure probability | Original unweighted Danger share in the corresponding fitted tree leaf |

The approximate 80/20 split concerns row counts while preserving whole sessions. An inner validation split further divides the outer training portion for tuning. It is not an independent random 80/20 row shuffle. The current splitter stops if it cannot form valid partitions with both classes; collect more genuine sessions rather than bypassing the check.

The data checker targets at least 300 usable observations and six sessions, but the trainer's separate minimal size check is only 30 rows and both classes. Passing that smaller software guard is not evidence that the collection targets or scientific adequacy requirements are met.

## Correction completed

Previously, equal-F1 thresholds were selected by closeness to 0.5 before considering Recall. The selector now prioritises Recall on equal F1, as required by the existing firmware task list. Deterministic secondary rules apply only when both scores are equal.

Five direct tests of the actual selector pass: higher Recall wins equal F1, F1 remains primary, exact-score ties are deterministic, closeness to 0.5 is only secondary to both scores, and empty/nonfinite validation tables are rejected. Forty-nine combined logging, timing, labelling and threshold checks pass.

## Still required before final training

- Verify the four input measurements, especially actual battery sensing. No battery feature was removed or synthesized.
- Confirm the final outcome target and observation rule with the manuscript, and validate the paired recording and label pipeline on hardware.
- Review usable rows, class/condition/link coverage and session identity before selecting partitions.
- Install and verify the full machine-learning runtime before an actual fit/export check. The selected bundled Python currently lacks scikit-learn, matplotlib and micromlgen; no real training run was executed during this review.
- Save the final settings, split membership, dataset provenance, seed, threshold, report and exported header.
- Use independent evaluation runs after the model is frozen. Do not use held-out evaluation results to tune the model without reporting that use and obtaining fresh independent test evidence as needed.

The threshold-specific firmware checklist item is complete. CART Task 18 remains open until the remaining training-readiness requirements are verified.
