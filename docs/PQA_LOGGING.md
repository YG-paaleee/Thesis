# Accepted queue entries and Priority Queuing Accuracy

Software preparation: 27 October 2026. Physical mixed-priority validation is pending.

## Problem and change

An RX event means an authenticated frame was heard. It can be overheard,
duplicated, rejected or delivered at the destination without entering a queue.
NEW also includes reports delivered locally at V1. Neither establishes queue
admission. Using the latest duplicate RX as the start can conceal a less urgent
transmission that occurred while a medical report waited.

The common queuePush wrapper now emits ENQUEUE only after successful admission
to the real FIFO or min-heap. It emits the event before releasing the queue mutex,
so a sender cannot select the newly inserted message before its entry is logged.
Rejected admissions emit no ENQUEUE. An admission that evicts another report emits
ENQUEUE for the new report and EVICT for the removed report. Duplicate reception
and destination-local delivery do not call this queue admission path.

## Analysis rules

For each session, node, boot, origin and message ID, measure from the first
accepted ENQUEUE to the first data TX. A k=1 sample is correct when no k=2 or k=3
data TX occurs during that interval. Log sequence resolves events in the same
millisecond. Admission and TX rows capture their event time before serial logging
delay; a lower-priority TX timestamped before admission is not an inversion even
if its log row appears later. This is millisecond-resolution ordering, not a
claim of microsecond precision. Subsequent TX retries are not additional k=1 samples. Heartbeats
and ACKs do not count as lower-priority data traffic. A repeated RX or entry event
cannot shorten an existing interval.

STORE preserves custody at the node, so the original interval continues through
DTN waiting until the first data transmission. DROP/EVICT ends an unsent interval
and excludes it from transmitted-message PQA; report these separately from PQA.
PQA does not by itself measure delivery, channel access delay or loss.

The interval requires boot and log-sequence metadata with no missing events.
A gap invalidates active intervals, reboot/session boundaries cannot be crossed,
and conflicting copies of a sequence invalidate that node/boot segment. Exact
duplicate input rows are deduplicated. Pending samples without a first TX and
TXs without verified admission are excluded. Audit reasons are attached to the
returned table and printed in detailed analysis; the per-run table includes
pqa_samples and pqa_audit_events. An audit event count is not a lost-packet count.

Older logs without ENQUEUE cannot provide this corrected PQA. They remain useful
for the other purposes supported by their evidence. No historical PQA is fabricated.

## Remaining physical check

1. After the distance survey, deliberately upload the updated firmware to the
   test boards. The survey firmware currently on V1/V6 was not changed by this work.
2. Record the sender and receiver, with the correct identities and configuration.
   Use controlled test reports and preserve the full raw and CSV logs.
3. In a Baseline FIFO test, hold transmission while admitting k=3, k=2, then k=1.
   Confirm actual ENQUEUE events. Release transmission with a usable route.
   If both less urgent packets transmit before k=1, its overtaken_by is 2 and
   this sample is incorrect. Do not infer the order from dashboard arrivals.
4. Repeat with a min-heap build. When all three are queued before selection and
   the route is usable, k=1 should transmit first and overtaken_by should be 0.
5. Confirm retries do not create extra samples and missing serial evidence is
   excluded. A live test must establish actual event order; the software tests
   are not a claim of physical queue/radio performance.
