# UI accuracy and recent report scope

Updated 2026-10-27 for Firmware Task List Priority 3. Software changes are implemented; actual-board browser checks remain pending.

## Resident node information

The resident page requests `/api/node_info` at load and every 15 seconds, with an eight-second request timeout. It displays the actual node ID and role, radio state and the firmware's configured Wi-Fi client capacity/current connected count. No passcodes or incident contents are returned by this public operating-information endpoint.

Radio ready means the radio was initialised and is not currently paused. It does not establish that a route exists or that delivery will succeed. The page says this explicitly. A paused or unavailable radio is identified separately. Failed or invalid operating-information requests show unavailable status and do not retain a claim that the mesh is active.

The standalone local preview intentionally has no live node-information API and shows unavailable information. It must not impersonate an actual node merely to make a preview look connected.

## Submission confirmation

Residents explicitly choose Medical SOS (priority 1), General emergency (priority 2), or Routine update (priority 3). The page starts with no category selected, and Clear form restores this state. Required native radio inputs and a script guard prevent submission without a choice. Category descriptions give ordinary examples rather than queue weights. Radio controls support native keyboard operation with visible focus; zoom is enabled and submission status uses a polite live region. Local browser selection checks and controlled tests of all three payload mappings passed. Representative-resident and physical-phone validation remain pending.

The accepted priority comes from the server response, not the current selection after a request has started. Local V1 intake is shown as recorded at this hub; another node's outgoing queue acceptance does not claim arrival at V1.

Submission requests have a ten-second timeout covering the response body. The button and a script guard prevent concurrent requests, and clearing the form is blocked during a request. Timeout, connection loss and invalid replies mean acceptance is unknown: aborting a browser request does not cancel work already performed by the node. No automatic retry is made. An explicit firmware error response is shown as rejection, with entered text preserved.

After an uncertain response, another submission requires acknowledgement that another report may be created. After confirmed acceptance, an identical priority/location/message is blocked in this page session and its reference is redisplayed. Wi-Fi instructions retain that reference. Clearing asks the resident to save it and explains that clearing does not cancel an accepted report. These are browser-session safeguards, not server-side idempotency: refresh, another tab or another phone can submit another report. Device interruption checks remain pending.

## Resident input limits

The firmware stores at most 83 UTF-8 location bytes plus a terminator and at most 200 bytes for location and message together. The form counts the trimmed strings actually submitted using UTF-8, rather than a character limit. It never automatically truncates either field. Both counters and a live warning explain excess length; submission is blocked until the user edits the report to fit. Empty/whitespace-only fields and embedded null characters are rejected by the form. Ordinary leading/trailing whitespace is still trimmed on submission, as before. The firmware's size-error response also explains its separate location limit instead of incorrectly describing every rejection as a combined-budget failure.

Controlled resident-script checks cover exact and excessive limits, Filipino text, accents, combining characters, emoji and successful correction. Host tests exercise the actual submission function at the location and shared-budget boundaries. A local browser check retained 50 emoji and showed the expected excess without cutting text. Real phone/node acceptance and end-to-end content checks remain pending.

## Dashboard history and export

V1 retains its latest 200 report records in RAM, replacing the oldest when full. The API returns at most 20 per page. Page 1 contains the newest group; Older/Newer buttons browse earlier groups. Cards, SOS summary, sorting and category filtering describe the selected page, not the entire history. The notice separately reports page size, retained snapshot size and successful hub recordings since restart. More than 200 recordings produce an explicit overwritten-record count. Reboot or loss of power clears RAM history; it is not permanent storage or a complete experimental record.

The recorded-since-restart counter is not automatically the experiment's PDR numerator, a persistent all-time total, a count of people needing help, or a count of unresolved incidents. It resets with the node and includes locally recorded V1 reports. USB logs and source evidence remain necessary for experiments.

Export this page saves its records independently of the display filter. Export retained history fetches every page of one snapshot, verifies count and unique arrival numbers, then downloads a single CSV. Failed/expired requests produce no partial download. Export scope, hub session token and snapshot counter are included in CSV, with distinct page/history filenames. Full origin-qualified references remain visible and spreadsheet formula-looking text is escaped.

