#!/usr/bin/env python3
"""
Quick metrics from a capture made with tools/capture_telemetry.py.

  python tools/analyze_run.py run01.csv

Reports, per priority class k:
  PDR      unique messages DELIVERed at the hub / unique messages created (NEW)
  Latency  pc_epoch_ms(DELIVER) - pc_epoch_ms(NEW), same (origin, id)
           Valid when the origin node and the hub were both captured on this PC.
  PQA      share of k=1 data transmissions sent with nothing more urgent waiting
           (ahead == 0); also how many older, less urgent packets they overtook.
Messages are keyed on (origin, id); duplicates are counted once.

Requires: pip install pandas
"""

import sys

import pandas as pd


def main(path: str) -> None:
    df = pd.read_csv(path)
    new = df[df.event == "NEW"].drop_duplicates(["origin", "id"])
    delivered = df[df.event == "DELIVER"].drop_duplicates(["origin", "id"])

    print(f"File: {path}   rows: {len(df)}   nodes: {sorted(df.node.unique().tolist())}\n")
    print("PDR and end-to-end latency (by k)")
    merged = new.merge(delivered[["origin", "id", "pc_epoch_ms"]], on=["origin", "id"],
                       how="left", suffixes=("_new", "_deliver"))
    merged["latency_ms"] = merged.pc_epoch_ms_deliver - merged.pc_epoch_ms_new
    for k, group in merged.groupby("k"):
        sent, got = len(group), int(group.latency_ms.notna().sum())
        lat = group.latency_ms.dropna()
        lat_text = (f"mean {lat.mean():.0f} ms, median {lat.median():.0f} ms, max {lat.max():.0f} ms"
                    if len(lat) else "no deliveries")
        print(f"  k={k}: PDR {got}/{sent} = {100 * got / sent:.2f}%   latency {lat_text}")
    if new.empty:
        print("  no NEW rows: was the origin node captured?")

    print("\nPriority Queuing Accuracy (data TX rows with k=1)")
    tx = df[(df.event == "TX") & (df.type != 1) & (df.type != 3) & df.ahead.notna()]
    sos = tx[tx.k == 1]
    if sos.empty:
        print("  no k=1 transmissions with queue state logged")
    else:
        correct = int((sos.ahead == 0).sum())
        print(f"  {correct}/{len(sos)} = {100 * correct / len(sos):.2f}% sent with nothing more urgent waiting")
        print(f"  overtook older lower-priority packets in {int((sos.bypassed > 0).sum())} of them "
              f"(total {int(sos.bypassed.sum())} packets bypassed)")
        late = sos[sos.ahead > 0]
        if not late.empty:
            print("  transmissions with something more urgent still waiting:")
            print(late[["pc_epoch_ms", "node", "origin", "id", "queue_len", "dtn_len", "ahead"]]
                  .to_string(index=False))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("usage: python tools/analyze_run.py <capture.csv>")
    main(sys.argv[1])
