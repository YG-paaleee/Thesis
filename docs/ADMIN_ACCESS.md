# Main hub administrative access

Updated 2026-10-27 for Firmware Task List Priority 2. Software implementation is ready for device verification; no board was configured or flashed by this work.

## Current behaviour

Only V1 serves `/admin` and `/api/live_incidents`. Both routes use the same authentication gate. Other nodes return 404 rather than exposing the dashboard or incident records.

The username is `admin`. There is no default administrator password. Until an operator sets one through V1's physical USB serial connection, these routes return an unavailable/configuration response and expose no incidents. A configured V1 challenges unauthenticated requests with the web library's authentication mechanism. Incident API responses request no caching.

The operator-set password is saved in the board's Preferences storage. It is separate from the community submission passcode. Updating or entering it is an operator task before recording; it is not included in the Group Logging Kit and not distributed in the resident page.

## Provision V1 when the board is available

1. Flash the updated V1 firmware and connect it through USB.
2. Close recording programs on that port. Open a serial monitor at 115200 baud with newline command submission.
3. Choose a private administrator password of 12 to 64 printable characters, with no spaces. Keep it in the group's approved private record.
4. Type `admin password ` followed by the chosen password and press Enter. Do not use these instructions' words as a password. Wait for the saved confirmation; the firmware does not print the password back.
5. Close the serial monitor before opening a capture program. Configure access before collecting shared logs, since a terminal with local echo may display what the operator types.
6. Connect to V1 Wi-Fi, open `/admin`, and sign in as `admin` using the chosen password. Verify the API also requires authentication.
7. Reset V1 and confirm the stored password still works. Verify V2 rejects both admin paths. Test an incorrect password too.

Changing a password may require a new private browser session to avoid previously cached browser credentials. The physical USB command can replace a forgotten password. This is local prototype administration; no TLS deployment or encrypted-at-rest credential storage is introduced by this change.

## Resident passcode

The resident page now asks for an operator-provided community passcode without embedding the value, prefilling it, showing a default, or comparing against a browser-side secret. It sends the entered value to the existing server-side credential check. Error handling no longer prints the credential-bearing payload to the browser console.

Invalid credentials must still be rejected and valid ones accepted in the device pilot. A blank resident field is intentional; the administrator and community credentials are different.
