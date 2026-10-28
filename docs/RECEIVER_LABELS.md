# Receiver reconciled CART labels

Implemented software preparation for training Task 4. Hardware verification and clock/observation-window measurements are still required. No fixed timing values in this document are validated field settings.

## Recording requirements

Flash the updated firmware to every participating endpoint before the paired pilot. The packet format and the CSV column names are unchanged. Capture both ends of each eligible directed link, including boot CONFIG records, using the same physical-session name across laptops. Keep original CSV and raw logs.

New information in CSV `detail`:

- Every event: `boot` identifies the node boot and `seq` numbers attempted log events. A mutex timeout or a missing serial row leaves a detectable sequence gap. Reordered rows, duplicate captures, missing metadata and gaps are treated conservatively.
- Data TX: `attempt` is local to the transmitting node and boot; `frame` is the full authentication tag of the transmitted bytes. It is a fingerprint, not a globally unique retry identifier.
- TX_DONE / TX_ERROR: machine-readable completion result, with the local attempt number.
- RX_ACCEPT: the intended receiver delivered the valid message, queued it for forwarding, or recognised and re-acknowledged a previously accepted duplicate. It does not imply an additional hub delivery.
- RX_REJECT: decrypt failure, invalid body, TTL expiry or forwarding-queue rejection, where the current receiver path has enough valid structure to emit the outcome. Other invalid frames may have only raw RX evidence and remain unknown.

Duplicate messages with identical bytes can share a fingerprint. Overlapping or otherwise ambiguous retry matches remain unknown. No wire-level attempt identifier has been added.

The capture tool now flushes each saved line and reports malformed CSV rows rather than silently discarding them. Raw lines remain available. Its diagnostic outcome counter is not a count of eligible training observations.

## Coverage review

The builder does not infer receiver loss from a missing ACK. It requires a reviewed JSON coverage file before producing verified data labels. Missing coverage leaves candidates in the audit file without binary labels.

Coverage specifies a common time mapping:

`reference_epoch_ms = node_local_ms + epoch_offset_ms`

Measure and document the mapping error and drift for each covered interval under Task 5. `uncertainty_ms` must cover clock mapping, timestamp placement and applicable logging/handling delay. Copying PC timestamps or merely executing the time command does not establish its value.

Task 5 software preparation now provides optional capture `--clock-probe-every`, `tools/timing_report.py`, and `tools/clock_reference.py`. The full group procedure is in `Documents/CART TIMING VERIFICATION PLAN.md` relative to the thesis root. These tools save measurements for review; none automatically marks coverage verified. Actual timing precision is still unmeasured.

Before asserting `verified: true`, inspect capture interruptions, node resets, CSV errors, logger continuity and endpoint identity. The code also requires bracketing log events and consecutive sequence numbers. Those automated checks supplement the documented review; they do not independently prove a perfect recording system.

The following is a template only. Its null values and false verification flag deliberately make it invalid until reviewed measurements replace them:

```json
{
  "target": "next_hop_acceptance",
  "acceptance_grace_ms": null,
  "observation_tail_ms": null,
  "coverage": [
    {
      "session": "baseline-pilot-01",
      "node": 2,
      "boot": "COPY_FROM_ACTUAL_LOG",
      "start_ms": null,
      "end_ms": null,
      "epoch_offset_ms": null,
      "uncertainty_ms": null,
      "verified": false,
      "evidence": "Describe the measured timing and recording continuity checks"
    }
  ]
}
```

Add a reviewed interval for each participating sender and receiver. Ambiguous overlapping intervals are not accepted. Local uptime rollover or boot changes require separate evidence intervals. CSV files with duplicate captures of the same endpoint/boot are rejected for continuity rather than silently counted twice.

`acceptance_grace_ms` extends the sender's recorded successful transmission-completion time to the receiver acceptance deadline. `observation_tail_ms` keeps an additional interval for separately classifying delayed events. Select these using the pilot and document them in the methodology. The code expands observation bounds by the sum of sender and receiver uncertainties and excludes acceptance events that straddle timing boundaries. It does not reuse the old 60-second ACK lookup as a receiver-loss deadline.

## Building and reviewing

From the project root, once coverage is verified:

```powershell
python tools/build_cart_dataset.py "captures/baseline-pilot-01-*.csv" --coverage coverage.json --out cart_dataset.csv
```

- `cart_dataset_audit.csv` retains all data TX candidates, features, identifiers and exclusion reasons.
- `cart_dataset.csv` contains verified binary data labels plus separately identified heartbeat diagnostic rows. The default training source selects Baseline data only.
- Safe 0: a uniquely matched, timely RX_ACCEPT event at the intended receiver.
- Danger 1: successful sender completion and reviewed complete observation, with no matching reception evidence. A conflicting ACK keeps this unknown.
- Rejected, delayed, ambiguous and incomplete observations have no binary label. Never silently relabel them to obtain enough Danger examples. Report exclusions and resulting condition/link coverage.

The trainer rejects data rows without the new reconciliation provenance. Rebuild legacy ACK-labelled datasets rather than editing their provenance field. This provenance is an audit contract, not protection against deliberately altered files.

Keep missing traffic unknown instead of replacing it with zero. Battery values remain unverified until the separate battery task is complete. A reconciled outcome does not validate its input measurements.

## Verification so far

Software cases in `tools/tests/test_receiver_labels.py` use explicitly artificial examples; none are field training data. The tests cover accepted frames, lost ACKs, non-reception, incomplete/missing coverage, conflicting evidence, retries and overlap, duplicates, rejection, delayed and uncertain timing, reset boundaries, legacy-label rejection, and the CSV-to-dataset command.

Baseline V1 and V2 firmware builds pass. The old V1-only indoor log produces no verified data training rows. Live paired logs, clock bounds, the observation-window choice, deployed logger coverage and agreement with the final manuscript target remain pending. Task 4 is not yet complete.
