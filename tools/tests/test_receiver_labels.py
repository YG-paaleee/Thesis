"""Artificial examples only: these tests are not field training data."""
import sys
import unittest
import tempfile
import json
import subprocess
import ast
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from receiver_labels import reconciled_rows
from build_cart_dataset import data_rows, load


def recording(receive='accept', received_at=1080, ack=True, retry_at=None):
    rows = []
    def add(node, event, ms, detail='', **kw):
        row = dict(session='S1', file=f'node{node}.csv', config='baseline', node=node,
                   event=event, ms=ms, origin=2, id=50, peer=3 if node == 2 else 2,
                   type=2, k=3, detail=detail, rssi=-90, snr=3, peer_batt_pct=60,
                   peer_traffic=2, peer_hb_age_ms=100)
        row.update(kw)
        rows.append(row)
    add(2, 'CONFIG', 0, 'cfg=baseline')
    add(2, 'TX', 1000, 'attempt=1;frame=abc')
    add(2, 'TX_DONE', 1100, 'attempt=1;status=ok')
    if ack:
        add(2, 'ACK', 1150)
    if retry_at:
        add(2, 'TX', retry_at, 'attempt=2;frame=abc')
        add(2, 'TX_DONE', retry_at + 100, 'attempt=2;status=ok')
    add(2, 'TX', 2000, 'heartbeat', type=1)
    add(3, 'CONFIG', 0, 'cfg=baseline')
    if receive:
        add(3, 'RX', received_at - 1, 'to_me')
        add(3, 'RX_ACCEPT' if receive == 'accept' else 'RX_REJECT', received_at,
            'frame=abc;reason=' + ('queued' if receive == 'accept' else 'queue_full'))
    add(3, 'RX', 2000, 'heartbeat', type=1)
    for node in (2, 3):
        local = sorted((r for r in rows if r['node'] == node), key=lambda r: r['ms'])
        for seq, row in enumerate(local, 1):
            row['detail'] += f';boot=b{node};seq={seq}'
    spec = dict(target='next_hop_acceptance', acceptance_grace_ms=100,
                observation_tail_ms=100, coverage=[dict(session='S1', node=n, boot=f'b{n}',
                start_ms=0, end_ms=2000, epoch_offset_ms=0, uncertainty_ms=0,
                verified=True, evidence='ARTIFICIAL TEST FIXTURE') for n in (2, 3)])
    return pd.DataFrame(rows), spec


