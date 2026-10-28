# Firmware and UI Progress Tracker

Last updated: 2026-10-28

## Status
Main task checkboxes mean all listed acceptance checks are complete. A checked software subtask means implementation and software checks passed; it does not claim an on-board test passed. Record hardware-dependent verification separately rather than hiding software progress behind an unchecked parent task.

## Current Focus
Close-distance retest 2026-10-27: both boards have the web-response fix and dedicated survey builds, which allow the direct V6–V1 link. User reported successful repeated page loads. V1 capture survey_close_20261027_193122 confirms all three reports V6#30200–30202 delivered and accepted, with no panic/reboot markers and one V1 boot token through more than two minutes after the last delivery. User confirmed all three reports are visible on the V1 dashboard; the close-distance delivery/dashboard check passed. This is a three-report engineering pass, not full reliability or research readiness. See `Code/Thesis/docs/WEB_SERVER_CRASH.md`.
User direction 2026-10-27: this is the primary implementation checklist. Priority 1, Priority 2 and Priority 3 software changes are prepared and checked. Priority 4 battery/receiver verification and Priority 5 readiness require hardware evidence and remain pending. Continue remaining software work in timing/live reliability and admin/resident usability, while retaining those physical checks. Four laptops are available; battery sensing still awaits a multimeter and a verified measurement path.

## Progress by section

| Section | Software progress | Remaining verification or work |
| --- | --- | --- |
| Priority 1 — Message Handling | Local V1 delivery and deterministic per-message failure counters implemented; policy documented; host checks and FIFO/heap builds pass | On-board local delivery, retry/failure scenarios, and manuscript insertion |
| Priority 2 — Access Controls | Hub-only authenticated admin routes and removal of the browser-exposed community credential implemented; software checks and builds pass | Provision a private V1 admin password through USB; verify HTTP access and persistence on boards |
| Priority 3 — UI Accuracy | Actual node-information endpoint, dynamic identity/radio/capacity, accepted-priority confirmation, recent-history scope and export labels implemented and JavaScript-checked | Actual-board metadata, priority and more-than-20-history checks |
| Priority 4 — Data Validity | Receiver reconciliation software and audit support prepared | Actual battery sensing, measured timing bounds and paired hardware verification |
| Priority 5 — Readiness Checks | Pending hardware/group work | Six-node bench tests, outdoor pilot and repeatability |
| Timing and live dashboard reliability | Timing tools prepared; dashboard/resident request timeouts, uncertain-retry handling and stale/empty/unavailable states checked in software; unverified clock differences labelled honestly | Actual delay and clock measurements; original intermittent API failure cause; device interruption checks |
| Barangay admin usability | Five-column/mobile layout, secondary technical details, accurate page counts/references and SOS meaning; 200-report RAM history with pagination and retained-history export implemented | Actual devices/admin review; 120+ arrivals, wraparound, reboot and runtime memory under traffic |
| Resident portal usability | Plain categories with explicit choice, local/queued status, timeout/uncertain retry controls, preserved text and UTF-8 limits; basic keyboard/zoom support | Actual phone/node submission, resident wording review and interruption/accessibility checks |
| Research readiness | Threshold tie-break verified; accepted PQA queue-entry logging and analysis implemented, host tests/builds pass | Physical PQA validation, independent Baseline classifier evaluation and final statistical analysis (software prepared) |
| Final readiness gates | Not passed | Complete relevant software and device checks; freeze only after evidence supports readiness |

## Verification Log

Dunn-Bonferroni software 2026-10-28: conditional pairwise testing added to analyze_run.py via posthoc_stats.py. SciPy 1.18.1 and scikit-posthocs 0.17.1 installed and recorded with capture/analysis dependencies. Formal five-configuration families retain all ten pairs per metric/tier; usable counts and skipped-test statuses are exported. Numerical tie/untied checks and final 98-test regression suite passed; comparison CLI output files also verified. No radio/firmware changes or Chapter 5 results. Actual experimental design/data review remains required.

Paper update confirmation 2026-10-27: user reports pasting the independent Baseline shadow-evaluation Chapter 4 changes. Insertion is recorded as user-confirmed, not independently checked against a newly saved manuscript. Model freeze and physical independent evaluation remain pending. Next available software task: Dunn post-hoc comparisons with Bonferroni correction.

