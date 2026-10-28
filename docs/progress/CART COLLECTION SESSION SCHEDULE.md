# CART Collection Session Schedule

Prepared 2026-10-27 for CART Task 9. Status: solo draft ready; confirm positions, endpoint coverage, timing and traffic amounts after the pilots. This is training collection planning, separate from the 150 independent evaluation runs.

## Before starting final collection

- Verify actual battery sensing and calibration for the intended four-feature model.
- Complete the indoor paired logging check, multi-laptop timing checks, distance survey and deployed pilot.
- Flash matching updated Baseline builds on all six nodes and save boot CONFIG records.
- Confirm node positions, antenna heights, directed routes, power arrangements and the recording coverage of participating endpoints.
- Agree on the analysed interval, acceptance deadline, observation tail, traffic schedule and uncertainty budget using the pilot. Do not invent these values to complete this sheet.

Power banks may support preliminary checks, but unverified battery percentages are not final four-feature training observations. A laptop connected over USB can change the node's power arrangement; resolve and document that before battery-dependent collection.

## Group roles

| Role | Responsibility |
| --- | --- |
| Coordinator | Announces session name, verifies readiness, records condition changes, and collects all files |
| Laptop operators | Confirm assigned node/configuration, record continuously, report interruptions and preserve files |
| Traffic operator | Runs the agreed traffic source or sends the agreed pilot messages and records references |
| Condition operator | Documents obstruction or controlled disruption, its actual onset and restoration |

One person can perform more than one role when feasible. Assign names at the group meeting.

## Four laptop coverage draft

| Assignment set | Laptop 1 | Laptop 2 | Laptop 3 | Laptop 4 |
| --- | --- | --- | --- | --- |
| A | V1 | V2 | V3 | V4 |
| B | V1 | V4 | V5 | V6 |

These sets are provisional recording assignments, not asserted routes. Keep all six node positions fixed for the collection series unless a planned condition explicitly changes them. Rotate the recording equipment between sets, document USB/power changes, and obtain new boot/timing evidence when necessary.

Before using either set, inspect actual directed transmissions. A candidate link is eligible only when its sender and intended receiver are recorded with usable evidence. For example, a V6-to-V5 attempt is not independently verified while only set A is recorded. Neither set covers every possible pair; if the pilots reveal important uncovered links, revise the sets or add a session. Do not silently force routing merely to fit the laptop assignments.

## Proposed first six sessions

Run these only after the readiness checks. The schedule provides varied conditions and recording coverage; it does not guarantee 300 eligible labels or adequate model performance.

| Order | Shared session name | Condition | Provisional coverage | What to document |
| --- | --- | --- | --- | --- |
| 1 | baseline-F01-normal-A | Normal intended deployment | A | Positions, routes, source and endpoint coverage |
| 2 | baseline-F02-normal-B | Normal intended deployment | B | Independently started observation; source and eligible links |
| 3 | baseline-F03-weak-A | Selected weak or obstructed link | A or revised set covering that link | Exact obstruction/location change, signal readings and actual outcomes |
| 4 | baseline-F04-weak-B | Another weak link or repeated weak condition in a separate session | B or revised set | Exact condition, independent start and covered endpoints |
| 5 | baseline-F05-busy | Increased data traffic | Set selected from actual busy links | Source nodes, pacing, payload, priorities and observed backoff counts |
| 6 | baseline-F06-disruption | Controlled temporary radio disruption | Set covering the disrupted receiver and its sender | Actual silence/restoration times, continued receiver logging and resulting outcomes |

Different filenames, ports or laptop operators alone do not make independent sessions. Record a distinct physical observation period and its actual conditions. Repeat or add sessions when the dataset review identifies inadequate coverage; six is a planning minimum, not an instruction to stop regardless of the evidence.

Choose origins from the actual pilot topology; do not inject messages at V1. Automated traffic can reduce manual work, but the agreed pacing and number of active origins must avoid an accidental unplanned burst. Do not run the guided manual recorder and a second program on the same serial port. Prepare the automated command for the final agreed assignment rather than guessing ports.

Controlled disruptions are real experimental interventions, not simulated battery values. Keep them separately identifiable. An abruptly silenced receiver can fail without a predictive change in the four inputs; do not assume the classifier can anticipate every such event or pool these sessions without reporting their role. Do not fabricate low signal/battery readings or alter labels to improve scores.

## Repeat this procedure for every session

1. Announce the shared session name and condition to all operators. Record the expected node/laptop/port map and actual power sources.
2. Perform the common-reference checks and start the required node captures. Capture and verify boot CONFIG; allow discovery and obtain timing evidence before the analysed interval.
3. Record an explicit start of the analysed interval. Start the agreed data traffic; heartbeats continue automatically. Save the actual origin/ID and link attempts.
4. Document condition changes, receiver silence/restoration, resets, malformed rows, disconnects and manual submission failures. Do not silently replace failed trials.
5. Stop traffic at the agreed end. Continue all required recordings through the fixed observation tail and final timing samples. Restore any deliberately silenced radio.
6. Stop recording cleanly, run the final reference comparisons and preserve every CSV, raw, clock and setup file. Keep a separate record of the analysed interval and actions.
7. Review configuration, continuity, input validity and reconciled outcomes before proceeding. Unobserved or ambiguous attempts remain unknown. Back up originals and report excluded candidates.

## Fields to finalise after the pilot

| Setting | Agreed value | Supporting pilot evidence |
| --- | --- | --- |
| Node positions and heights | Pending | |
| Actual directed links and coverage sets | Pending | |
| Data-message origins per condition | Pending | |
| Priority pattern and payload size | Pending | |
| Traffic interval or schedule per condition | Pending | |
| Number of submissions or analysed duration per session | Pending | |
| Discovery/readiness check | Pending | |
| Acceptance deadline and capture tail | Pending | |
| Timing reference and uncertainty | Pending | |
| Actual battery sensing and logging power setup | Pending | |
| Location of file backups | Pending | |

Do not calculate collection time by assuming one message equals one usable training row. Count verified link-attempt examples after reconciliation. Never use the capture tool's diagnostic counter as the usable-label count.

## Dataset review before deciding collection is sufficient

- Current planning targets: at least 300 usable labelled observations and at least six physical sessions. The current checker also targets at least 20% Danger outcomes. Retain genuine outcomes and explain their distribution rather than manufacturing a percentage.
- Check conditions, links, originating nodes and exclusion reasons, not just the total count. Avoid repeatedly collecting only one easy link.
- Verify whole-session training/validation/test partitions can each contain both classes. One failure-only session cannot supply independent failure evidence to all three partitions. Add genuine observations across sessions as needed; do not rename or split one physical session to bypass this check.
- Keep the final held-out test sessions unused for threshold selection. If held-out results guide revisions, record that use and obtain fresh independent test evidence as needed.
- Training collection is complete only after these data-validity checks. Freeze the model afterward, then collect new formal evaluation runs.

## Session record

| Session | Actual condition and interval | Origins | Recorded nodes and eligible links | Power/timing evidence | Files and backup | Issues or follow-up |
| --- | --- | --- | --- | --- | --- | --- |
| | | | | | | |
