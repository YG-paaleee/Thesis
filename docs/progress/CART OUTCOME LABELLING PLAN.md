# CART Outcome Labelling Plan

Status: software implementation prepared and checked on 2026-10-26. Baseline V1 and V2 builds and 25 artificial software checks pass. Live verification, measured clock bounds, observation-window selection and final methodology alignment remain pending. No boards were flashed.

Related work: CART Training Task List Task 4 and FIRMWARE TASKLIST Priority 4 — Complete receiver-side label reconciliation.

## Purpose

Create training examples by matching the sender's pre-transmission neighbour features with evidence from the intended next-hop receiver. Heartbeat outcomes and hub-only arrival counts do not replace this matching.

## One example and its identity

One candidate example is one actual directed data-transmission attempt, such as V6 sending one frame to V5. A later V5-to-V1 transmission is another example. A retry is a separate attempt, not a new user message.

Retain physical session, node boot identity, originating node, original message ID, transmitting node, intended receiver, data type, attempt identity, transmission start/completion information, receiver outcome, and the corresponding four input values. Retain the reason for every excluded candidate.

The existing on-air header has a message ID but no unique transmission-attempt identifier. Its MAC-busy-retry field counts channel deferrals and is not a unique attempt number. The current sender CSV has no explicit unique attempt field. Do not claim exact per-attempt matching until the instrumentation or a verified unambiguous matching method supports it. Repeated identical transmissions may otherwise overlap in the current 60-second search window.

## Proposed outcome target

Recommended target for review: valid acceptance by the intended next hop, with underlying radio reception and acknowledgement outcomes recorded separately. At V1, acceptance is application delivery; at a relay, it is successful acceptance into forwarding custody. Confirm that this wording matches the manuscript before implementation.

Do not silently mix this target with merely detecting an authenticated radio frame. An addressed frame can be received and then rejected because of invalid content, expired TTL or a full forwarding queue. Those mechanisms need separate outcome reasons.

## Outcome categories

| Category | Evidence | Training treatment |
| --- | --- | --- |
| Timely accepted | A uniquely matched intended receiver accepts the valid frame within the agreed timing rule | Safe, label 0, once the target and rule are finalised |
| Confirmed non-reception | Sender transmission completion is evidenced, the receiver observation is demonstrably complete, timing/identity are unambiguous, and no matching frame reception is found | Danger, label 1, under the final agreed loss definition |
| Received but rejected | Receiver records the frame but cannot accept it; retain the specific reason | Separate category; do not present it as radio loss or assign a binary label until the target explicitly covers this mechanism |
| Delayed or ambiguous timing | A matching event is outside the agreed timing rule, or clock uncertainty prevents deciding which side of the boundary it falls on | Retain separately; no automatic binary label |
| Missing evidence | Disconnected logger, reset, incomplete recording, malformed/missing required events, missing configuration, uncertain identity or another observation gap | Unknown; exclude from final binary training labels and report why |
| Transmission not completed | No route, local submission rejection, radio start/completion error, or no demonstrated on-air attempt | Separate system outcome; do not automatically label it as over-air packet loss |

Absence from a file is not sufficient proof of non-reception. Define and verify the logging continuity checks used to establish the receiver observation interval. An alive node or occasional heartbeat alone does not prove that every required log event was saved.

## ACK and duplicate rules

1. Receiver acceptance with no sender ACK is still acceptance; record an acknowledgement-path failure separately.
2. An ACK with missing receiver evidence is not automatically an independent receiver-verified example. Keep it provisional under this collection design.
3. A receiver duplicate event can demonstrate reception of a retry only if it is uniquely matched to that retry. It must not create another application delivery.
4. Do not assign a later retry's successful reception to an earlier failed attempt.
5. Count each user message once for hub delivery rate, independently of the per-attempt training table.
6. Overheard frames at an unintended node cannot establish intended-receiver success.

## Timing rule to finalise under Task 5 and the pilot

Do not adopt the dataset builder's 60-second ACK search window as a validated receiver-loss deadline. The firmware waits for an ACK after data transmission completion using ACK airtime plus a 2.5-second guard; that is a different rule and does not by itself define independent receiver ground truth.

Record transmission start and successful completion, actual frame length/radio settings, receiver-event timing, and the estimated cross-device clock and logging uncertainty. Use these to define non-overlapping matching intervals and any acceptance deadline before final collection. A long final capture tail preserves evidence but is not automatically the definition of timely reception for an individual attempt.

