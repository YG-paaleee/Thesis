# CART Timing Verification Plan

Task 5 status: software and procedure preparation in progress. Hardware clock measurements and deployed verification are pending. This document does not certify timing accuracy.

## What we are checking

Each node starts its own uptime counter when it boots. Two nodes displaying the same uptime have not necessarily recorded the same real moment. We must map the relevant node timestamps to one shared reference and record how uncertain that mapping is.

There are two separate checks:

1. Node to laptop: a USB request and matching CLOCK response bound the relation between node uptime and the connected laptop's clock.
2. Laptop to common reference: comparisons on one local network establish clock-offset measurements between the four laptops and one reference service.

The tools do not silently adjust laptop clocks, manufacture synchronization, or mark coverage verified. Measurements at isolated times do not prove an error bound between them; drift, logging delay, resets and interruptions still require review.

## Solo preparation available now

- Firmware `clock <token>` command: reports a numbered local-uptime event through USB. It does not change the heartbeat interval, transmit a radio packet, or set the node clock.
- Capture `--clock-probe-every`: sends periodic USB timing requests and saves matched measurements in a separate `_clock.jsonl` file alongside the CSV and raw log.
- `tools/timing_report.py`: reports node/laptop offset intervals, response time, unanswered probes, clock-change indicators and separate boot identities. It never automatically approves training coverage.
- `tools/clock_reference.py`: a local-network reference service and client comparison tool. No reference service is started automatically.
- Software tests use artificial examples and mocked devices/network responses. They are not real clock measurements or training data.

## Group procedure later

### 1 Prepare the laptops and boards

Use the laptop setup procedure under Task 3 to install Python, pyserial and the updated tools on all four laptops. Flash the updated logging/timing firmware to participating boards. Keep the group indoors for the first check. Close other programs using the same serial ports.

Record each laptop name, assigned node, serial port and power source. One laptop may capture several nearby USB nodes; record that separately from the intended field power arrangement.

### 2 Establish one reference

Connect the four laptops to the same trusted local network. Internet is not required by the reference tool. Select Laptop 1 as the reference; keep it powered, awake and running the reference process until all final comparisons finish.

On Laptop 1, run in a separate terminal:

```powershell
python tools/clock_reference.py serve
```

Record the printed reference ID and Laptop 1's local IPv4 address. Do not restart the service during the same comparison series. The reference uses a monotonic clock anchored when the service starts, so its reference time is not certified UTC.

On every laptop, including Laptop 1, run a comparison before collection. Substitute the actual reference address and a unique laptop filename:

```powershell
python tools/clock_reference.py check REFERENCE_IP --out laptop2_before.json
```

Do not type `REFERENCE_IP` literally. Laptop 1 can use `127.0.0.1` for its own comparison. If no valid replies are saved, resolve connectivity before relying on shared timing. Different printed reference IDs cannot be treated as one continuously running reference without additional alignment evidence.

### 3 Start recording with USB timing probes

Use the actual node port, one shared physical-session name and a unique node filename. Example placeholders:

```powershell
python tools/capture_telemetry.py COM4 --no-time-sync --clock-probe-every 30 --session baseline-timing-pilot-01 --out baseline-timing-pilot-01-V1.csv
```

The 30-second USB probe interval is a pilot setting, not a verified precision claim. It is independent of the existing 30-second LoRa heartbeat. The probe works even with `--no-time-sync`; it measures a timing relation rather than setting the node's wall clock. The dashboard may still report unavailable latency.

Start capture before resetting the board so CONFIG is retained. Initial probes may be lost during the reset; check later replies rather than hiding the missing samples. Record at least two answered probes from the same boot before the analysed traffic. Continue periodic probing during the pilot and record further answered probes after the final data events. Keep the laptop awake.

Do not send manual serial commands from another monitor while capture owns the port.

### 4 Check with a small paired-message pilot

Send a small numbered batch from a recorded source to a recorded intended receiver. Retain source NEW, TX and TX_DONE, receiver RX_ACCEPT/RX_REJECT, and hub DELIVER where applicable. Check that event ordering is physically plausible after clock mapping.

A nearby test does not require or imply zero delay: airtime, queue waiting and channel access still take time. Evaluate the logging/probe overhead under representative traffic as well as at idle.

For application delivery delay, a possible definition is source NEW to matched hub DELIVER on the shared reference. Confirm this boundary with the manuscript before formal evaluation. It excludes any earlier phone entry or browser-to-node delay. Do not subtract unrelated uptime counters, arrival gaps, PC receipt times from different unaligned laptops, or unchecked phone timestamps.

### 5 Save final evidence

After the final traffic, keep recording for the agreed observation tail and obtain further timing replies. Stop capture with Ctrl+C and preserve the CSV, `_raw.log`, and `_clock.jsonl` files.

While the same reference service is still running, repeat the laptop comparison and use a new output filename:

```powershell
python tools/clock_reference.py check REFERENCE_IP --out laptop2_after.json
```

Then generate a USB measurement report for each recording:

```powershell
python tools/timing_report.py baseline-timing-pilot-01-V1_clock.jsonl --out baseline-timing-pilot-01-V1_timing_report.json
```

Stop the reference service only after every laptop's final comparison is complete. Return the files for review; do not mark coverage verified just because a command finished successfully.

## How the measurements will be reviewed

- For each USB probe, the node CLOCK event occurs between laptop request and response. The report returns an offset interval, not an exact offset. Long USB or processing delays widen this interval.
- For each network reference exchange, the client records request/reply times and the reference records receive/send times. Causal bounds give an interval for reference time minus laptop time without assuming equal delay in both directions.
- Add the two offset intervals to relate node uptime to the common reference. Include measurement resolution, timestamp-placement effects, inter-sample drift and any known logging delay in the final uncertainty budget.
- Compare before/after laptop offsets, repeated node probe samples, and epoch-versus-monotonic changes. Clock steps, sleep, reset, uptime wrap, unanswered probes or excessive drift may require splitting or excluding a recording interval. Before/after agreement alone does not rule out an intervening step.
- Verify continuity and coverage of both endpoints as required by `Code/Thesis/docs/RECEIVER_LABELS.md`. Timing evidence does not substitute for reception evidence.
- Select acceptance grace and observation-tail values using the pilot and document them. Do not guess them from the old 60-second ACK lookup or the dashboard arrival gaps.
- If uncertainty spans a label boundary, retain the outcome as ambiguous. If a latency interval is too broad for the claimed conclusion, report it as uncertain or unavailable.

## Task 5 completion condition

Complete only after actual node/laptop and cross-laptop evidence supports the selected analysed intervals, the uncertainty and drift assumptions are documented, the paired pilot supports valid ordering/matching, and the observation rules are agreed. No measured precision value is available yet.
