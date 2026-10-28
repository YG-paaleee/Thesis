"""Report USB clock measurements; never marks receiver coverage verified."""
import argparse
import json
import math
from collections import defaultdict
from pathlib import Path


def probe_interval(sample, clock_step_tolerance_ms=5.0):
    keys = ['send_epoch_ms', 'receive_epoch_ms', 'send_mono_ms', 'receive_mono_ms', 'local_ms']
    if not all(isinstance(sample.get(k), (int, float)) and math.isfinite(sample[k]) for k in keys):
        raise ValueError('missing or nonfinite timing measurement')
    if not sample.get('boot') or not sample.get('probe'):
        raise ValueError('missing boot or probe identity')
    rtt = sample['receive_mono_ms'] - sample['send_mono_ms']
    wall = sample['receive_epoch_ms'] - sample['send_epoch_ms']
    if rtt < 0 or wall < 0 or abs(wall - rtt) > clock_step_tolerance_ms:
        raise ValueError('laptop clock step or invalid round-trip timestamps')
    # Millisecond node stamps and non-atomic PC clock reads need a rounding margin.
    lower = sample['send_epoch_ms'] - sample['local_ms'] - 2.0
    upper = sample['receive_epoch_ms'] - sample['local_ms'] + 2.0
    return dict(offset_lower_ms=lower, offset_upper_ms=upper,
                midpoint_offset_ms=(lower + upper) / 2,
                sample_uncertainty_ms=(upper - lower) / 2, round_trip_ms=rtt)


def report(path):
    records = [json.loads(line) for line in Path(path).read_text(encoding='utf-8').splitlines() if line.strip()]
    captures = [r for r in records if r.get('event') == 'CAPTURE']
    if len(captures) != 1:
        raise ValueError('Expected exactly one capture identity in a clock file')
    grouped = defaultdict(list)
    invalid = []
    seen = set()
    replies = set()
    for record in records:
        if record.get('event') != 'PROBE_REPLY':
            continue
        key = (record.get('port'), record.get('probe'))
        replies.add(key)
        try:
            if key in seen:
                raise ValueError('duplicate probe reply')
            seen.add(key)
            sample = dict(record, **probe_interval(record))
            grouped[(record['node'], record['boot'], record['port'])].append(sample)
        except ValueError as error:
            invalid.append(dict(probe=record.get('probe'), reason=str(error)))
    results = []
    for (node, boot, port), samples in grouped.items():
        samples.sort(key=lambda r: r['send_mono_ms'])
        warnings = []
        for previous, current in zip(samples, samples[1:]):
            wall = current['send_epoch_ms'] - previous['send_epoch_ms']
            mono = current['send_mono_ms'] - previous['send_mono_ms']
            if abs(wall - mono) > 5:
                warnings.append('laptop_wall_clock_changed_between_probes')
            if current['local_ms'] <= previous['local_ms']:
                warnings.append('local_uptime_nonincreasing_or_wrapped')
        lower = max(s['offset_lower_ms'] for s in samples)
        upper = min(s['offset_upper_ms'] for s in samples)
        if lower > upper:
            warnings.append('no_single_offset_fits_all_samples_drift_or_clock_change')
        if len(samples) < 2:
            warnings.append('insufficient_samples_to_check_drift')
        results.append(dict(node=node, boot=boot, port=port, samples=len(samples),
            local_start_ms=samples[0]['local_ms'], local_end_ms=samples[-1]['local_ms'],
            min_round_trip_ms=min(s['round_trip_ms'] for s in samples),
            max_round_trip_ms=max(s['round_trip_ms'] for s in samples),
            sample_offset_intersection_ms=[lower, upper] if lower <= upper else None,
            warnings=sorted(set(warnings)), measurements=samples, verified=False))
    requests = {(r.get('port'), r.get('probe')) for r in records if r.get('event') == 'PROBE_SEND'}
    return dict(capture=captures[0], clean_close=any(r.get('event') == 'CAPTURE_END' for r in records),
        unanswered_probes=len(requests - replies), invalid_samples=invalid, nodes=results,
        verified=False, limitation='USB measurements relate nodes to this laptop only. Cross-laptop reference, drift/handling bounds, recording continuity and observation windows require separate review.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('clock_log')
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    result = report(args.clock_log)
    if Path(args.out).resolve() == Path(args.clock_log).resolve():
        parser.error('Output cannot overwrite the raw clock log')
    Path(args.out).write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(f'Prepared report for {len(result["nodes"])} node boot(s); invalid samples: {len(result["invalid_samples"])}.')
    print('Not a verification certificate. Review cross-laptop reference and drift before generating coverage.')


if __name__ == '__main__':
    main()