If identity is explicit, some reception matching may be possible without precise clock synchronisation, but timed labels and confirmed absence still need defensible observation bounds. Keep boundary cases unknown rather than forcing a label.

## Gaps identified before implementation

The table below records the original design-review findings. See the implementation progress section for what is now implemented and what remains pending.

| Location | Current behaviour | Needed work before completion |
| --- | --- | --- |
| `src/main.cpp` receiver path | RX to_me is emitted before duplicate/body/TTL/forwarding-queue acceptance checks. V1 emits DELIVER; relay queue acceptance has no explicit equivalent event. | Add or establish evidence that distinguishes frame reception, acceptance, duplicate handling and rejection according to the final target. |
| `src/main.cpp` sender path | Data TX indicates a successful startTransmit call; completion failures are readable debug output. ACK and NOACK refer to message/peer without a unique attempt identifier. | Establish attempt identity and machine-readable completion/outcome evidence sufficient for unambiguous matching. |
| `tools/build_cart_dataset.py:data_rows()` | Labels from the first matching ACK/NOACK within 60 seconds; missing ACK becomes Danger when sender logging continues long enough. | Reconcile intended-receiver evidence, enforce session/boot/attempt boundaries, retain unknown/delayed/rejected categories, and export auditable identifiers. |
| `tools/capture_telemetry.py` and deployed capture procedure | USB records include PC read timestamps; malformed CSV rows are skipped and disconnects are printed. | Verify endpoint coverage and recording continuity; retain configuration, clock mapping, reset and gap evidence. |

## Verification cases

Exercise these first with explicitly artificial logic examples and later with controlled hardware tests. Artificial examples verify the processing logic; they are not measured field-training observations.

| Case | Expected treatment |
| --- | --- |
| Receiver accepts and sender gets ACK | One Safe attempt |
| Receiver accepts but ACK is lost | Safe reception/acceptance; separate ACK failure |
| Sender completes transmission but receiver records no reception in a verified complete interval | Confirmed non-reception according to the final rule |
| Receiver logger disconnects during the interval | Unknown, not Danger |
| First attempt fails and a later retry succeeds | Distinct outcomes, with no evidence reused between attempts |
| A different node overhears the frame | No success claim for the intended receiver |
| Receiver records a frame but its forwarding queue is full | Received but rejected; retain reason |
| Node reboots and message IDs or local uptime repeat | Separate boot identity; do not match across the boundary |
| Capture ends before the full observation interval | Unknown |
| Timestamp falls near a deadline within clock uncertainty | Ambiguous timing; retain separately |

## Implementation progress 2026-10-26

- Firmware now records boot/log-sequence metadata, local sender attempt numbers, frame fingerprints, TX_DONE/TX_ERROR and explicit RX_ACCEPT/RX_REJECT events. The radio packet format and CSV columns remain unchanged. Overlapping identical retries still require conservative exclusion; a frame fingerprint is not a wire-level attempt ID.
- `tools/receiver_labels.py` reconciles paired evidence against reviewed coverage and clock mappings. ACK loss alone cannot create a Danger label. Uncertain timing, missing evidence and receiver rejection remain separately auditable.
- The dataset builder keeps all candidate attempts in an audit CSV and requires verified receiver evidence for binary data labels. The training loader rejects legacy ACK-only data-label provenance. Missing traffic is no longer silently replaced with zero.
- The capture tool flushes each saved line and warns about malformed CSV rows. Counter values are identified as diagnostic outcomes rather than verified training labels.
- Verified: 25 software cases passed, including CSV input through the dataset command and the actual training-loader provenance guard. These fixtures are artificial logic checks, not field observations. Baseline V1 and V2 builds passed; existing web-library deprecation warnings remain. The full training executable was not run; its scikit-learn dependency is not installed in the selected bundled Python environment.
- The old indoor hub-only file was checked: no verified data training rows are generated. Its earlier delivery result remains valid for that logging test.
- Procedure and reviewed coverage-file schema: `Code/Thesis/docs/RECEIVER_LABELS.md`, relative to the thesis root. Timing values cannot be guessed or copied from the old ACK search window.

## Completion evidence

Task 4 remains unchecked until the target and timing rules are finalised, required recording and processing changes are implemented and checked, and actual sender/receiver pilot records reproduce the expected categories. Task 2 battery validity and Task 3 deployed endpoint coverage remain separate requirements.
