# Field Test Plan - LoRa Mesh, Barangay San Miguel

Updated 22 October 2026. This procedure is maintained with the firmware.
Run commands from the folder containing `platformio.ini` (`Code/Thesis`).
COM ports below are examples: replace them with the node-to-port map.

### Two-node V1–V6 distance survey (27 October update)

Use `survey-n1` and `survey-n6`, not the formal Baseline builds, for a direct
V1–V6 survey with the other four boards off. The planned topology excludes this
direct link, even when heartbeats are received. Survey builds permit measured
links and report configuration `range-survey`; FIFO/no-DTN/no-filter behaviour
is retained. Formal experiment builds still enforce the planned topology.
Use `--expected-config range-survey` when capturing survey firmware. First verify
three unique V6 reports at V1 at close distance, then conduct the distance survey.
Keep these engineering results separate from formal Baseline training sessions.

## 1. Separate the three stages

1. **Engineering checks:** range, placement, portal, routing, buffering and queue behaviour.
2. **Training-data collection:** Baseline data packets with pre-decision neighbour features and sender/receiver logs.
3. **Independent evaluation:** frozen model and firmware; five configurations, three tiers, ten trials per tier/configuration.

Do not train or tune on the independent evaluation sessions. Site checks can proceed
while unresolved measurement features are being completed, but cannot substitute for
protocol-complete training/evaluation data.

### Readiness requirements

- **Battery sensing (part e) remains unresolved.** The actual setup is a 3.7 V,
  2000 mAh KC18650 Li-ion battery with Battery Shield V3, connected through a
  switched USB extension and USB-A-to-USB-C cable to the Heltec USB-C port.
  The firmware reads the Heltec VBAT circuit; this does not measure the shield cell
  through USB. Verify a sensing arrangement before battery-feature collection.
  Do not describe this setup as a directly connected LiPo/JST battery.
- **Ground truth (task 28):** the dataset builder currently uses ACK/NOACK outcomes.
  Implement intended-receiver reconciliation and the confirmed-loss, delayed-delivery,
  logger-failure and missing-evidence categories before final training. A missing ACK
  alone does not prove that the receiver missed the data packet.
- **Classifier ground truth (task 26, revised 27 October):** use new independent
  Baseline shadow sessions after model freeze, with paired receiver outcomes.
  No outcomes are assigned to untried avoided links. See docs/AVOIDED_LINK_EVALUATION.md.
- **Threshold tuning (task 27):** align tied-F1 selection with the paper's higher-recall
  rule before freezing the model. The current script prefers proximity to 0.5.
- **Statistics (task 13, software prepared 28 October):** significant eligible
  Kruskal-Wallis tests now lead to tie-corrected Dunn-Bonferroni comparisons of
  all ten formal configuration pairs within each metric/tier. Tests/statuses are
  saved separately. McNemar requires the independent Baseline plan and reviewed
  receiver outcomes. Physical verification, metric validity and sampling-design
  review remain pending. See docs/STATISTICAL_ANALYSIS.md.

## 2. Flash configuration-specific builds

Every node in a run must use the same configuration, with its own node ID:

| Configuration | Build environments | Queue | Relay assessment | DTN |
| --- | --- | --- | --- | --- |
| Baseline | `baseline-n1` ... `baseline-n6` | FIFO | None | Off |
| Partial | `partial-n1` ... `partial-n6` | Min-Heap | None | Off |
| Heuristic | `heuristic-n1` ... `heuristic-n6` | Min-Heap | Static rule | Off |
| Ablation | `ablation-n1` ... `ablation-n6` | Min-Heap | Static rule | On |
| Full | `full-n1` ... `full-n6` | Min-Heap | CART | On |

`node1` ... `node6` are development builds, not the formal Baseline. Full builds
require the trained `include/cart_model.h`; do not insert a dummy model.

Example: flash one connected board at a time for Baseline collection:

```powershell
pio run -e baseline-n1 -t upload
pio run -e baseline-n2 -t upload
pio run -e baseline-n3 -t upload
pio run -e baseline-n4 -t upload
pio run -e baseline-n5 -t upload
pio run -e baseline-n6 -t upload
```

With multiple boards connected, select the corresponding port explicitly:

```powershell
pio device list
pio run -e partial-n3 -t upload --upload-port COM5
```

Label V1-V6 and record firmware revision, environment, model/header version,
library versions, radio settings and topology mask. V1 is the Main Hub; V2-V5
are Mini Hubs; V6 is the Distant Edge Node. Verify each boot CONFIG record.
The capture tool does not reset boards on connect: start capture, then press RST
on every node to include CONFIG records. Never open two programs on one COM port.

