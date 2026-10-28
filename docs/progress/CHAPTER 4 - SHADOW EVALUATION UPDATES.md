# Chapter 4 edits - independent Baseline shadow evaluation

Approved method: separate Baseline shadow-mode evaluation, 27 October 2026.
These edits are ready to paste; they have not been inserted into the manuscript.
Chapter 5 is unchanged. Formulas for Precision, Recall and F1 remain unchanged.

Locations refer to the manuscript PDF currently saved in Documents, PDF pages
130-132 and 137. If your editable manuscript has shifted, find the quoted text.

## 1. Section 4.7, metric 4 - replace the probe paragraph

Find the complete paragraph beginning:

> To resolve the avoided-link paradox and ensure independent ground-truth labeling, the testing protocol introduces a dual-transmission probe mechanism during Phase 3.

Replace that paragraph, through the sentence ending with Rainio et al. (2024), with:

> Classifier performance will be evaluated in independent Baseline sessions conducted after the CART model and decision threshold are frozen. These sessions will be excluded from training, tuning and development testing. Baseline routing will select the next hop independently of either classifier, while CART and the heuristic record predictions for that same hop in shadow mode. Ground truth will be established by reconciling completed transmissions with intended-receiver records within the predefined observation window. Safe denotes verified timely acceptance; Danger denotes verified non-reception under complete observation. Missing acknowledgments alone will not establish failure. The first attempt per message and intended hop will be evaluated; ambiguous, delayed, rejected or incompletely observed cases will be excluded and reported. Precision, Recall and F1-score will describe prediction performance on these sampled Baseline links. No outcome will be inferred for an untried link.

Why: the actual observation is whether a transmitted frame was accepted, not
whether a hypothetical detour would have succeeded. Network performance across
the five configurations remains a separate evaluation.

## 2. Table 4.6 - replace the whole table

Keep the title: **Table 4.6: Evaluative Confusion Matrix Layout.**

| Observed outcome | Predicted Danger / Risky (1) | Predicted Safe (0) |
| --- | --- | --- |
| Danger (1): verified non-reception within the observation window | True Positive (TP): correctly predicted non-reception | False Negative (FN): missed non-reception |
| Safe (0): verified timely receiver acceptance | False Positive (FP): incorrectly predicted non-reception | True Negative (TN): correctly predicted acceptance |

This replaces all references in the table to triggering a detour, successful
routing, a fully operational link or a permanently degraded link. Each row
represents the observed outcome of one eligible transmission attempt.

## 3. Metric 4 - replace the Where list under the formulas

Replace the existing TP/FN/FP definitions (successful detours, fatal drops and
acceptable unnecessary detours) with this complete list:

- **TP:** Predicted Danger with verified non-reception.
- **FN:** Predicted Safe with verified non-reception.
- **FP:** Predicted Danger with verified timely acceptance.
- **TN:** Predicted Safe with verified timely acceptance.

Keep the existing equations. Numerical worked examples can remain if their
counts match these definitions and are explicitly illustrative.

## 4. Metric 4 - replace Processing Steps 1-4

1. **Extract predictions:** Select the paired CART and heuristic verdicts for the first data-transmission attempt per message and intended hop in the independent Baseline sessions.
2. **Establish outcomes:** Match sender completion and intended-receiver records using session, node, boot, message, attempt and frame identity, with reviewed timing and logging coverage. Exclude unverified outcomes.
3. **Construct confusion matrices:** Compare each classifier against the same eligible observed outcomes and tally TP, FP, TN and FN.
4. **Calculate performance:** Compute Precision, Recall and F1-score; report the eligible sample count and exclusion reasons. Treat undefined metrics as unavailable.

## 5. Replace the shadow-logging sentence if already inserted

Find your added sentence beginning either **Across all configurations, each data
transmission records...** or **in every configuration, each data transmission
logs...**. Replace that sentence with:

> The firmware records paired CART and heuristic verdicts when the frozen model and required inputs are available. Formal classifier comparison will use only the independent Baseline sessions; shadow records from other configurations will remain diagnostic.

## 6. Section 4.7, statistical tests - replace item 2

Replace the existing McNemar item with:

> **2. McNemar's Test:** Applied to paired classification correctness for CART and the heuristic on the same eligible first-attempt cases from the independent Baseline shadow-mode sessions. Each prediction will be assessed against verified intended-receiver outcomes. The sampling design will be reviewed for dependence among messages, hops and sessions before inferential testing. Recall and F1-score will be reported separately as descriptive metrics.

## What happens later

1. Finish the prerequisites and collect the development/training data.
2. Train, tune, test and freeze CART.
3. Collect new Baseline shadow-evaluation sessions with the frozen model and
   complete sender/receiver evidence. Keep their session names distinct from
   every development session.
4. Compute the classifier metrics using the reviewed plan and coverage manifest.
5. Conduct the separate five-configuration network evaluation under its frozen
   protocol. Report real results in Chapter 5 after the data have been reviewed.

Software preparation and method selection do not establish physical validation.
Details and the analysis command are in Code/Thesis/docs/AVOIDED_LINK_EVALUATION.md.
