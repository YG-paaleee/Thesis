# CART Training Task List

Purpose: track the work from collection preparation through training and freezing the TinyML CART model. Independent evaluation runs and Chapter 5 analysis follow this checklist.

The three days are planning targets, not deadlines that override verification. Complete each stage's readiness check before starting the next stage.

## Progress tracking

- Last updated: 2026-10-27
- Current stage: Day 1 — Prepare and verify data collection
- Verified completed tasks: 1 of 22
- Next task: Follow [FIRMWARE TASKLIST.md](FIRMWARE%20TASKLIST.md) as the primary implementation checklist at the user's request on 2026-10-27. Priorities 1–3 have software changes and checks recorded; remaining UI/reliability software and hardware-dependent data-validity/readiness checks remain open. Return here after the required firmware/UI work and pilots. Prepared collection, labelling and timing work is retained; no hardware readiness gate has been waived.
- Blocking issues: Battery sensing; deployed sender/receiver capture; outcome definition and reconciliation; attempt/session identity and timing; collection-log completeness verification. See the Task 1 review below.

Check a task only after its result is verified. Add evidence, filenames, or a short note below the task. An unchecked task may be partially complete; record that in its notes.

Previous evidence: the indoor logging check on 2026-10-24 saved all 25 numbered V2 messages at V1, including records beyond the dashboard's latest-20 limit. This verifies that capture session, not the complete deployed training-data workflow.

### Solo work now and group work later

User preference recorded 2026-10-26: progress on work that can be done alone now; defer work requiring group participation until the planned meeting tonight. Dependencies still apply and deferred tasks remain unchecked.

Solo order:
1. Task 4: define outcome categories, matching rules and software requirements; use clearly identified artificial examples only for logic checks. Live receiver verification remains pending.
2. Task 5: prepare the multi-laptop timing procedure; verify it with the actual laptops later.
3. Task 3: prepare laptop setup instructions and recording/file-naming procedures locally; install and verify on the other laptops later.
4. Task 9: draft a session schedule and node/laptop assignment plan; finalise after deployment and pilot checks.
5. Task 18: review feature definitions and training settings, including the threshold tie-break; final readiness still depends on the verified dataset and any authorised software corrections.

Group/hardware work later: actual battery verification once a multimeter is available; multi-laptop setup and capture; distance survey; six-node placement checks; deployed pilot; final collection. Training and freezing follow usable data, not merely completion of solo preparation.

## Day 1 — Prepare and verify data collection

- [x] **1. Review the remaining collection blockers**
  - Identify the firmware and logging fixes needed for valid training data. Cross-reference `FIRMWARE TASKLIST.md` rather than duplicating its implementation tasks.
  - Notes / evidence: Completed 2026-10-26 by inspecting the firmware tracker, current firmware, capture/dataset/training scripts, field-test plan, and the saved 25-message indoor log. Findings and existing implementation-task references appear below. Review completion does not mean the blockers are fixed.

- [ ] **2. Verify actual battery measurement**
  - Confirm that the firmware measures the external battery correctly. If it cannot, settle the feature and paper changes before final collection. A displayed percentage alone is not verification.
  - Notes / evidence: In progress 2026-10-26. Static inspection confirms `BATTERY_SOURCE_LIPO` reads the Heltec VBAT path on GPIO1 with GPIO37 control, then estimates percent linearly from 3.30–4.20 V. The reported Battery Shield V3 powers Heltec through USB; the code has no demonstrated measurement path to that external cell. Its plausible-voltage check cannot establish the source of the voltage. Actual external-cell voltage and charge are not verified. Await clear shield/Heltec connection photos, exact board identification, confirmation of any battery-connector or sensing wires, and availability of a multimeter. Do not calibrate against an unrelated USB-powered VBAT reading. No firmware or wiring changes made. The task remains unchecked pending physical verification or an explicitly agreed feature/methodology revision.
  - Hardware clarification 2026-10-26: The user reports the shields broke and replacement units are being ordered. Current field power is a 10,000 mAh USB power bank through a switched USB extension and USB cable into Heltec. The supplied setup photo is consistent with USB power; no separate battery-sensing connection is reported. Replacement listing screenshots call the two-cell module V8, although it was previously called V3; its exact hardware and telemetry capability remain unverified. Receiving a replacement shield will not by itself establish battery telemetry over the same USB power connection. The user proposed synthesized heartbeat battery percentages; this has not been implemented or accepted as measured field data. Pending decision: verified battery sensing versus an explicitly documented three-feature model without battery. Synthetic values may be used only in separately identified simulation/debug tests, not represented as measured power-bank charge.
  - Deferred at the user's request 2026-10-26 while obtaining a multimeter. The user intends to retain the shield-based final setup; no feature-removal decision has been made. Continue independent logging preparation and pilots, but resolve battery validity before final four-feature training collection. Task remains unchecked.