Independent Baseline shadow method selected 2026-10-27: user approved replacing the probe method with new Baseline sessions after model freeze. Firmware now computes the paired verdicts before TX and logs generated model identity. Training export records header identity/hash and all development sessions. The analysis requires a reviewed classifier plan and receiver coverage, matching frozen model, Baseline configuration and new session names; first-attempt sampling prevents success-only retry selection. Exact paper edits and the procedure are saved. 84 regression checks and final baseline-n1/node6 builds passed; no boards flashed. Actual training/model freeze, manuscript insertion and physical evaluation remain pending.

PQA preparation 2026-10-27: accepted ENQUEUE logging and evidence-based PQA analysis implemented. Eleven final PQA/message-handling checks passed, including the actual queuePush wrapper with both FIFO and min-heap. Final baseline-n1 and node6 builds passed after event-time handling was added; diff whitespace check passed. Prior survey capture correctly produces zero eligible PQA samples. No boards flashed or physical priority performance claimed. Physical mixed-priority verification remains pending; see Code/Thesis/docs/PQA_LOGGING.md.

Close-distance delivery PASS 2026-10-27: survey_close_20261027_193122_raw.log records exactly one DELIVER and RX_ACCEPT for each V6#30200, V6#30201 and V6#30202 (Survey check 01–03), k=3, route V6–V1. One V1 boot token (1ddb3d2a), no panic/backtrace/reboot markers, and continued recording beyond two minutes after the final delivery. Capture stopped after review. User previously confirmed repeated page loads succeeded. User confirmed all three reports are visible on the V1 dashboard. V6 stability was not independently captured. No valid end-to-end latency is claimed from this unsynchronized receiver-only test.

V1 survey upload 2026-10-27: COM4 identity confirmed as V1 before upload; survey-n1 upload succeeded with flash hashes verified. Postflash V1 confirms radio ON, all measured links enabled and a measured V1–V6 edge of weight 1. Both boards now have survey builds. Capture survey_close_20261027_193122 started on COM4 for three-report retest; actual report delivery remains pending.

Survey correction verification 2026-10-27: real LinkStateDb/Dijkstra host test reproduces blocked V6–V1 routing with the mask and verifies the direct hop with the survey setting; lost measured links remain unroutable. survey-n1 and survey-n6 builds passed. COM4 identity rechecked as V6, survey-n6 uploaded with flash hashes verified. Postflash V6 reports `all measured links` and `Route to hub V1: next hop V1, total cost 1`. Evidence: V6-survey-postflash.log. V1 survey upload and three actual report deliveries remain pending.

Two-node survey blocker 2026-10-27: user reports page reloads succeed; V1 capture has no panic/reboot markers but no deliveries for V6#35622–35624. V6 serial evidence confirms it hears V1 with measured link weight 1 yet reports no route: the planned topology mask excludes V6–V1. Dedicated survey-n1/survey-n6 builds now permit measured direct links and use config name range-survey; formal builds retain their planned topology. Build/upload and three-report hardware verification must be recorded separately. See docs/WEB_SERVER_CRASH.md and Documents/Firmware Crash Evidence/2026-10-27/V6-delivery-listen.log. Earlier missing-message causes are not fully established without sender logs.

V6 update 2026-10-27: after the user switched USB boards, COM4 was queried and returned V6 before upload. Corrected baseline-n6 uploaded successfully; flash hashes verified and board restarted. V1 and V6 now both have the web-response fix. Reconnect V1 for capture, then verify repeated page loads and three numbered V6-to-V1 reports before resuming the distance survey.

Web response crash fix 2026-10-27: matching old ELF preserved and decoded; installed-library flash-response regression passed. baseline-n1 and baseline-n6 builds passed. COM4 queried and confirmed V1 before flashing; corrected baseline-n1 uploaded successfully with flash hashes verified. V6 USB connection/update and post-update page-stability/three-report delivery tests remain pending. This does not yet establish a hardware crash-free pass.

History pagination update 2026-10-27: actual firmware ring insertion/page-planner tests passed for 120 arrivals, all pages and 205-arrival wraparound. Dashboard checks passed for navigation, snapshot expiry/recovery, page/full-retained CSV export and interrupted-export rejection. Fictional browser preview confirms older-page navigation. Final node1, baseline-n1 and baseline-n2 builds passed; V1 static RAM is 150,220/327,680 bytes (45.8%), V2 remains 83,244 bytes. Runtime Wi-Fi/radio headroom and hardware acceptance checks remain pending; no boards flashed. This is a bounded RAM history, not durable complete storage.

