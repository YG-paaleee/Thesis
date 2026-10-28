"""Conservative next-hop acceptance labels from reviewed paired capture evidence.

No coverage manifest means no verified data labels. A manifest records separately
verified clock mappings and observation continuity; it is not generated from ACKs.
No packet layout changes: identical-frame retries with overlapping windows are
ambiguous and remain unlabelled.
"""
import json
import math
from pathlib import Path

import pandas as pd


def detail_fields(value):
    return dict(part.split('=', 1) for part in str(value).split(';') if '=' in part)


def read_coverage(path):
    if path is None:
        return None
    spec = json.loads(Path(path).read_text(encoding='utf-8'))
    if spec.get('target') != 'next_hop_acceptance':
        raise ValueError('Coverage target must be next_hop_acceptance')
    for name in ('acceptance_grace_ms', 'observation_tail_ms'):
        value = spec.get(name)
        if not isinstance(value, (float, int)) or not math.isfinite(value) or value < 0:
            raise ValueError(f'{name} must be a finite nonnegative number')
    records = spec.get('coverage', [])
    for record in records:
        for name in ('start_ms', 'end_ms', 'epoch_offset_ms', 'uncertainty_ms'):
            value = record.get(name)
            if not isinstance(value, (float, int)) or not math.isfinite(value):
                raise ValueError(f'Coverage {name} must be finite')
        if record['end_ms'] <= record['start_ms'] or record['uncertainty_ms'] < 0:
            raise ValueError('Invalid coverage interval or clock uncertainty')
        if not all(record.get(k) is not None for k in ('session', 'node', 'boot')):
            raise ValueError('Coverage needs session, node and boot')
        if record.get('verified') is not True or not str(record.get('evidence', '')).strip():
            raise ValueError('Every coverage interval needs verified=true and evidence')
    return spec


