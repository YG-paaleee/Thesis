# Estimated Receipt Clock

The admin table shows estimated receipt clock time in Asia/Manila (PHT).
View details includes the date, seconds, time source and network uncertainty.
This is not delivery latency or a validated research timing measurement.

## Firmware

- Records receipt uptime using 64-bit `esp_timer_get_time() / 1000` instead of wrapping 32-bit `millis()`.
- Keeps `rxTime` in milliseconds, preserving the existing JSON field name.
- Returns `X-Hub-Uptime-Ms` alongside the existing `X-Hub-Session` on authenticated history responses.
- Adds public `uptimeMs` and `bootId` fields to `/api/node_info` without changing access controls.

## Dashboard

Samples the device clock before and after the history request. The midpoint is
matched to the uptime header from that same response and boot session:

`estimated receipt epoch = midpoint device epoch - (sample uptime - receipt uptime)`

The approximation depends on the device clock being correct. Network uncertainty
is bounded by half the request round-trip interval only; this does not include
device-clock error, oscillator drift or timestamp acquisition delay. Samples
over two seconds or with an in-flight clock jump are rejected. Clock anchors are
kept stable within a boot session and replaced on reboot, missing timing headers,
or when a newer receipt requires a newer anchor. Uptime-only fallback remains
available for older firmware. Nothing is persisted across page reloads.

No node clock is changed. No RTC, internet, LoRa synchronization packet or extra
radio traffic is introduced. Different viewers can obtain different estimates.
CSV exports retain raw uptime and existing unverified clock-difference fields;
the display estimate is not substituted into research measurements.

Delivery duration stays unavailable until synchronized send/receive timing is
independently supported. Queuing, message routing and custody handling are unchanged.

## Preview and checks

`python -B tools/preview_admin_layout.py` serves fictional records on port 8766
with a simulated uptime header. The yellow sample banner remains visible.

`node tools/tests/test_admin_dashboard.mjs` tests clock estimates and the existing
dashboard behavior. Regenerate embedded pages with `python tools/sync_web_assets.py`.
Build `node1` before flashing. Host tests/builds do not establish board verification.

## Verification on October 28, 2026

- Dashboard/history/clock JavaScript tests passed, including reboot and missing-header invalidation.
- Message handling, report pagination (including 64-bit receipt uptime), and survey-routing host tests passed.
- `node1` ESP32-S3 firmware build succeeded with PlatformIO; no upload was performed.
- Browser preview confirmed a PHT receipt estimate and a full date/time under View details.
- The original `Documents/THESIS/Thesis-main` checkout is unchanged. Work is isolated
  on `codex/admin-receipt-time` in `Downloads/Thesis-admin-receipt-time`.
- Physical clock mapping, board reboot behavior and device-clock accuracy still
  require hardware verification. No delivery-duration implementation is claimed.