Admin layout update 2026-10-27: five-column report view, mobile cards, expandable technical details, four aligned count cards and clear receipt wording implemented. Dashboard script checks passed for sorting/filtering, literal report text, disclosure persistence, recent-only export and error/stale/timeout recovery. Desktop and 390px browser previews reviewed with fictional samples. Baseline V1/V2 builds passed. Actual device/admin review pending; no boards flashed.

Input preservation update 2026-10-27: resident-script Unicode/boundary/edit-recovery checks and host tests of actual firmware submission limits passed. Local browser retained over-limit emoji text and showed the correct excess. Baseline V1/V2 builds passed. Actual phone-to-node-to-hub content verification remains pending; no boards flashed.

Resident language/category update 2026-10-27: explicit choice, three priority payload mappings and no-default reset passed controlled JavaScript checks. Local browser preview confirmed initially unselected controls, mouse selection, arrow-key selection and Clear form reset. Baseline V1/V2 builds passed. Actual phone/node acceptance and representative-resident wording review remain pending; no boards flashed.

Submission reliability update 2026-10-27: controlled resident-script checks passed for ten-second timeout, repeated clicks, explicit rejection, malformed replies, connection loss, retry cancellation/confirmation and subsequent successful recovery. Entered text and confirmed references are retained. Baseline V1/V2 firmware builds passed. No boards flashed; real phone/Wi-Fi interruption checks remain pending. The duplicate guard is limited to the current page session.
| Date | Task | Change made | Verification result | Remaining issue |
|---|---|---|---|---|
| 2026-10-27 | Priorities 1–2 | Local V1 intake; per-message retry counters; accurate no-DTN logs; authenticated V1-only admin; removed resident-page credential | 50 Python/host software tests passed; resident JavaScript checks passed; baseline-n1, baseline-n2 and node1 builds passed | Device/API/browser/persistence tests and paper insertion pending; no boards flashed |
| 2026-10-27 | Priority 3 | Live node identity/radio/capacity, recent vs recorded-since-restart scope, recent-only export, full references, honest timing and unavailable/stale states | Resident and admin JavaScript behaviour checks passed; generated web assets synchronised; baseline-n1 and baseline-n2 builds passed | Flashed-board verification pending; no data collection or flashing performed |

# Firmware and UI Task List — Before Formal Data Collection

## Priority 1: Message Handling

- [ ] **Fix messages submitted directly on V1.**
  - Record them as locally delivered and display them on the dashboard.
  - Verify: A V1 submission produces a reference, a delivery log, and one dashboard entry.
  - [x] Software: V1 records an incident immediately, emits NEW/DELIVER, returns `delivered_local` and does not queue a radio TX. A busy incident store returns an error. The portal distinguishes this from remote-node queue acceptance; no radio latency is assigned to local intake.
  - [x] Host logic checks and Baseline V1/V2 plus heap/DTN development builds passed on 2026-10-27.
  - [ ] On-board submission, one dashboard entry and no radio TX verified. Procedure: `Code/Thesis/docs/MESSAGE_HANDLING_POLICY.md` relative to thesis root.

- [ ] **Resolve the no-route/retry policy.**
  - Define when configurations without DTN drop immediately versus retry.
  - Align the firmware, paper, and test plan.
  - Verify: Logs show the expected attempts and drop reason for each failure scenario.
  - [x] Software/policy: no-DTN builds drop on no route; while a route remains, count failed hops per queued message and drop on the third counted failure. CAD deferrals are separate. Replaced the random eight-slot failure tracker with queue-resident counters covering all entries without changing queue order. NOACK logs now distinguish DTN holding from no-DTN drops/retries.
  - [x] Host checks cover both FIFO and heap queues, all 32 entries, origin-qualified identity, removal/reuse and policy decisions. Field-test plan and a manuscript wording proposal are prepared.
  - [ ] Actual no-route/retry/DTN scenarios verified on boards; manuscript wording inserted and reviewed. See `Code/Thesis/docs/MESSAGE_HANDLING_POLICY.md`.

## Priority 2: Access Controls

- [ ] **Restrict administrative access.**
  - Protect `/admin` and `/api/live_incidents`, and restrict them to V1.
  - Verify: Unauthenticated users cannot access incident data; relay nodes do not expose the dashboard.
  - [x] Software: `/admin` and `/api/live_incidents` share a V1-only authentication gate. Non-hub nodes return 404; V1 without provisioned credentials exposes no incidents. Private operator-set admin credentials are stored using Preferences; no default admin password is shipped. Incident API responses request no caching.
  - [x] Actual authorization helper passes host checks for relay denial, unset credentials, invalid credentials and accepted credentials; firmware builds pass.
  - [ ] Provision and verify login, API rejection, relay restriction and persistence on boards. Operator steps: `Code/Thesis/docs/ADMIN_ACCESS.md`. This password must be configured before expecting the newly flashed V1 dashboard to open.