Older-page navigation freezes a snapshot of arrival numbers and pauses live polling. Return to latest resumes polling. Requests use a random boot-session token to detect hub restarts; the firmware rejects expired snapshots when their oldest record has been replaced. Failed navigation preserves the prior page. Pages are not silently mixed across reboot or buffer wrap. A page snapshot copies text into the JSON document while holding the incident mutex, then releases the lock before serialization; allocation failure returns an error rather than a partial page. Node-specific static storage grows only on V1; relays retain their previous allocation.

USB sender/receiver captures remain required for research, including transmissions that never reached V1. This bounded dashboard history does not prove PDR or remove the need to verify runtime heap headroom under actual Wi-Fi/radio traffic. Before collection, verify 120 arrivals, all six pages, a full export, oldest-record replacement after 200, snapshot expiry and hub restart behaviour on hardware.

Final V1 FIFO and development heap/DTN builds passed with 150,220 bytes static RAM (45.8% of 327,680 bytes); V2 remains at 83,244 bytes. These are build-time figures, not measured runtime free heap under Wi-Fi/radio load. Host tests combine the actual ring insertion function with the actual page planner; controlled JavaScript tests cover six-page/120-report export, expired snapshots and rejecting partial downloads.

## Connection and timing accuracy

Before the first successful hub response, figures are unavailable rather than asserted zero. An actual empty response is distinct from an unavailable connection or a filter with no matches. A later failed request retains the last view and identifies its last successful update; it does not claim those counts are current. Dashboard requests time out after eight seconds and release their polling guard for recovery.

The page no longer averages unverified phone/hub clock differences under a measured-latency title. The summary directs operators to verified paired logs. Existing per-record values and exports are explicitly labelled unverified clock differences. Hub uptime and gaps between arrivals are not end-to-end delivery delay. The SOS summary explicitly counts recent received records, not unread or unresolved emergencies.

This work improves UI accuracy and connection-failure handling; it does not identify the original hardware/API failure's cause or establish actual clock accuracy. Physical-device usability review remains pending.

## Report presentation

The admin report view uses five columns: category, location/report, complete reference, receipt information and technical details. Location and message are prominent and wrap without truncation. Category names match the resident portal. The receipt column explicitly states seconds after hub restart plus arrival number, rather than implying wall-clock time or delivery latency. Radio path, origin, packet type, security, unverified clock difference and arrival gap are inside native expandable details. Missing security metadata is not labelled authenticated by default.

Below 760px, rows become stacked cards with visible field labels. Sort/filter controls have associated labels, visible keyboard focus and at least 44px height. The four page-count metrics remain together; verified-timing guidance is a note outside that grid. Page and retained-history CSV exports are explicitly separate and independent of the display filter.

Expanded detail state is retained across sorting/filtering and changes to the records. Unchanged polling responses do not rebuild the report DOM, preserving focus and selection. Controlled script checks cover these behaviours, full literal text, sort/filter results and the existing connection/error/export safeguards. Desktop and a 390px iframe viewport were visually reviewed. `tools/preview_admin_layout.py` provides a separate localhost-only preview on port 8766 with prominently labelled fictional examples; `/phone` provides the narrow iframe. These samples never enter firmware or research logs. The ordinary port-8765 preview continues to report its API as unavailable.

## Verification

Node-based JavaScript checks execute the actual inline scripts with controlled DOM/API responses. Resident checks cover node roles, radio states, actual capacity, invalid metadata, local/queued response wording, accepted-priority changes and credential omission. Dashboard checks cover 20 recent records versus a 25-record counter, complete references, export scope, timing labels, initial error versus empty, stale views, timeout and recovery. These fixtures are not field data or a substitute for an actual browser/device test.

Before checking the parent Priority 3 items complete, flash the updated firmware and verify V1/V2/V6 identities, paused/unavailable radio states, configured Wi-Fi capacity, submission-priority behaviour and more-than-20 incident scope on the actual boards. Keep complete USB captures as the separate experimental evidence.