def reconciled_rows(df, spec=None):
    """Return every data TX candidate, including excluded rows and their reasons."""
    work = df.copy().reset_index(drop=True)
    work['_meta'] = work.detail.map(detail_fields)
    work['_boot'] = work._meta.map(lambda m: m.get('boot', ''))
    work['_seq'] = pd.to_numeric(work._meta.map(lambda m: m.get('seq')), errors='coerce')
    work['_frame'] = work._meta.map(lambda m: m.get('frame', ''))
    work['_attempt'] = work._meta.map(lambda m: m.get('attempt', ''))
    tx = work[(work.event == 'TX') & work.type.isin([0, 2])].copy()
    tx['source'] = 'data'
    tx['link'] = tx.apply(lambda r: f'V{int(r.node)}->V{int(r.peer)}' if pd.notna(r.peer) else '', axis=1)
    tx['boot'] = tx._boot
    tx['attempt'] = tx._attempt
    tx['frame'] = tx._frame
    tx['label'] = float('nan')
    tx['label_basis'] = 'receiver_reconciled_v1'
    tx['outcome'] = 'unknown'
    tx['outcome_reason'] = 'no_reviewed_coverage'
    tx['receiver_file'] = ''
    tx['receiver_ms'] = float('nan')
    if spec is None:
        return tx.drop(columns=[c for c in tx if c.startswith('_')])

    def coverage(row):
        matches = [c for c in spec['coverage'] if str(c['session']) == str(row.session)
                   and c['node'] == row.node and str(c['boot']) == row._boot
                   and c['start_ms'] <= row.ms <= c['end_ms']]
        return matches[0] if len(matches) == 1 else None

    def stream_for(c):
        return work[(work.session.astype(str) == str(c['session'])) & (work.node == c['node'])
                    & (work._boot == str(c['boot']))].sort_values('ms', kind='stable')

    def continuous(c, low, high):
        if c['start_ms'] > low or c['end_ms'] < high:
            return False
        stream = stream_for(c)
        if stream.empty or stream._seq.isna().any() or stream._seq.duplicated().any():
            return False  # duplicate endpoint captures are not independent evidence
        before, after = stream[stream.ms <= low], stream[stream.ms >= high]
        if before.empty or after.empty:
            return False
        a, b = before.iloc[-1], after.iloc[0]
        interval = stream[(stream.ms >= a.ms) & (stream.ms <= b.ms)]
        return bool((interval._seq.diff().dropna() == 1).all())

    # Prepare all windows first; no receiver event may label two attempts.
    windows = {}
    ambiguous_starts = set()
    for index, row in tx.iterrows():
        reason = 'missing_attempt_metadata'
        if not row._boot or not row._frame or not row._attempt:
            tx.at[index, 'outcome_reason'] = reason
            continue
        sender = coverage(row)
        if sender is None:
            tx.at[index, 'outcome_reason'] = 'missing_sender_coverage'
            continue
        same = work[(work.session == row.session) & (work.node == row.node)
                    & (work._boot == row._boot) & (work._attempt == row._attempt)]
        starts = same[(same.event == 'TX') & same.type.isin([0, 2])]
        ends = same[same.event.isin(['TX_DONE', 'TX_ERROR'])]
        if len(starts) != 1 or len(ends) != 1:
            tx.at[index, 'outcome_reason'] = 'missing_or_ambiguous_completion'
            continue
        done = ends.iloc[0]
        if (done.event == 'TX_ERROR' or done.ms < row.ms or done.origin != row.origin
                or done.id != row.id or done.peer != row.peer or done.type != row.type):
            tx.at[index, 'outcome_reason'] = 'transmission_not_completed'
            continue
        start = row.ms + sender['epoch_offset_ms']
        deadline = done.ms + sender['epoch_offset_ms'] + spec['acceptance_grace_ms']
        finish = deadline + spec['observation_tail_ms']
        # A retry with missing completion/coverage cannot be ignored merely
        # because it failed to produce its own eligible matching window.
        next_starts = tx[(tx.session == row.session) & (tx.node == row.node)
                         & (tx._boot == row._boot) & (tx.origin == row.origin)
                         & (tx.id == row.id) & (tx.peer == row.peer)
                         & (tx.ms > row.ms)]
        if not next_starts.empty:
            next_start = next_starts.ms.min() + sender['epoch_offset_ms']
            if next_start <= finish + sender['uncertainty_ms']:
                tx.at[index, 'outcome_reason'] = 'ambiguous_retry_window'
                ambiguous_starts.add(index)
        receivers = [c for c in spec['coverage'] if str(c['session']) == str(row.session)
                     and c['node'] == row.peer
                     and c['start_ms'] + c['epoch_offset_ms'] <= start
                     and c['end_ms'] + c['epoch_offset_ms'] >= finish]
        if len(receivers) != 1:
            tx.at[index, 'outcome_reason'] = 'missing_or_ambiguous_receiver_coverage'
            continue
        receiver = receivers[0]
        uncertainty = sender['uncertainty_ms'] + receiver['uncertainty_ms']
        slo = start - uncertainty - sender['epoch_offset_ms']
        shi = finish + uncertainty - sender['epoch_offset_ms']
        rlo = start - uncertainty - receiver['epoch_offset_ms']
        rhi = finish + uncertainty - receiver['epoch_offset_ms']
        if not continuous(sender, slo, shi) or not continuous(receiver, rlo, rhi):
            tx.at[index, 'outcome_reason'] = 'incomplete_or_gapped_observation'
            continue
        receiver_stream = stream_for(receiver)
        configs = receiver_stream[receiver_stream.event == 'CONFIG']
        if row.config == 'unknown' or configs.empty or not (configs.config == row.config).all():
            tx.at[index, 'outcome_reason'] = 'missing_or_mismatched_configuration'
            continue
        events = receiver_stream[(receiver_stream.peer == row.node) & (receiver_stream.origin == row.origin)
                                 & (receiver_stream.id == row.id) & (receiver_stream.type == row.type)]
        times = events.ms + receiver['epoch_offset_ms']
        events = events[(times >= start - uncertainty) & (times <= finish + uncertainty)]
        windows[index] = (row, start, deadline, finish, uncertainty, receiver, events)

    event_owners = {}
    for index, (_, _, _, _, _, _, events) in windows.items():
        for event_index in events[events.event.isin(['RX_ACCEPT', 'RX_REJECT'])].index:
            event_owners.setdefault(event_index, set()).add(index)
    for index, (row, start, deadline, finish, uncertainty, receiver, events) in windows.items():
        if index in ambiguous_starts:
            continue
        decisions = events[events.event.isin(['RX_ACCEPT', 'RX_REJECT']) & (events._frame == row._frame)]
        if any(len(event_owners.get(i, set())) > 1 for i in decisions.index):
            tx.at[index, 'outcome_reason'] = 'ambiguous_retry_window'
            continue
        if len(decisions) > 1:
            tx.at[index, 'outcome_reason'] = 'multiple_receiver_decisions'
            continue
        if len(decisions) == 1:
            event = decisions.iloc[0]
            when = event.ms + receiver['epoch_offset_ms']
            tx.at[index, 'receiver_file'] = event.file
            tx.at[index, 'receiver_ms'] = event.ms
            if when - uncertainty < start or (when - uncertainty <= deadline < when + uncertainty):
                tx.at[index, 'outcome_reason'] = 'ambiguous_timing'
            elif when - uncertainty > deadline:
                tx.at[index, 'outcome'] = 'delayed'
                tx.at[index, 'outcome_reason'] = 'outside_acceptance_window'
            elif event.event == 'RX_REJECT':
                tx.at[index, 'outcome'] = 'rejected'
                tx.at[index, 'outcome_reason'] = event._meta.get('reason', 'receiver_rejected')
            else:
                tx.at[index, 'label'] = 0
                tx.at[index, 'outcome'] = 'safe'
                tx.at[index, 'outcome_reason'] = event._meta.get('reason', 'accepted')
        else:
            # A raw RX indicates reception, but not valid acceptance. No accepted
            # event must not turn a received/rejected/malformed frame into loss.
            raw = events[(events.event == 'RX') & events.detail.str.startswith('to_me', na=False)]
            sender_events = work[(work.session == row.session) & (work.node == row.node)
                                 & (work._boot == row._boot) & (work.origin == row.origin)
                                 & (work.id == row.id) & (work.peer == row.peer)
                                 & (work.event == 'ACK') & (work.ms >= row.ms)
                                 & (work.ms + coverage(row)['epoch_offset_ms'] <= finish + uncertainty)]
            if not sender_events.empty:
                tx.at[index, 'outcome_reason'] = 'ack_receiver_evidence_conflict'
            elif not raw.empty:
                tx.at[index, 'outcome_reason'] = 'reception_without_matched_decision'
            else:
                tx.at[index, 'label'] = 1
                tx.at[index, 'outcome'] = 'danger'
                tx.at[index, 'outcome_reason'] = 'verified_non_reception'
    return tx.drop(columns=[c for c in tx if c.startswith('_')])