- [ ] **Remove the exposed community passcode.**
  - Remove prefilled values, visible hints, and the hard-coded browser-side comparison.
  - Retain server-side validation.
  - Verify: Invalid credentials are rejected and valid credentials permit submission.
  - [x] Software: removed browser-side credential constant, prefill, example/default hints and reset value. The resident enters the operator-provided passcode; the existing server-side check remains. Error logging no longer dumps the credential-bearing payload. JavaScript checks confirm the page does not contain the server credential.
  - [ ] Valid/invalid credential submissions verified on a flashed board.

## Priority 3: UI Accuracy

- [ ] **Replace hard-coded node information.**
  - Display the actual node identity, radio state, and configured Wi-Fi capacity.
  - Verify: Different boards display their correct identities and operating states.
  - [x] Software: public `/api/node_info` returns operating metadata only. Resident page reads actual V1/V2–V5/V6 role/identity, ready/paused/unavailable radio state and configured/current Wi-Fi connection counts. Failed/invalid metadata shows unavailable, not a false active mesh. A ready radio does not claim a route or delivery. JavaScript checks cover roles, states, capacity and invalid data.
  - [ ] Actual node identities, paused/unavailable states and configured capacity verified on boards. See `Code/Thesis/docs/UI_ACCURACY.md`.

- [ ] **Correct the submission-priority confirmation.**
  - Display the priority accepted by the server rather than a selection changed during submission.
  - Verify: Changing the selection while a request is pending cannot produce an incorrect confirmation.
  - [x] Software: confirmation uses the server's accepted priority. JavaScript checks change the selection while the response is pending and confirm the accepted category is retained, for both queued and locally delivered responses.
  - [ ] Same interaction verified in an actual browser connected to a flashed board.

- [ ] **Clarify dashboard history and preserve complete records.**
  - [x] Pagination update 2026-10-27: V1 now retains the latest 200 report records in RAM and serves 20 per page. Older/Newer/Return-to-latest controls use stable snapshots with boot-session checks. Dashboard states that older entries are replaced after 200 and RAM clears on restart. Page counts/filter/sort scope is explicit. Separate page and all-retained-history exports include scope/session/snapshot; interrupted or expired exports do not download partial files. USB logs remain the complete experimental source, including sender/receiver evidence.
  - [x] Controlled JavaScript checks retrieve/export 120 records across six pages and test snapshot expiry, recovery and a 205-arrival/200-retained case. Host tests exercise the actual insertion function and page planner together, including ring wrap and record text. Local fictional browser preview confirms older-page navigation.
  - [ ] Hardware gate: verify 120 received reports across six pages/full export, more than 200 arrivals/oldest replacement, restart clearing/session expiry and runtime memory headroom under representative Wi-Fi/radio traffic. Do not treat a successful compile as proof of runtime capacity.
  - Identify the dashboard as a recent-incidents view.
  - Retain complete experimental records separately.
  - Verify: More than 20 arrivals remain available in the experimental logs, even when older dashboard entries disappear.
  - Progress 2026-10-26: The previous 25-message V1 capture verified retention beyond 20 arrivals. A shareable Windows logging kit now prepares timestamped recording files, session/node/laptop/power metadata, node/configuration checks and overwrite protection. Forty-four combined software checks pass; actual installation and deployed endpoint coverage on the group's laptops remain pending. No dashboard redesign has been completed by this work. See `GROUP LOGGING KIT.zip` in Documents and CART Task 3.
  - [x] Software update 2026-10-27: cards and export are explicitly recent-view only. Hub response headers report retention capacity and successfully recorded reports since restart, separately from retained rows. Added a labelled recent-report export button, scope column and full origin-qualified references. Complete experimental logging remains separate. An initial unavailable feed is not shown as zero, and a lost connection marks the retained view as stale. JavaScript checks simulate 20 retained out of 25 recorded reports, missing metadata, empty/error/stale states and recovery.
  - [ ] Updated firmware's counts/export scope and complete recordings verified together with more than 20 actual arrivals.

## Priority 4: Data Validity

