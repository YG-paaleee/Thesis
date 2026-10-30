# Combined Citizen and Admin UI: Hardware Test

This checkout is based on samir commit eb2d585. It combines the approved citizen
interface with the simplified admin page and estimated receipt clock support.
It is not a demo transport. At the user's request, the passcode SANMIGUEL2026 is
prefilled for supervised group testing. This exposes it in the page source;
remove the prefill before public use.
Authentication and message acceptance still come from the firmware API.

## Included

- No input placeholders or report-category descriptions.
- Eye button to show/hide the passcode; Clear form hides it and restores the test prefill.
- Centered incorrect-passcode notification for three seconds, only after an
  explicit incorrect-passcode rejection from the hub.
- Compact reference popup after a valid queued or locally recorded response.
  It stays locked for ten seconds, then remains until dismissed.
- Copy-reference fallback for captive browsers without clipboard access.
- Exact UTF-8 counters: 83 bytes for location; 200 shared by location and message.
- Actual node identity, radio status and Wi-Fi count from the hub API.
- Admin estimated receipt time in PHT, with date and seconds in View details.
- Delivery duration remains unavailable; UI clock estimates are not research latency.

The demo in Downloads/San-Miguel-Firmware-UI-Updated.html remains separate.
Do not copy its simulated transport into this checkout.

## Safe rollout

Use this project folder, not the older Thesis-main checkout. Flash Node 1 and
one mini hub first, using each board's matching nodeN target. Do not erase flash
or reset stored admin credentials. The previous firmware can be rebuilt from
the unchanged Thesis-main checkout if rollback is needed.

Only the build targets explicitly verified in the current session should be
described as compiled. Physical behavior must still be checked on the boards.

## Board checklist

- Connect to each board's Wi-Fi; reload the page after the firmware update.
- Check the correct hub ID and live connected-device count.
- Confirm the test passcode is prefilled, masked, and the eye works.
- Try an incorrect passcode: centered error disappears after three seconds;
  location and message remain intact and no reference popup appears.
- Use the operator-provided passcode and send a test report from a mini hub.
  Confirm queued status and a server-generated reference, not guaranteed delivery.
- Save or copy the reference. Verify the popup cannot close for ten seconds.
- Try sending the identical report again: reuse the confirmation, do not queue
  another copy. Clear form before submitting a genuinely new report.
- Test Clear form and multibyte text near both byte limits.
- Send directly from Node 1: popup must say recorded, not radio-delivered.
- Confirm the report and reference at the admin dashboard; compare its estimated
  PHT receipt time with a device having the correct date/time.
- Expand View details, then reboot Node 1 and repeat a receipt-time check.
- Disconnect during submission: no false success; ambiguous acceptance retains
  the warning that retrying could create a duplicate.

Do not use live emergency reports during these checks. No physical-node test,
upload, Git commit or push is implied by successful host tests/builds.

## Verification: October 28, 2026

- Resident portal and admin dashboard JavaScript suites passed.
- Generated embedded headers match their source pages exactly.
- Browser check passed for the eye toggle and Clear form before the requested test prefill was added; host tests cover restoring that prefill.
- Combined `node1` build succeeded: 152620 bytes static RAM, 933497 bytes program.
- Combined `node2` build succeeded: 83484 bytes static RAM, 933701 bytes program.
- Builds are under `%LOCALAPPDATA%/ThesisReceiptClock/build/node1` and `node2`.
- Other node targets were not rebuilt in this verification pass; select the
  matching target when building/uploading each additional board.
- No boards were flashed; main-hub and mini-hub physical tests remain pending.