- [ ] **3. Prepare sender and receiver logging**
  - Establish how participating nodes will save complete logs while deployed, with node identities, firmware configuration, and power sources documented. V1-only logging cannot verify every relay link.
  - Notes / evidence: Started 2026-10-26. Current USB capture is verified at V1 in the indoor test. Need inventory of available recording computers/devices and a plan for capturing all required deployed endpoints. Firmware inspection confirms a nominal 30-second heartbeat interval with scheduling jitter, data-priority deferral and channel-busy skip logic; it is not an exact guaranteed 30-second reception schedule. No firmware changes made.
  - Inventory and deferral 2026-10-26: Four laptops are available and can accompany deployed nodes. Group installation and the multi-endpoint pilot are deferred at the user's request until the group meeting later tonight. Four simultaneous recordings do not cover all six nodes automatically; record the eligible sender/receiver pairs and plan coverage across sessions. Laptop logging can affect the power setup and must be documented.
  - Solo preparation update 2026-10-26: Created [GROUP LOGGING KIT.zip](GROUP%20LOGGING%20KIT.zip) and an extracted kit in Documents. Includes a Windows setup launcher, guided single-node Baseline recorder, current capture and timing tools, assignments sheet, timing guide and file-hash manifest. Recorder filenames include session/node/laptop/timestamp and retain declared power metadata. Capture refuses existing output files and stops on detected node/boot-configuration mismatches or serial disconnection. Forty-four combined software checks pass (eight new logging/setup checks); launcher dry run and non-installing setup check pass on this laptop, and archive contents/hashes verify. This does not verify installing on other laptops or opening their USB ports. Other Windows laptops need individual Python/pyserial setup; non-Windows devices need an equivalent procedure. Keep Task 3 unchecked until the actual group pilot passes. No board flashed or test traffic sent.

- [ ] **4. Complete outcome labelling**
  - Match transmissions with intended-receiver records. Define observation windows and how to handle failures, delayed arrivals, retries, and missing evidence. Missing ACKs alone do not prove failed reception.
  - Notes / evidence: Solo design review completed 2026-10-26; see [CART OUTCOME LABELLING PLAN.md](CART%20OUTCOME%20LABELLING%20PLAN.md). Documents proposed outcome categories, independent receiver evidence, attempt/reset identity, timing requirements, ACK-loss and duplicate handling, software gaps and verification cases. The current builder's 60-second ACK search is not a validated receiver-loss rule. Exact acceptance target and timing bounds require finalisation before implementation; no code changes or live validation completed. Task remains unchecked.
  - Implementation update 2026-10-26: User authorised solo software work. Added receiver acceptance/rejection and sender completion records, boot/log-sequence metadata, per-boot sender attempt IDs and frame fingerprints. Added paired receiver reconciliation with a reviewed coverage/clock manifest, an audit CSV for all candidate outcomes, and a training provenance guard against legacy ACK-only labels. Capture flushes every line and warns about malformed rows. Twenty-five artificial software checks pass; Baseline V1 and V2 builds pass. No boards flashed. Live paired acceptance/loss tests, timing bounds and observation-window selection remain pending, so Task 4 is not checked complete. See `Code/Thesis/docs/RECEIVER_LABELS.md` relative to the thesis root.

- [ ] **5. Verify the timing reference**
  - Confirm that records from different nodes can be matched reliably. Do not compare unrelated node uptime values. Document clock uncertainty and any effect on outcome classification.
  - Notes / evidence: Solo software/procedure preparation 2026-10-26. Added a USB-only CLOCK probe command and optional periodic capture probes with a separate `_clock.jsonl` file. Added `tools/timing_report.py` for measured offset intervals, drift/clock-step indicators and per-boot review, and `tools/clock_reference.py` for before/after laptop comparisons against a continuously running LAN reference without adjusting clocks. Guide: [CART TIMING VERIFICATION PLAN.md](CART%20TIMING%20VERIFICATION%20PLAN.md). Thirty-six artificial software checks pass across Tasks 4–5 (25 receiver-label checks and 11 timing checks). No actual timing measurements, cross-laptop accuracy, drift allowance or observation-window values have been verified. Group hardware checks remain pending and Task 5 stays unchecked. No boards flashed.
  - Build verification: Updated Baseline V1 and V2 builds pass with timing probes included; existing web-library deprecation warnings remain. All three timing/capture command help entry points run. The reference server was not started and no node or laptop clocks were adjusted during solo preparation.