- [ ] **Resolve battery sensing.**
  - Establish a measurement path for the actual shield battery.
  - Calibrate it and confirm valid local and neighbour readings.
  - Verify: Readings agree with a multimeter; missing values remain unavailable.
  - Progress 2026-10-26: Deferred at the user's request pending a multimeter. Current nodes use USB power banks; the user intends replacement shields for the final setup. The external-cell sensing path remains unverified. Continue independent logging preparation; do not substitute synthetic percentages for measured field battery data.

- [ ] **Complete receiver-side label reconciliation.**
  - Match transmissions with intended-receiver records.
  - Distinguish confirmed loss, delayed delivery, logger failure, and missing evidence.
  - Verify: ACK loss alone does not become a false packet-loss label.
  - Progress 2026-10-26: Software implemented and checked under CART Task 4. Receiver acceptance/rejection and sender completion events now support reconciliation; boot/log sequence, local attempt IDs and frame fingerprints preserve identity/continuity evidence. The new builder requires reviewed clock/coverage bounds, retains unknown/rejected/delayed cases in an audit file, and no longer uses missing ACKs as automatic loss labels. Twenty-five artificial logic checks and Baseline V1/V2 builds pass. Paired hardware validation, timing bounds and observation-window selection remain pending; task stays unchecked. No boards flashed. Procedure: `Code/Thesis/docs/RECEIVER_LABELS.md` relative to thesis root.

## Priority 5: Readiness Checks After Fixes

- [ ] Bench-check all six nodes: submissions, delivery, duplicate handling, priority order, buffering, recovery, and log completeness.
- [ ] Run outdoor pilot tests using the planned topology and traffic tiers.
- [ ] Confirm repeatable results and valid records before starting formal data collection.

**Current status:** Implementation is underway. Checked software subtasks and the verification log above show completed preparation. Parent tasks requiring hardware or manuscript insertion remain unchecked until those checks pass. No firmware was flashed during the 2026-10-27 software work.

## Additional Findings — Timing and Live Dashboard Reliability

- [ ] **Establish the actual one-hop delivery time.**
  - Investigate the reported delay using paired V2 sender and V1 receiver logs.
  - Distinguish submission time, queue waiting, radio transmission, ACK/retry time, and dashboard display delay.
  - Verify: A controlled test accounts for the observed delay using recorded events.

- [ ] **Clarify arrival time versus delivery latency.**
  - Do not present hub uptime or the gap between arrivals as delivery latency.
  - Use plain labels such as “Received,” “Delivery delay,” and “Time since previous arrival.”
  - Verify: Users can distinguish these values without understanding firmware timestamps.
  - [x] Software update: removed the measured-average-latency claim. Summary points to verified paired logs; per-record values and export columns are labelled unverified clock differences, and uptime/arrival gaps are explicitly distinguished from delivery delay. JavaScript checks passed.
  - [ ] Actual operator/browser understanding verified; technical columns remain for the later layout redesign.

- [ ] **Make latency measurements trustworthy.**
  - Establish a common time reference and document its uncertainty.
  - Explain unavailable or invalid timing rather than showing a misleading value.
  - Verify: A timestamped message has a defensible measured delay, or an explicit unavailable status.
  - Progress 2026-10-26: CART Task 5 solo preparation added USB CLOCK probes, saved request/reply measurements, an offline timing report and a LAN reference comparison tool. These expose timing intervals and clock-change indicators rather than declaring exact synchronization. Thirty-six combined software checks pass and Baseline V1/V2 builds pass. Actual clock bounds, drift, event-timing uncertainty and the multi-laptop pilot remain unverified; task stays unchecked. No clocks adjusted or boards flashed. See `CART TIMING VERIFICATION PLAN.md` in Documents.

- [ ] **Investigate intermittent dashboard API failures.**
  - [x] Concrete crash path identified and software fix prepared: matching ELF decoded the supplied close-distance panic to resident-page response construction/sending. Root/admin HTML now use AsyncProgmemResponse via an explicit static buffer and length, avoiding whole-page String responses. Host regression checks repeated byte-exact page reads and independent readers. This does not establish every API failure's cause.
  - [ ] Flash baseline-n1/baseline-n6 and verify repeated root/admin loads, no restart and three exact V6 references delivered at V1. Physical stability remains unverified.
  - Determine why `/api/live_incidents` sometimes fails while the page remains open.
  - Check connection changes, server responses, request duration, and node availability.
  - Verify: Repeated refreshes remain stable during representative traffic.