## 3. Power, sensing and equipment

Bring six nodes with antennas fitted, charged battery/shield sets, enclosures,
laptops/loggers, verified data cables, phones, a multimeter, site map and field sheets.
Verify every battery/switch/cable connection and record the power source of each node.

After a valid cell-voltage sensing path exists, compare it against a multimeter,
use `battery cal <measured volts>` per node, and check the `battery` report.
Calibration cannot fix an absent sensing connection. Verify valid BATT records at
startup and approximately every minute, plus neighbour battery telemetry in heartbeats.
The current battery percentage is a voltage-based estimate (3.30 V -> 0%,
4.20 V -> 100%), not directly measured remaining capacity.

Battery-shield USB power differs from laptop USB power. Voltage-drop measurements
require the measured battery to power the node without external power or charging.
The analysis does not automatically exclude laptop-powered nodes. Establish a
logging arrangement that does not unintentionally power the measured node; the
current USB capture tool does not itself solve that hardware requirement.
Do not replace missing battery data with 100% or silently drop the battery feature.

## 4. Roles and site record

| Role | Responsibility |
| --- | --- |
| Hub operator | V1 logging and destination arrivals |
| Sender/operator | Phone submissions or traffic injection and source records |
| Node crew | Positioning, configuration checks and controlled disruptions |
| Recorder | Run IDs, positions, power sources, faults and timing |

The current topology mask permits V1-V2, V1-V3, V1-V4, V2-V4, V2-V5,
V3-V5, V3-V6 and V5-V6. Keep it fixed across comparisons. Record node
GPS/landmarks, antenna heights, obstructions and route matrices. Maintain separate
team coordination when the test network is deliberately disrupted.

## 5. Preliminary engineering checks A-E

These are separate from the 150 formal evaluation runs. Record actual outcomes;
do not assume every message arrives or promise a fixed recovery time.

### A. Range survey - Baseline

Power only V1 and V3. At measured positions, wait at least two minutes and record
RSSI, SNR, heartbeats, antenna height and obstructions. Submit labelled portal
messages and match origin/ID to V1 arrivals. A local reference ID or hop ACK is
not proof of hub delivery. Baseline has no DTN: a dropped out-of-range message
is not expected to reappear automatically when the sender returns.

### B. Planned-link check - Baseline

Place all six nodes and allow about ten minutes for initial link-state propagation.
Run `routes` and save the matrix. Reposition and recheck unusable planned links
(weight 255). Freeze positions for subsequent comparisons; document any changes.

### C. Portal and multi-hop delivery - Baseline

Submit three labelled messages per origin V2-V6. Record source references,
priorities, routes and confirmed hub arrivals. Capture source and destination logs.
With hub-only capture, use a source submission sheet for manual PDR; the script
cannot infer the denominator without source NEW records. Measure latency only
with a documented common time reference and stated clock uncertainty.

### D. Rerouting and buffering - Ablation

Use `ablation-n1` ... `ablation-n6` to test DTN before training CART.
Use `silent on` on a selected relay, then `silent off` after a fixed 60-second
disruption. Record actual silence onset: an in-progress transmission finishes first.
First test an available alternate path; separately isolate both planned neighbours
of V6 to test no-route buffering. Record STORE, FORWARD, DROP/EVICT, ACK/NOACK,
routes and hub arrivals. Restore all radios afterwards. A serial monitor and capture
cannot share a port: settle command/control logging before formal trials.

### E. Priority handling - Partial

Queue k=3, k=2 and k=1 messages at the same node. Use local logs to check
whether any less urgent data TX occurs strictly between each k=1 entry record
and its first TX. Use accepted ENQUEUE records, never RX/NEW as inferred queue
admission; require continuous node/boot log sequences. See `docs/PQA_LOGGING.md`.
Do not calculate PQA from heap Index 0, queue_index or hub
arrival order. A lower-priority transmission begun before entry is not a violation.

## 6. Test F - Baseline data-packet collection

Flash all six Baseline builds. Generate data packets; passive heartbeat-only
recording is not the chosen training source. Heartbeats supply neighbour features;
HB_OK/HB_MISS are diagnostic. Features are RSSI, SNR, estimated battery percentage
and neighbour data-backoff count. Verify battery sensing before the final collection.

Capture sender and intended-receiver records with CONFIG metadata and a usable
common time reference. Do not compare local `ms` values between different nodes.
Retain RX `to_me`/`overheard` details; another node overhearing a packet is not
intended-receiver delivery. Save setup records but select a settled observation interval.

Example (add all relevant node ports; do not inject at V1):

```powershell
python tools/capture_telemetry.py COM8 COM5 COM6 --inject COM5 --every 30 --session baseline-F01-normal --out baseline-F01-normal.csv
```