- [ ] **6. Complete the distance survey**
  - Test message delivery at measured distances, repeat promising points, and select provisional node positions. Preserve the original logs and test sheets.
  - Notes / evidence:

- [ ] **7. Deploy and check all six nodes**
  - Use matching Baseline builds. Verify identities, routes, positions, antenna heights, and delivery. Recheck links after mounting or relocation.
  - Notes / evidence:

- [ ] **8. Run and inspect a short collection pilot**
  - Confirm that the saved files produce complete training examples: four inputs recorded before transmission plus a verified outcome. Check configuration and session metadata too.
  - Notes / evidence:

**Ready for Day 2 when:** the pilot produces usable examples and the deployed logging method works. Resolve failed checks before final training-data collection.

## Day 2 — Collect and validate training data

- [ ] **9. Prepare the session schedule**
  - Assign unique session names and plan normal, weak or obstructed, busy, and controlled-disruption conditions. Files from one physical session share its session identity.
  - Notes / evidence: Solo draft prepared 2026-10-27 in [CART COLLECTION SESSION SCHEDULE.md](CART%20COLLECTION%20SESSION%20SCHEDULE.md). Includes six provisional normal/weak/busy/disruption sessions, four-laptop assignment sets covering all six nodes across sessions, per-session procedure, coverage limitations, session identifiers and dataset sufficiency checks. Actual positions, origins, eligible links, traffic amounts, power arrangements and observation bounds must be finalised using the deployed pilot. No final collection was started; task remains unchecked until these assignments are confirmed.
  - [x] Solo session-schedule draft prepared.
  - [ ] Final deployed assignments and pilot-based collection settings confirmed.

- [ ] **10. Collect normal-condition sessions**
  - Record automatically generated data traffic and accompanying neighbour information using the verified pilot procedure.
  - Notes / evidence:

- [ ] **11. Collect weak or obstructed-link sessions**
  - Record actual outcomes across relevant links. Do not assume a weak signal means failure.
  - Notes / evidence:

- [ ] **12. Collect busy and controlled-disruption sessions**
  - Document traffic settings, disruption actions, actual onset, restoration, and observation windows.
  - Notes / evidence:

- [ ] **13. Check every session immediately**
  - Confirm complete logs, valid measurements, and matchable outcomes before continuing to further collection.
  - Notes / evidence:

- [ ] **14. Build and review the preliminary dataset**
  - Check the current planning targets: at least 300 usable labelled link observations across at least six sessions, including both outcome classes. The current checker also targets at least 20% Danger examples. These are coverage targets, not guarantees of adequacy; retain real outcomes and never fabricate labels to meet a percentage.
  - Notes / evidence:

- [ ] **15. Collect missing evidence and back up files**
  - Repeat unusable sessions and address missing conditions. Preserve original logs, setup notes, anomalies, and exclusion reasons.
  - Notes / evidence:

**Ready for Day 3 when:** verified examples cover the required conditions and support separate training, validation, and testing sessions. A logged-row count alone is insufficient.

## Day 3 — Train, verify, and freeze CART

- [ ] **16. Finalise the dataset**
  - Resolve exclusions, missing values, outcome labels, and session identities. Preserve the original source files and record dataset provenance.
  - Notes / evidence:

- [ ] **17. Prepare separate data partitions**
  - Keep whole sessions separate for training, validation, and held-out testing. Do not tune against the held-out test results.
  - Notes / evidence:

