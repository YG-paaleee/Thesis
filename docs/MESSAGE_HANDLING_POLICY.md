# Message handling policy

Updated 2026-10-27 for Firmware Task List Priority 1. Software checks are separate from the required on-board pilot.

## Reports submitted directly at V1

V1 is already the destination. After validating the submission and constructing its encrypted body, the firmware stores one local incident, emits NEW followed by DELIVER, and returns `delivered_local` with the origin-qualified reference and accepted priority. It does not enqueue a radio transmission. If incident storage is busy, the API returns an error rather than claiming delivery.

This local operation can work even when the LoRa radio is unavailable. It is not evidence of LoRa delivery or radio latency. The display path is V1 rather than V1 to V1. The resident response distinguishes local recording from a remote node accepting a report into its outgoing queue.

The serial traffic generator continues to reject V1 as an injection origin. Formal radio experiments use the planned non-hub origins and must not mix local hub submissions into radio-delivery measurements.

## Configurations without DTN

Baseline, Partial and Heuristic have no store-and-forward custody:

- If no usable route is available, discard the queued message immediately and record DROP with `no_route`. A route lookup that fails before transmission is not a failed over-air training attempt.
- After an unacknowledged transmission or a transmission-completion failure, re-evaluate the route. If no usable route remains, apply the immediate no-route drop.
- If a usable route remains, count the failed hop on that local queued message. Retry after a short delay while the count is below three; drop with `retries_exhausted` on the third counted failure. Additional CAD/channel-busy deferrals are not themselves completed data transmissions and do not consume that failed-hop budget.
- RETRY records expose the failure count and limit. Counts are stored with all queue entries, not an eight-slot table that can randomly replace another message's counter. Updating a count does not reset arrival order or priority.
- A message already removed or evicted while its transmission was in flight is not reintroduced by this counter update.

An ACK is a hop-control outcome, not independent proof of receiver-side training truth. Receiver reconciliation remains necessary. No-ACK logs now describe the applicable DTN/no-DTN action instead of saying a no-DTN message is being held in DTN.

## Configurations with DTN

Ablation, Full and the development DTN builds retain the existing store-and-forward policy: queue messages may move into bounded DTN custody, route absence triggers polling, and failed acknowledged delivery with a route triggers a short retry. Buffer capacity, eviction and expiry still apply. This is not a promise that every message will eventually arrive.

## Manuscript alignment to apply

Use the following wording in the configuration description and any description of no-DTN link-failure handling. Review the manuscript source before insertion; this document does not edit the PDF:

> Configurations without DTN discard a message when no usable route is available. If a transmission fails to obtain an acknowledgement and a usable route remains, the node applies a bounded retry policy, discarding the message after three failed hop attempts. Channel-access deferrals are recorded separately. DTN-enabled configurations instead retain eligible messages for store-and-forward, subject to buffer capacity, eviction, and expiry.

If describing V1 intake, state that reports submitted directly at V1 are recorded locally and are not LoRa transmissions. Keep this distinct from the radio evaluation's origin selection.

## Remaining device verification

- Submit one report on V1: confirm the reference, NEW/DELIVER events and exactly one incident entry, with no data TX for that report.
- Test V1 intake while its radio is unavailable and verify that a busy incident buffer is not reported as success.
- Submit on V2: confirm queued response, subsequent actual radio delivery and the accepted priority in the UI.
- Exercise no-route, lost ACK with an available route, repeated failed attempts, queue eviction, and DTN recovery scenarios. Match logs to the specified outcomes.
- Insert and review the manuscript wording above. Keep Priority 1 unchecked until its required device checks and paper alignment are complete.
