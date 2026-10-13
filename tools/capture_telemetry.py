#!/usr/bin/env python3
"""
Capture the machine-readable event log from one or more LoRa nodes over USB.

Every node prints rows that start with "CSV," (see logCsv() in src/main.cpp).
This script keeps ONLY those rows, ignores the human-readable debug lines, and
stamps each row with the PC's clock. With all nodes plugged into the same PC
(Phase 2 bench / stress tests) that PC timestamp is one shared clock, so
end-to-end latency = pc_epoch_ms(DELIVER at V1) - pc_epoch_ms(NEW at origin).

On connect it also sends "time <unix-seconds>" to each node, so the node clocks
(and the hub dashboard's latency column) are set too.

Usage (Windows examples):
  python tools/capture_telemetry.py COM3
  python tools/capture_telemetry.py COM3 COM5 COM7 --out run01.csv
  python tools/capture_telemetry.py COM3 COM5 --target 300      # stop after 300 CART labels

  CART training data (passive: the node labels every heartbeat it expects from its neighbours):
  python tools/capture_telemetry.py COM8 --session F1-V1-normal --out F1-V1-normal.csv

  Final evaluation (laptop sends a test message from the node every 30 s):
  python tools/capture_telemetry.py COM5 --inject COM5 --every 30 --session E1-heap --out E1-heap.csv

Outputs:
  <out>.csv        pc_epoch_ms,port,session,<node CSV columns...>   (load with pandas)
  <out>_raw.log    every line from every port, for debugging

Requires: pip install pyserial
"""

import argparse
import sys
import threading
import time
from pathlib import Path

try:
    import serial
except ImportError:
    sys.exit("pyserial is missing: run  pip install pyserial")

BAUD = 115200
CSV_PREFIX = "CSV,"
NODE_HEADER = ("ms,node,event,origin,id,k,type,peer,rssi,snr,peer_batt_pct,peer_traffic,"
               "peer_queue,peer_hb_age_ms,self_batt_pct,self_used_mah,mac_retries,bytes,queue_len,dtn_len,"
               "ahead,bypassed,detail")
LABEL_EVENTS = {"ACK", "NOACK", "HB_OK", "HB_MISS"}   # one labelled link attempt each (CART rows)
FAIL_EVENTS = {"NOACK", "HB_MISS"}


class Capture:
    def __init__(self, out_csv: Path, target: int, session: str):
        self.out_csv = out_csv
        self.raw_log = out_csv.with_name(out_csv.stem + "_raw.log")
        self.target = target
        self.session = session.replace(",", "_")
        self.lock = threading.Lock()
        self.rows = 0
        self.labelled = 0
        self.failed = 0
        self.header_columns = NODE_HEADER.count(",") + 1
        self.stop = threading.Event()
        self.csv_file = open(self.out_csv, "w", encoding="utf-8", newline="")
        self.raw_file = open(self.raw_log, "w", encoding="utf-8", newline="")
        self.csv_file.write("pc_epoch_ms,port,session," + NODE_HEADER + "\n")

    def handle_line(self, port: str, line: str) -> None:
        pc_ms = int(time.time() * 1000)
        with self.lock:
            self.raw_file.write(f"{pc_ms} {port} {line}\n")
            if not line.startswith(CSV_PREFIX):
                return                                   # debug line: never counted as data
            body = line[len(CSV_PREFIX):]
            if body.startswith("ms,"):
                if body != NODE_HEADER:
                    print(f"\n[{port}] WARNING: firmware CSV columns differ from this script. "
                          "Update NODE_HEADER or re-flash.", file=sys.stderr)
                return                                   # header printed at node boot
            if body.count(",") + 1 != self.header_columns:
                return                                   # incomplete row (e.g. cut by a reset)
            self.csv_file.write(f"{pc_ms},{port},{self.session},{body}\n")
            self.rows += 1
            fields = body.split(",")
            if fields[2] in LABEL_EVENTS:
                self.labelled += 1
                if fields[2] in FAIL_EVENTS:
                    self.failed += 1
            if self.rows % 10 == 0:
                self.csv_file.flush()
                self.raw_file.flush()
            share = f"{100 * self.failed / self.labelled:.0f}%" if self.labelled else "-"
            print(f"\rrows: {self.rows}   CART labels: {self.labelled}"
                  + (f"/{self.target}" if self.target else "")
                  + f"   failures (HB_MISS/NOACK): {self.failed} ({share})   ", end="", flush=True)
            if self.target and self.labelled >= self.target:
                self.stop.set()

    def close(self) -> None:
        with self.lock:
            self.csv_file.close()
            self.raw_file.close()


def open_port(name: str) -> serial.Serial:
    port = serial.Serial()
    port.port = name
    port.baudrate = BAUD
    port.timeout = 0.5
    # Keep DTR/RTS low so opening the port does not reset the ESP32.
    port.dtr = False
    port.rts = False
    port.open()
    return port


