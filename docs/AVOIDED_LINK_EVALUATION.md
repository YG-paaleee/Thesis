# Independent Baseline shadow evaluation

Status: selected by the user on 27 October 2026. Software preparation is complete;
physical evaluation remains pending. The user confirmed manuscript insertion on
27 October 2026; the revised file has not been independently reread. No probe packets
are required by the selected method. No boards were flashed for this update.

## What is evaluated

After training, tuning and development testing, freeze the CART header and
threshold. Conduct new Baseline sessions. Baseline routing chooses the next hop;
CART and the heuristic predict that same hop without changing the routing decision.
Evaluate those predictions against the intended receiver's independently recorded
outcomes. This estimates failure-prediction performance on the sampled Baseline
links. It does not measure counterfactual outcomes of links avoided in Full mode.
Five-configuration network evaluation remains separate.

## Software safeguards

- The training exporter stamps CART_MODEL_ID in the generated header. Its report
  records this identity, the header's SHA-256 and every development session,
  including train, validation, development test and any externally inspected data.
- Firmware CONFIG logs include the loaded model identity. Missing/old model
  identity is unavailable; the analysis does not invent it. Both verdicts are
  computed before data transmission. Baseline retains no relay filter.
- The classifier plan references the frozen report/header, the new evaluation
  session names and evidence of the board freeze. Wrong artifact hashes, missing
  provenance, an incompatible training source/split and overlapping sessions fail.
- Only planned independent Baseline sessions with the matching recorded model
  enter classifier evaluation. Full/Heuristic/survey sessions are excluded.
- Only the first attempt for each session/node/boot/origin/message/intended-hop
  unit is sampled. A later successful retry cannot replace an unknown or failed
  first attempt. The study must still review dependence between messages, hops
  and sessions before interpreting McNemar significance.
- Outcomes require reviewed sender completion, receiver coverage and measured
  timing uncertainty using receiver_labels.py. Missing ACKs do not label loss.
  Rejected, delayed, ambiguous and unobserved cases stay excluded and audited.
- Both classifiers use the same eligible cases, with Danger positive. Reports
  include confusion counts, Precision, Recall and F1; unavailable denominators
  remain unavailable. *_classifier_audit.csv contains every real TX candidate,
  recorded model identity, eligibility and exclusion reason.

## Correct collection order

1. Complete the firmware, battery-feature and paired-logging prerequisites.
2. Collect the Baseline development data and train/tune/test CART by session.
3. Freeze report.json, cart_model.h, threshold, features and firmware. Do not
   retrain against the independent evaluation data after inspecting outcomes.
4. Build and upload the frozen model with the formal baseline-nX environments.
   Confirm model identity and Baseline configuration in each participating log.
   Use planned links: ordinary Baseline excludes direct V6-V1. Survey builds
   are for range engineering, not these classifier sessions.
5. Choose new session names and record them in the classifier plan before tests.
   Sample normal and weak conditions, with sufficient observed Safe and Danger
   cases for meaningful Recall/F1. Agree the conditions, sample sizes and timing
   windows before collecting; no fixed count guarantees reliability.
6. Save sender and intended-receiver logs for evaluated links. With four laptops,
   only links with adequate paired evidence are eligible; V1-only logging is
   insufficient for remote relay links. Review coverage and clock uncertainty.
7. Run the comparison below, inspect exclusions and confirm the sampling design.
   The separate five-configuration runs measure PDR, delay, queuing and buffering.

## Plan and analysis

Copy docs/classifier_plan.example.json to a new plan beside the actual frozen
artifacts, then fill in its real paths, session names and freeze evidence. The
example is not an approved or completed experiment. Paths are relative to the
plan file. Existing historical training reports without provenance cannot be
silently accepted; generate the frozen report through the updated exporter.

```powershell
python tools/analyze_run.py "shadow-evaluation/*.csv" --compare --coverage reviewed_coverage.json --classifier-plan classifier_plan.json --table shadow_results.csv
```

The coverage manifest has the schema in docs/RECEIVER_LABELS.md. This command
performs no training, changes no firmware and transmits no radio packets.

Exact Chapter 4 edits are in Documents/CHAPTER 4 - SHADOW EVALUATION UPDATES.md
relative to the thesis root. Chapter 5 is unchanged. Parent readiness tasks remain
unchecked until the paper is updated and physical paired tests pass.