- [ ] **Clearly identify stale dashboard data.**
  - Show connection state, last successful update, and a visible stale-data warning.
  - Distinguish “No reports received” from “Unable to retrieve reports.”
  - Verify: Disconnecting the dashboard cannot leave old figures looking current.
  - [x] Software update: identifies last successful update, initial unavailable versus actual empty response, and saved/stale view after connection failure. Counts are not silently reset to a claimed zero. Controlled JavaScript failure/recovery checks passed.
  - [ ] Actual connection-loss and recovery behaviour verified on the deployed browser/node.

- [ ] **Handle stalled requests and reconnection.**
  - Define request timeouts and recovery behavior for both dashboard polling and message submission.
  - Verify: An interrupted connection does not leave the interface indefinitely waiting or sending.
  - [x] Dashboard polling and node-information requests now have eight-second abort timeouts and release their request guards for recovery. Controlled dashboard timeout/recovery checks passed.
  - [x] Resident message-submission timeout and uncertain-response/repeated-submission handling implemented and checked. Ten-second request timeout, concurrent-request guard, preserved input/reference, no automatic retry, explicit warning before retrying an uncertain request, and identical-confirmed-report guard in the current page. JavaScript checks cover timeout, rejection, malformed replies, connection loss and recovery. Refresh/new tabs do not share this guard; server-side idempotency is not implemented.
  - [ ] Actual radio/Wi-Fi interruption and recovery checked on devices.

## Additional Findings — Barangay Admin Usability

- [ ] **Redesign the received-message presentation.**
  - Prioritize urgency, location, message, complete reference, and receipt information.
  - Move radio path, packet type, and cryptographic details into secondary technical details.
  - Verify: An administrator can quickly identify what happened and where assistance is needed.
  - [x] Software 2026-10-27: reduced ten columns to category, location/report, full reference, hub receipt information and expandable technical details. Radio path, packet type, security and unverified clock differences are secondary. Clear category names match the resident form. Full report text is rendered literally without truncation. Sorting, filtering, reference/export scope and stale/error states pass controlled checks.
  - [ ] Confirm barangay administrators can interpret the reports on actual deployment devices.

- [ ] **Make the dashboard readable across screen sizes.**
  - Address small table text, crowded columns, and the isolated latency card.
  - Verify: Essential information remains readable on the actual laptop, tablet, or phone used in deployment.
  - [x] Software 2026-10-27: larger report text, wrapping five-column layout, labelled stacked cards below 760px, labelled 44px controls, and four aligned summary cards. Delivery-timing guidance is a note rather than an isolated fifth metric. Desktop and 390px iframe browser previews reviewed using explicitly fictional samples. Expandable details remain open across sorting/filtering and updated records; unchanged polls preserve the existing report DOM and focus.
  - [ ] Verify actual laptop, tablet and phone layouts, keyboard navigation and Wi-Fi interruptions on flashed nodes.

- [ ] **Distinguish recent-buffer counts from cumulative totals.**
  - Extend the existing history task to cover the metric cards and SOS summary.
  - Do not label the current 20-record window as the total received during a test.
  - Verify: More than 20 arrivals produce accurate, clearly labelled counts and complete experimental records.
  - [x] Software: recent cards/export scope is explicit; the history notice separately shows the recorded-since-restart counter from the authenticated hub API. It does not present this counter as a persistent all-time total or experimental PDR. Simulated 20-of-25 check passed.

- [ ] **Use complete message references consistently.**
  - Include the origin node with the Message ID, including in the SOS summary.
  - Verify: Messages with the same numeric ID from different origins remain distinguishable.
  - [x] Software: table, medical-report list and CSV use origin-qualified references such as V2#0006. JavaScript checks passed.

- [ ] **Clarify what the SOS summary represents.**
  - Identify whether it counts received reports, unread reports, or unresolved incidents.
  - Do not imply that every buffered SOS is a new or currently active emergency.
  - Verify: The summary wording matches the implemented behavior.
  - [x] Software: summary identifies medical reports in the recent view and explicitly avoids unread/unresolved-incident claims. It uses unavailable wording before a confirmed response and sorts recent references by arrival order. Browser/device review pending.

## Additional Findings — Resident Portal Usability

- [ ] **Simplify resident-facing language.**
  - Explain emergency categories in ordinary language.
  - Move queue weights, packet terminology, and encryption implementation details out of the main reporting flow.
  - Verify: A resident can submit a report without technical explanation.
  - [x] Software 2026-10-27: plain report-category names with examples; removed queue weights, access-token wording and LoRa terminology from the main reporting steps. Confirmation labels use the same category names. Existing radio state and node identity remain truthful. Local browser preview reviewed.
  - [ ] Confirm wording is understandable to representative residents on the actual phones.