class ReceiverLabels(unittest.TestCase):
    def outcome(self, df, spec):
        return reconciled_rows(df, spec).iloc[0]

    def test_accepted(self):
        df, spec = recording()
        self.assertEqual(self.outcome(df, spec).label, 0)

    def test_ack_loss_is_still_safe(self):
        df, spec = recording(ack=False)
        self.assertEqual(self.outcome(df, spec).label, 0)

    def test_no_manifest_does_not_turn_noack_into_loss(self):
        df, _ = recording(receive=None, ack=False)
        self.assertTrue(pd.isna(data_rows(df).iloc[0].label))

    def test_ack_only_without_receiver_evidence_is_unknown(self):
        df, spec = recording()
        spec['coverage'] = spec['coverage'][:1]
        self.assertTrue(pd.isna(self.outcome(df, spec).label))

    def test_confirmed_non_reception(self):
        df, spec = recording(receive=None, ack=False)
        self.assertEqual(self.outcome(df, spec).label, 1)

    def test_receiver_log_gap_is_unknown(self):
        df, spec = recording(receive=None)
        mask = (df.node == 3) & (df.ms == 2000)
        df.loc[mask, 'detail'] = 'heartbeat;boot=b3;seq=4'
        self.assertEqual(self.outcome(df, spec).outcome_reason, 'incomplete_or_gapped_observation')

    def test_rejection_is_not_radio_loss(self):
        df, spec = recording(receive='reject')
        row = self.outcome(df, spec)
        self.assertEqual(row.outcome, 'rejected')
        self.assertTrue(pd.isna(row.label))

    def test_late_acceptance_is_retained(self):
        df, spec = recording(received_at=1250)
        self.assertEqual(self.outcome(df, spec).outcome, 'delayed')

    def test_clock_boundary_is_unknown(self):
        df, spec = recording(received_at=1195)
        spec['coverage'][1]['uncertainty_ms'] = 10
        self.assertEqual(self.outcome(df, spec).outcome_reason, 'ambiguous_timing')

    def test_retry_is_not_assigned_to_first_attempt(self):
        df, spec = recording(received_at=1480, retry_at=1400, ack=False)
        results = reconciled_rows(df, spec)
        self.assertEqual(results.label.tolist(), [1, 0])

    def test_overlapping_retry_windows_are_unknown(self):
        df, spec = recording(received_at=1250, retry_at=1200, ack=False)
        results = reconciled_rows(df, spec)
        self.assertTrue(results.label.isna().all())
        self.assertEqual(set(results.outcome_reason), {'ambiguous_retry_window'})

    def test_unintended_receiver_does_not_establish_success(self):
        df, spec = recording(ack=False)
        df.loc[(df.node == 3) & df.event.isin(['RX_ACCEPT', 'RX']), 'peer'] = 4
        self.assertEqual(self.outcome(df, spec).label, 1)

    def test_ack_without_any_receiver_record_is_conflicting_evidence(self):
        df, spec = recording(receive=None, ack=True)
        self.assertEqual(self.outcome(df, spec).outcome_reason, 'ack_receiver_evidence_conflict')

    def test_retry_missing_completion_does_not_label_first_safe(self):
        df, spec = recording(received_at=1250, retry_at=1200, ack=False)
        df = df[~((df.event == 'TX_DONE') & (df.ms == 1300))]
        self.assertTrue(reconciled_rows(df, spec).label.isna().all())

    def test_duplicate_is_safe_without_another_delivery(self):
        df, spec = recording()
        df.loc[df.event == 'RX_ACCEPT', 'detail'] = 'frame=abc;reason=duplicate;boot=b3;seq=3'
        self.assertEqual(self.outcome(df, spec).label, 0)
        self.assertEqual((df.event == 'DELIVER').sum(), 0)

    def test_old_or_missing_completion_is_unknown(self):
        df, spec = recording()
        df = df[df.event != 'TX_DONE']
        self.assertEqual(self.outcome(df, spec).outcome_reason, 'missing_or_ambiguous_completion')

    def test_transmission_completion_error_is_unknown(self):
        df, spec = recording()
        df.loc[df.event == 'TX_DONE', 'event'] = 'TX_ERROR'
        self.assertEqual(self.outcome(df, spec).outcome_reason, 'transmission_not_completed')

    def test_capture_ends_too_soon(self):
        df, spec = recording(receive=None)
        spec['coverage'][1]['end_ms'] = 1200
        self.assertTrue(pd.isna(self.outcome(df, spec).label))

    def test_wrong_configuration_is_unknown(self):
        df, spec = recording()
        df.loc[df.node == 3, 'config'] = 'full'
        self.assertEqual(self.outcome(df, spec).outcome_reason, 'missing_or_mismatched_configuration')

    def test_receiver_reception_without_acceptance_is_unknown(self):
        df, spec = recording(ack=False)
        df.loc[df.event == 'RX_ACCEPT', 'event'] = 'OTHER'
        self.assertEqual(self.outcome(df, spec).outcome_reason, 'reception_without_matched_decision')

    def test_duplicate_capture_files_are_not_continuity_proof(self):
        df, spec = recording()
        duplicate = df[df.node == 3].copy()
        duplicate['file'] = 'duplicate.csv'
        df = pd.concat([df, duplicate], ignore_index=True)
        self.assertTrue(pd.isna(self.outcome(df, spec).label))

    def test_hub_only_capture_has_no_data_candidates(self):
        df, _ = recording()
        df = df[~((df.event == 'TX') & (df.type == 2))]
        self.assertEqual(len(reconciled_rows(df)), 0)

    def test_csv_to_cli_dataset_and_audit(self):
        df, spec = recording(ack=False)
        # Temporary fixtures live under this test directory, never the user's data.
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as directory:
            root = Path(directory).resolve()
            self.assertTrue(root.is_relative_to(Path(__file__).parent.resolve()))
            files = []
            for node in (2, 3):
                path = root / f'node{node}.csv'
                df[df.node == node].drop(columns=['config', 'file']).to_csv(path, index=False)
                files.append(str(path))
            loaded = load(files)
            self.assertEqual(set(loaded.config), {'baseline'})
            manifest = root / 'coverage.json'
            manifest.write_text(json.dumps(spec), encoding='utf-8')
            output = root / 'dataset.csv'
            result = subprocess.run([sys.executable, '-B', str(Path(__file__).resolve().parents[1] / 'build_cart_dataset.py'),
                *files, '--coverage', str(manifest), '--out', str(output)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            dataset = pd.read_csv(output)
            self.assertEqual(dataset.label.tolist(), [0])
            self.assertEqual(dataset.label_basis.tolist(), ['receiver_reconciled_v1'])
            self.assertEqual(len(pd.read_csv(root / 'dataset_audit.csv')), 1)

    def test_training_rejects_legacy_ack_labels(self):
        # Execute the actual loader without requiring the later ML dependencies.
        source = Path(__file__).resolve().parents[1] / 'train_cart.py'
        parsed = ast.parse(source.read_text(encoding='utf-8'))
        pieces = [item for item in parsed.body if
                  (isinstance(item, ast.FunctionDef) and item.name == 'load') or
                  (isinstance(item, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'FEATURE_COLUMNS' for t in item.targets))]
        namespace = {'pd': pd, 'sys': sys}
        exec(compile(ast.Module(body=pieces, type_ignores=[]), str(source), 'exec'), namespace)
        load_training = namespace['load']
        df, _ = recording()
        df = df[df.event == 'TX'].copy()
        df['source'] = 'data'
        df['label'] = 0
        df['battery'] = df.peer_batt_pct
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as directory:
            root = Path(directory).resolve()
            self.assertTrue(root.is_relative_to(Path(__file__).parent.resolve()))
            path = root / 'legacy.csv'
            df.to_csv(path, index=False)
            with self.assertRaisesRegex(SystemExit, 'receiver-reconciled'):
                load_training(path, ['rssi', 'snr', 'battery', 'traffic'], 'data')

    def test_reset_cannot_supply_previous_boot_receiver_evidence(self):
        df, spec = recording()
        df.loc[df.node == 3, 'detail'] = df.loc[df.node == 3, 'detail'].str.replace('boot=b3', 'boot=new', regex=False)
        self.assertTrue(pd.isna(self.outcome(df, spec).label))


if __name__ == '__main__':
    unittest.main()