class Injector:
    """Sends "sos <k> <location>|<message>" to a node on a timer (serial command in main.cpp)."""

    def __init__(self, every_s: float, priorities, session: str, offset_s: float):
        self.every_s = every_s
        self.priorities = priorities
        self.location = session[:40] or "FIELD"
        self.next_at = time.time() + 15 + offset_s   # let heartbeats/routes settle first
        self.count = 0

    def due(self) -> bool:
        return time.time() >= self.next_at

    def command(self, port_name: str) -> bytes:
        k = self.priorities[self.count % len(self.priorities)]
        self.count += 1
        self.next_at += self.every_s
        if self.next_at < time.time():                # PC slept / port stalled: do not burst
            self.next_at = time.time() + self.every_s
        return f"sos {k} {self.location}|CART test {port_name} #{self.count}\n".encode()


def reader(name: str, capture: Capture, sync_clock: bool, injector=None) -> None:
    try:
        port = open_port(name)
    except serial.SerialException as error:
        print(f"\n[{name}] could not open: {error}", file=sys.stderr)
        return
    print(f"[{name}] connected" + (f", sending a test message every {injector.every_s:g} s" if injector else ""))
    if sync_clock:
        port.write(f"time {int(time.time())}\n".encode())
    buffer = b""
    try:
        while not capture.stop.is_set():
            if injector and injector.due():
                port.write(injector.command(name))
            # Read whatever has arrived right away (blocks at most 0.5 s only when idle),
            # so each row is stamped within a few ms of reaching the PC.
            chunk = port.read(port.in_waiting or 1)
            if not chunk:
                continue
            buffer += chunk
            while b"\n" in buffer:
                raw, buffer = buffer.split(b"\n", 1)
                line = raw.decode("utf-8", errors="replace").strip()
                if line:
                    capture.handle_line(name, line)
    except serial.SerialException as error:
        print(f"\n[{name}] disconnected: {error}", file=sys.stderr)
    finally:
        port.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("ports", nargs="+", help="serial ports, e.g. COM3 COM5 (Windows) or /dev/ttyUSB0")
    parser.add_argument("--out", default="empirical_telemetry_dataset.csv", help="output CSV file")
    parser.add_argument("--target", type=int, default=0,
                        help="stop after this many CART labels (HB_OK/HB_MISS/ACK/NOACK rows); 0 = until Ctrl+C")
    parser.add_argument("--no-time-sync", action="store_true", help="do not send the 'time' command to nodes")
    parser.add_argument("--session", default="",
                        help="label written on every row, e.g. A-V6-200m (default: output file name). "
                             "Used to split training/test data by session.")
    parser.add_argument("--inject", nargs="+", default=[], metavar="PORT",
                        help="ports whose node should send automatic test messages (never the hub V1)")
    parser.add_argument("--every", type=float, default=30.0,
                        help="seconds between injected messages per port (default 30; keep >= 20 at SF12)")
    parser.add_argument("--priorities", default="1,2,3",
                        help="priorities to cycle through for injected messages (default 1,2,3)")
    args = parser.parse_args()

    unknown = [p for p in args.inject if p not in args.ports]
    if unknown:
        sys.exit(f"--inject ports must also be listed as capture ports: {' '.join(unknown)}")
    if args.inject and args.every < 10:
        sys.exit("--every below 10 s would flood the SF12 channel")
    try:
        priorities = [int(k) for k in args.priorities.split(",") if k.strip()]
    except ValueError:
        sys.exit("--priorities must look like 1,2,3")
    if not priorities or any(k not in (1, 2, 3) for k in priorities):
        sys.exit("--priorities must only contain 1, 2 or 3")

    session = args.session or Path(args.out).stem
    capture = Capture(Path(args.out), args.target, session)
    stagger = args.every / max(len(args.inject), 1)
    threads = [threading.Thread(target=reader,
                                args=(p, capture, not args.no_time_sync,
                                      Injector(args.every, priorities, session, stagger * args.inject.index(p))
                                      if p in args.inject else None),
                                daemon=True)
               for p in args.ports]
    for thread in threads:
        thread.start()
    print(f"Writing {capture.out_csv} (raw log: {capture.raw_log}). Press Ctrl+C to stop.")
    try:
        while not capture.stop.is_set() and any(t.is_alive() for t in threads):
            time.sleep(0.2)
    except KeyboardInterrupt:
        pass
    capture.stop.set()
    for thread in threads:
        thread.join(timeout=2)
    capture.close()
    print(f"\nSaved {capture.rows} rows ({capture.labelled} CART labels, {capture.failed} failures) "
          f"to {capture.out_csv}")


if __name__ == "__main__":
    main()