- [ ] **Prevent accidental highest-priority submissions.**
  - Review the automatic Medical SOS selection and make category choice clear.
  - Verify: Medical, general, and routine submissions preserve the intended priority.
  - Note: The screenshot showing only SOS reports does not prove misclassification; this is a usability risk to check.
  - [x] Software 2026-10-27: no default category at load or after Clear form. Required native radio controls and a script guard require a choice. All three priority mappings and reset behaviour pass controlled JavaScript checks. Mouse and arrow-key selection checked in the local browser.
  - [ ] Confirm all three categories are accepted with the correct priority on flashed nodes.

- [ ] **Make submission status precise.**
  - Distinguish “Sending to nearby node,” “Accepted into queue,” and any verified delivery status.
  - Do not claim arrival at V1 without end-to-end evidence.
  - Verify: Every success message accurately describes what has been confirmed.

- [ ] **Prevent accidental repeated submissions.**
  - Review repeat clicks and retries after an uncertain response.
  - Preserve the reference number and explain when retrying may create another report.
  - Verify: Interrupted requests do not cause unexplained duplicate reports.
  - Note: Repeated “Help5” text with different IDs is not, by itself, evidence of LoRa retransmission duplicates.
  - [x] Software safeguards and controlled checks complete: repeat clicks blocked, uncertain retries require acknowledgement, confirmed identical reports redisplay their reference, and Wi-Fi instructions preserve it. Clear form is blocked while sending and otherwise warns before discarding submission history.
  - [ ] Verify interruption, retry and reference preservation on actual phones/nodes. Protection across refresh, tabs or devices is not claimed.

- [ ] **Align input limits and preserve entered text.**
  - Match the location-field limit and shared UTF-8 byte budget to backend validation.
  - Replace silent message truncation with clear feedback.
  - Verify: Accented text, Filipino text, and emoji cannot cause unexplained rejection or silent loss of message content.
  - [x] Software 2026-10-27: removed character-count location limit and silent message trimming. UTF-8 validation now matches the firmware's 83-byte location and 200-byte shared budget, preserves both fields and reports how many bytes must be removed. Submission is blocked while over limit. Firmware size-error text now explains the separate location limit as well as the combined limit. Null characters are blocked by the form to avoid C-string truncation.
  - [x] Controlled checks cover ASCII, Filipino text, accented and combining characters, emoji, exact boundaries, empty/whitespace input and recovery after editing. Host checks of the actual firmware submission function confirm 83/84-byte location and 200/201-byte total boundaries. Local browser preserved 50 emoji and showed 207/200 bytes with a seven-byte over-limit warning.
  - [ ] Verify text preservation and accepted content end to end on actual phones and flashed nodes.

- [ ] **Improve accessibility and small-screen interaction.**
  - Review text size, zoom restrictions, priority selection, and keyboard/touch behavior.
  - Verify: The form remains usable on the team's actual phones.
  - [x] Partial software preparation: enabled zoom, native labelled category radios in a fieldset, visible category focus outline, passcode label association, and announced submission status. Local browser mouse/keyboard checks passed; broader phone/layout review remains pending.

## Readiness Gate Before Formal Data Collection

- [ ] Resolve message-handling defects and preserve complete source/receiver logs.
- [ ] Verify battery sensing and receiver-side training labels.
- [ ] Establish timing accuracy and explain observed one-hop delays.
- [ ] Complete mixed-priority and controlled-failure pilot runs.
- [ ] Confirm the dashboard clearly distinguishes live, stale, empty, and unavailable data.
- [ ] Freeze the firmware, radio settings, model, and test procedure before formal comparison runs.

## Additional Research-Readiness Requirements

- [ ] **Validate PQA queue-entry records.**
  - [x] Software: successful FIFO/min-heap admission emits ENQUEUE before releasing the queue mutex. Rejected admissions, overheard frames, duplicates and locally delivered V1 reports do not create queue-entry evidence. Entry/TX event timestamps are captured before serial logging delay.
  - [x] Analysis: uses ENQUEUE to first data TX, never inferred RX/NEW entries. Duplicate reception cannot reset the start. Retries do not create extra samples. Session/node/boot/origin/ID and continuous log sequences protect matching; drops, missing evidence and conflicting logs are excluded/audited. Old captures without ENQUEUE leave PQA unavailable. Per-run summaries include the eligible sample count.
  - [x] Eleven software checks passed, including real FIFO/min-heap queue-wrapper admission and rejection, eviction, FIFO inversions, correct ordering, duplicates/retries, log gaps, reboot/session separation, timestamp wrap and already-started transmissions.
  - [ ] Physical mixed-priority FIFO/min-heap verification remains pending. No boards flashed for this update. See `Code/Thesis/docs/PQA_LOGGING.md`.
  - Verify: Known message sequences produce the expected PQA for both FIFO and Min-Heap.