- [ ] **18. Verify the training settings**
  - Check feature definitions, tree settings, and threshold-selection rules against the methodology. Resolve the outstanding threshold tie-break issue before final training.
  - Notes / evidence: Reviewed 2026-10-27; see [CART TRAINING SETTINGS REVIEW.md](CART%20TRAINING%20SETTINGS%20REVIEW.md). Recorded actual feature units, tree defaults, whole-session outer/inner partitions and validation-only threshold tuning. Corrected equal-F1 threshold selection to prefer higher Danger Recall; five direct selector checks and all 49 combined software checks pass. The feature warning no longer suggests that selecting a LiPo build alone verifies measurement. Full training was not run; battery inputs, hardware label/timing verification and full ML runtime remain pending. Keep the parent task open.
  - [x] Current software settings reviewed and documented.
  - [x] Threshold tie-break corrected and software-tested.
  - [ ] Full training runtime and final dataset readiness verified.

- [ ] **19. Train and validate CART**
  - Review Recall, F1-score, the confusion matrix, and missed risky links. Report held-out results separately from training and validation results.
  - Notes / evidence:

- [ ] **20. Decide whether the model is ready**
  - Review the evidence against the agreed acceptance criteria. Address data or model problems before freezing. If held-out results guide revisions, document that use and obtain fresh independent test evidence as needed.
  - Notes / evidence:

- [ ] **21. Export and verify the model on the ESP32**
  - Confirm that firmware predictions match the exported model for representative inputs, including threshold boundaries where practical. Verify required inputs are available during operation.
  - Notes / evidence:

- [ ] **22. Freeze and back up the model package**
  - Save the dataset, session partitions, model header, threshold, reports, training settings, seed, and firmware revision. Record a model version and freeze date.
  - Notes / evidence:

**Finished when:** the model is validated, works on the ESP32, and its exact version and supporting evidence are saved. Independent evaluation runs come next.

## Task 1 review completed 2026-10-26

This is a blocker register and evidence record. Implementation remains under the existing items in [FIRMWARE TASKLIST.md](FIRMWARE%20TASKLIST.md); this review adds no duplicate implementation checklist.

### Blockers before final training collection

| Finding | Current evidence and required resolution | Existing firmware task reference | Training task |
| --- | --- | --- | --- |
| Battery feature is not validated for the actual power setup | `src/main.cpp` selects `BATTERY_SOURCE_LIPO` and reads Heltec VBAT using GPIO1/GPIO37. The reported external shield powers Heltec through USB; this does not establish a cell-voltage measurement path. Displayed nonempty percentages are not proof of actual shield charge. Verify the physical sensing path and calibration, or explicitly settle a revised feature set and matching methodology. | Priority 4 — Resolve battery sensing | 2 |
| Deployed sender and receiver evidence is not yet demonstrated | `capture_telemetry.py` records USB serial streams. The indoor file has only node 1 records; it has no V2 NEW or data TX records. V1-only capture cannot reconstruct every directed relay-link attempt. Establish and pilot a practical arrangement for all required endpoints without unintentionally changing battery operation. | Priority 3 — Clarify dashboard history and preserve complete records; Readiness Gate — preserve complete source/receiver logs | 3 and 8 |
| Labels still describe ACK outcomes rather than reconciled receiver outcomes | `build_cart_dataset.py:data_rows()` assigns Safe from ACK and Danger from NOACK or a sufficiently long absence of ACK. It does not match intended-receiver records. Lost ACKs, disconnected loggers, delayed delivery and actual failed reception must be distinguished. | Priority 4 — Complete receiver-side label reconciliation | 4 |
| Meaning of successful reception and identity of an attempt need definition | Firmware RX `to_me` is logged before duplicate, body-validation, TTL and forwarding-queue checks. Relay acceptance has no explicit success event after queue insertion. Decide whether the target is authenticated radio reception or valid receiver acceptance, and record the evidence required for that definition. The dataset builder matches outcomes using file/node/origin/id/peer and a 60-second window; repeated attempts can share those keys and overlap. Verify unambiguous attempt matching, reset boundaries and duplicate handling before assigning labels. | Priority 4 — Complete receiver-side label reconciliation; Priority 5 — duplicate handling and log completeness | 4 and 8 |
| Time and session metadata need a verified deployed procedure | Capture can send each node a time command, but PC read timestamps and a time-setting command alone do not establish cross-laptop clock accuracy. The indoor check used `--no-time-sync`. Boot CONFIG is emitted by firmware, but the saved check contains none; the default data-training loader excludes unknown configurations. Capture CONFIG for every node, use shared physical-session identities, document resets and verify the time reference used for matching and observation windows. | Additional Findings — Make latency measurements trustworthy; Readiness Gate — freeze firmware, radio settings and procedure | 3, 5 and 8 |
| Completeness of logs needs a pilot under the intended conditions | `logCsv()` silently returns if its mutex cannot be acquired within 50 ms. The capture tool skips CSV rows with an unexpected column count and flushes files every ten accepted rows. These are potential missing-evidence paths, not demonstrated causes of loss in the indoor test. Verify clean stop, connection continuity, malformed-row handling, missing-event detection and retention under representative traffic before treating absence as loss. | Priority 3 — Clarify dashboard history and preserve complete records; Priority 5 — log completeness; Priority 4 — receiver-side label reconciliation | 3, 4 and 8 |