Start capture before resetting nodes to include their CONFIG records. Continuous
injection starts automatically, so exclude startup traffic from the analysed interval.
Use normal, obstructed/weak, distant, busy and controlled-failure sessions across
multiple sending nodes and links. One physical collection session uses the same
session ID across node files; a different port alone does not define a new session.

Target at least 300 usable labelled observations and multiple independent sessions
(the current report checks at least six and 20% Danger). These are planning targets,
not guarantees of adequacy. Do not discard successes or fabricate failures to reach
a target. Collect and retain the full condition-specific observations.

Do not use `--target` as the eligible training-record count: it mixes heartbeat and
ACK/NOACK events. Use documented session windows. Record at least 60 seconds
beyond the last analysed data transmission and retain later arrivals for delayed
classification. An incomplete observation window is not a confirmed loss.

```powershell
python tools/build_cart_dataset.py baseline-F*.csv --coverage coverage.json --out cart_dataset.csv
```

Configuration metadata now identifies Baseline data candidates. Missing/mixed CONFIG
records are not accepted by default training. **Receiver reconciliation is now
implemented in software, but paired hardware verification is pending.** Review
the target and measured clock/observation bounds before creating `coverage.json`;
see `docs/RECEIVER_LABELS.md`. Safe (0) means uniquely matched timely next-hop
acceptance. Danger (1) requires completed transmission and verified non-reception
under reviewed complete observation. Rejection, delay, logger failure, uncertain
matching and missing evidence remain separate audit categories. Without coverage,
data candidates remain unlabelled; the diagnostic heartbeat rows are not a substitute.
New firmware logging must be flashed and tested on participating endpoints before
this pilot. Its packet layout is unchanged. Old hub-only delivery logs remain useful
for PDR checks with source submission evidence, but do not establish per-link labels.

## 7. Train and freeze CART

Only after the sensing and label requirements above are met:

```powershell
python tools/train_cart.py cart_dataset.csv --train-source data --split session --features rssi,snr,battery,traffic --out-dir cart_output --header include/cart_model.h
```

Training retains original feature units, Gini, maximum depth 5, minimum split size
10 and balanced classes. Whole sessions form the outer approximately 80/20
training/test split; an internal session split tunes the threshold. Invalid session
splits stop training; do not bypass this by splitting adjacent rows.

The Recall tie-break is corrected and software-tested: equal validation F1
prefers higher Danger Recall. Verify the full training runtime and final dataset
before fitting. Freeze the resulting header,
threshold, data, reports, seed and firmware revision before independent evaluation.
Alpha remains 2: the multiplier is `1 + 2 * Pf`, subject to integer rounding and
the firmware's weight limit. No sensitivity analysis is claimed.

Compile the same frozen model into all configurations for shadow logging. Only
new independent Baseline shadow sessions enter formal classifier comparison; the
five-configuration network trials remain separate. See docs/AVOIDED_LINK_EVALUATION.md.
Only Full uses it for routing; the others log CART in shadow mode. Missing model
inputs leave CART verdicts unavailable and cannot support a paired comparison.

## 8. Formal comparison: 150 runs

Five configurations x three tiers x ten repetitions = **150 runs**. Use the same
positions, origin, seed/run pairing, observation window and disruption protocol
for matched comparisons. Balance and record configuration order across trials.

| Tier | One batch per origin | k1 / k2 / k3 | Disruption |
| --- | --- | --- | --- |
| Low | 5 messages in the configured 5-second window | 2 / 2 / 1 | None |
| Medium | 15 messages in the configured 2-second window | 5 / 6 / 4 | None |
| High | 30-message burst, paced at >=50 ms per serial command | 15 / 9 / 6 | Origin radio silenced, restored approximately 60 s after the burst |

### Every run

1. Verify configuration/model and node/port mapping. Close competing monitors.
2. Start capture, then reset **all six** nodes to clear queue/DTN state and capture
   CONFIG. For tier runs, do this promptly within the 120-second start delay.
   If startup takes longer, abort/restart or set a longer delay consistently for
   every configuration. Do not inject before routes have settled.
3. Record source NEW, relevant TX/RX and classifier verdicts, ACK/NOACK, DTN
   events and hub DELIVER. Include every relevant node port.
4. Inject one batch at one selected origin. More injection ports multiply the
   workload and require a revised protocol. Keep seed and run numbers matched.
5. Record for a fixed observation window established by pilot runs. Examples use
   600 seconds after the last scheduled command. Keep the same window across
   configurations; do not stop early because some messages arrived.