- [x] **Correct the CART threshold tie-break.**
  - When candidate thresholds have equal failure-class F1, select the one with higher failure-class Recall, as specified in the paper.
  - Verify before final model training.
  - Verified 2026-10-27: `train_cart.py:select_threshold()` selects maximum validation Danger F1, then higher Danger Recall. Only exact ties in both scores use nearest 0.5 and then lower threshold. Five direct tests of the actual selector pass; all 49 combined software checks pass. This completes the threshold-selection fix, not full model training or hardware validation.

- [ ] **Complete avoided-link ground truth.**
  - [x] Common analysis safeguard: classifier comparison now uses reviewed sender/intended-receiver outcomes, not ACK/NOACK labels. Unknown/rejected/delayed outcomes are excluded and preserved in a companion audit CSV. Eight tests pass; confusion metrics use Danger as positive and paired cases are identical for both classifiers. No boards flashed.
  - [x] Method selected by the user: new independent Baseline shadow-mode sessions after model freeze; no dual-transmission probes. Baseline chooses routes while both classifiers predict the same chosen hop. Five-configuration network evaluation stays separate.
  - [x] Software: classifier plan checks frozen report/header identity and excludes development sessions, unplanned sessions, non-Baseline configurations, wrong/missing model IDs and later retries. Firmware captures both verdicts before TX and records the generated model identity in CONFIG. Training reports list all development sessions and frozen-header provenance.
  - [x] Final regression: 84 Python/host checks passed, including real comparison CLI, frozen-artifact validation and earlier queue/logging tests. Final baseline-n1 and node6 builds passed. No boards flashed and no trained field model generated.
  - [x] Exact Chapter 4 replacement text prepared: `Documents/CHAPTER 4 - SHADOW EVALUATION UPDATES.md`. Covers the probe paragraph, confusion matrix, definitions, processing, shadow-logging sentence and McNemar item. Chapter 5 unchanged.
  - [x] User confirmed the Chapter 4 replacements were pasted on 2026-10-27. This records user confirmation; the revised manuscript file has not been independently reread.
  - [ ] Freeze a real trained model; verify paired hardware coverage and conduct independent shadow sessions. Parent remains unchecked. Procedure: `Code/Thesis/docs/AVOIDED_LINK_EVALUATION.md`.
  - Follow the approved replacement method consistently; do not assign outcomes to untried links.
  - Do not assign outcomes to avoided links without observations.
  - Verify before independent classifier evaluation.

- [ ] **Complete the planned statistical analysis.**
  - [x] Software 2026-10-28: after a significant eligible Kruskal-Wallis result, run tie-corrected two-sided Dunn tests with Bonferroni correction across all ten configuration pairs, separately for each metric/tier. Save omnibus/status and pairwise CSVs, raw/adjusted p-values, usable sample sizes and exclusions.
  - [x] Safeguards: all five formal configurations required; at least five finite run-level values each for the asymptotic calculation (planned ten trials unchanged). Missing/duplicate run identities, unknown tiers, missing configurations, small groups and identical pooled values do not generate misleading p-values. Survey/unknown configurations are excluded. Dependencies are recorded in tools/requirements-analysis.txt.
  - [x] McNemar comparison uses the approved independent Baseline shadow plan and verified receiver-side outcomes, not ACK-based failure labels.
  - [x] Verification: 98 Python/host regression tests pass, including 14 statistical tests with independently derived tied/untied probabilities and the actual comparison-command output files. No firmware changed/flashed or empirical thesis data generated by these tests.
  - [ ] Before final reporting, complete the planned evaluation trials, verify one complete independent run per comparison input, review paired/repeated-measure dependence and metric validity, then inspect actual results/exclusions. Parent stays unchecked until final analysis is performed. See Code/Thesis/docs/STATISTICAL_ANALYSIS.md.
  - Complete before final analysis; this alone does not prevent collecting otherwise valid raw data.