### Existing policy issue to settle for the collection protocol

The firmware has both immediate no-route dropping and a bounded failed-hop policy in non-DTN configurations. Record and align the intended Baseline policy under **Priority 1 — Resolve the no-route/retry policy**. A message dropped before any data TX is a system-delivery outcome, not automatically a labelled radio-link attempt. The collection protocol must keep those cases distinct.

### Required later but not a reason to delay otherwise valid training raw logs

- **Before final training:** fix the threshold tie-break under **Additional Research-Readiness Requirements — Correct the CART threshold tie-break**. The current script breaks equal-F1 ties by closeness to 0.5 rather than higher failure-class Recall. Tracked at training Task 18.
- **Before collecting independent evaluation evidence for the affected metrics:** validate actual PQA queue-entry events and independent Baseline shadow-mode classifier evaluation with paired receiver outcomes. The user selected this method on 2026-10-27 to replace dual-transmission probes; use newly collected sessions after model freeze, never development sessions. See `Code/Thesis/docs/AVOIDED_LINK_EVALUATION.md`. These belong to the corresponding existing firmware tasks.
- **Before final analysis:** complete the planned statistical analysis. This does not by itself block otherwise valid raw training collection.
- Dashboard layout, wording and access-control tasks remain open in the firmware tracker. Their unresolved status must be considered before public or resident use; they do not substitute for sender/receiver evidence in a controlled team collection pilot.

### Verified evidence retained from the indoor test

- Source: `Range Survey Logs/logging_check_20261024_181105.csv` and its `_raw.log` companion, relative to this Documents folder.
- Confirmed 25 unique node 1 DELIVER records from origin 2, IDs 8597 through 8621, with numbered message text retained in the raw log.
- CSV events present: BATT 26, DELIVER 25, HB_MISS 2, HB_OK 49, RX 74, TX 74. All are node 1 records. There are no CONFIG or NEW records. Node 1 TX records in this file are heartbeats and acknowledgements, not the origin's data TX examples.
- Conclusion: complete retention of these 25 hub deliveries is verified. The dashboard's buffer limit does not limit the saved file. Deployed per-link training capture, battery validity, outcome labels and timing are not established by this test.

### Next action

Task 2 is deferred at the user's request pending a multimeter and physical sensing verification. Proceed with independent **Task 3 — Prepare sender and receiver logging**. Return to Task 2 before final four-feature training collection; calibration alone cannot make a USB-powered VBAT reading represent the external cell.

## What one training example contains

| Component | Required value |
| --- | --- |
| Input 1 | Neighbour RSSI in dBm, available before transmission |
| Input 2 | Neighbour SNR in dB, available before transmission |
| Input 3 | Verified neighbour battery estimate in percent |
| Input 4 | Neighbour data-backoff count per 30-second heartbeat window |
| Outcome | Verified outcome of the corresponding data transmission to the intended next hop, under the agreed labelling rule |

Heartbeats supply neighbour information. Baseline data transmissions supply the outcomes for the current training plan. Collect both during the same sessions. Keep delayed delivery and missing evidence separate from confirmed loss according to Task 4.

## After this checklist

Collect new independent evaluation runs for Chapter 5. The current field-test plan specifies five configurations, three traffic tiers, and ten repetitions, totalling 150 runs. Confirm the protocol and readiness of each measurement before those runs.

Those runs support five main metric groups: delivery rate, delivery latency, priority handling, classifier performance and paired heuristic comparison, and battery voltage decline. They are separate from model training.

## Progress notes

| Date | Task | Work completed or issue found | Evidence or file | Next action |
| --- | --- | --- | --- | --- |
| 2026-10-26 | 1 | Review completed; collection blockers separated from later training and evaluation requirements. No firmware or script edits. | Task 1 review above; current firmware tracker and scripts; indoor capture files | Task 2 — Verify actual battery measurement |