6. Restore silenced radios, save evidence and reset all six nodes before the next
   run. Retain aborted trials and document any replacement runs.

Example: Baseline trial 1, V6=COM5. COM8/COM6 are additional example capture
ports, not an assertion that three ports cover the whole topology. Add the rest.

```powershell
python tools/capture_telemetry.py COM8 COM5 COM6 --inject COM5 --tier low --run 1 --seed 2026 --start-delay 120 --stop-after 600 --session baseline-low-run01 --out baseline_low_01.csv
python tools/capture_telemetry.py COM8 COM5 COM6 --inject COM5 --tier medium --run 1 --seed 2026 --start-delay 120 --stop-after 600 --session baseline-medium-run01 --out baseline_medium_01.csv
python tools/capture_telemetry.py COM8 COM5 COM6 --inject COM5 --tier high --run 1 --seed 2026 --hold 60 --start-delay 120 --stop-after 600 --session baseline-high-run01 --out baseline_high_01.csv
```

These are three separate runs, each with the reset procedure. For the other four
configurations, change both the flashed environments and session/output names.
Repeat trial numbers 1-10 per tier. Do not add an unplanned relay disruption to
these tier runs; define any additional disruption scenario separately and match it.

For High, inspect actual STORE/FORWARD and failed-attempt/DROP evidence.
Configurations 1-3 have no DTN and use a three-failed-attempt policy. Ablation and
Full buffer subject to capacity/eviction/expiry. Do not assume all injected messages
were accepted or stored: retain NEW, rejection, EVICT and DROP evidence.

More precisely, configurations 1-3 drop immediately if no usable route exists.
The three-failed-hop budget applies while a usable route remains; channel-access
deferrals are separate. Failed-hop counters are local to queued messages. See
`docs/MESSAGE_HANDLING_POLICY.md`. Reports submitted directly on V1 are local
deliveries and must not be mixed into the planned radio evaluation workload.

### Manual portal-intake subset

The methodology specifies 10% of the ten Baseline low-tier runs: **one manual
run**. Disable automatic injection and submit five messages with the same 2/2/1
priority counts. Record input timing/order and origin/IDs. Example capture:

```powershell
python tools/capture_telemetry.py COM8 COM5 COM6 --session baseline-low-manual-run01 --out baseline_low_manual_01.csv
```

Identify it as manual; do not silently equate its workload timing with an automated
run. Finalise its position within the 150-run schedule before evaluation and use
matching input methods for workload-effect comparisons.

## 9. Analysis and evidence

```powershell
python tools/analyze_run.py baseline_low_01.csv
python tools/analyze_run.py evaluation/*.csv --compare
```

Use one complete run per comparison CSV. Review resets, clock accuracy and missing
source/receiver records first. The software produces conditional Dunn-Bonferroni comparisons, but outputs
do not by themselves certify metric validity or the independence of runs.
See docs/STATISTICAL_ANALYSIS.md for saved files, eligibility and exclusions.

- PDR uses unique hub arrivals and unique source messages; lost ACKs do not cancel
  confirmed delivery. Preserve session, origin and message identifiers.
- Report latency with corresponding PDR/priority and the time-reference uncertainty.
- PQA uses local entry-to-first-TX order, not heap index or hub arrival order.
- Compare CART/heuristic correctness only on planned independent Baseline shadow
  sessions with reviewed receiver outcomes and the frozen model identity. Use
  --classifier-plan and --coverage; no ACK-based fallback exists.
- Use the first attempt per message/hop, audit exclusions, and review independent
  sampling before interpreting McNemar. Do not label untried avoided links.
- Voltage-drop analysis needs eligible calibrated cell readings over continuous
  sessions (currently at least five minutes). Exclude externally powered intervals
  before analysis; the rate does not establish energy consumption or full lifetime.

Retain CSV and `_raw.log` files, models/reports, build identity, node/port and power
maps, positions, routes, run order, manual submissions, anomalies and exclusions.

| Session/run | Configuration/model | Tier/condition | Origin | Node/port map | Start/end | Power sources | Faults/exclusions | Files |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| | | | | | | | | |

| Time | Node | Position/height | Action | Origin/ID | Priority | Intended next hop | Actual reception/route | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| | | | | | | | | |

## 10. Field precautions

Keep antennas attached whenever powered. Use radio-silence commands for controlled
link failures; power removal is a different scenario because it resets the node and
erases volatile buffers. Restore all radios after checks. Keep boards/connectors dry.
If a COM port is busy, close the other monitor/capture. If the portal does not open
automatically, open `http://192.168.4.1` manually and record the issue.

This plan update does not certify unresolved sensing, paired hardware or statistical
features. Chapter V and hardware costs are outside its scope.
