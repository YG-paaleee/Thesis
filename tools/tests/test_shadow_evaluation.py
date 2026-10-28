"""Artificial fixtures only, not training data or a frozen field model."""
import json
import sys
import tempfile
import subprocess
import unittest
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from model_provenance import stamp_header, freeze_record
from shadow_evaluation import read_classifier_plan, shadow_rows
from test_receiver_labels import recording

MODEL = 'a' * 64


def fixture(**kwargs):
    frame, coverage = recording(**kwargs)
    frame['cart_class'] = 'Risky'
    frame['heur_class'] = 'Safe'
    mask = frame.event == 'CONFIG'
    frame.loc[mask, 'detail'] = frame.loc[mask, 'detail'].str.replace(
        'cfg=baseline', f'cfg=baseline;cart=1;model={MODEL}', regex=False)
    plan = dict(model_id=MODEL, evaluation_sessions=['S1'], development_sessions=['TRAIN-01'])
    return frame, coverage, plan


class ShadowSelection(unittest.TestCase):
    def test_independent_baseline_with_frozen_verdicts_eligible(self):
        frame, coverage, plan = fixture()
        rows = shadow_rows(frame, coverage, plan)
        self.assertEqual(rows.classifier_eligible.tolist(), [True])
        self.assertEqual(rows.recorded_model_id.tolist(), [MODEL])

    def test_no_plan_or_coverage_does_not_produce_scores(self):
        frame, coverage, plan = fixture()
        self.assertFalse(shadow_rows(frame, coverage).classifier_eligible.any())
        self.assertFalse(shadow_rows(frame, None, plan).classifier_eligible.any())

    def test_full_and_survey_builds_excluded(self):
        for config in ('full', 'range-survey', 'heuristic', 'unknown'):
            frame, coverage, plan = fixture()
            frame['config'] = config
            rows = shadow_rows(frame, coverage, plan)
            self.assertEqual(rows.classifier_exclusion.tolist(), ['not_baseline'])

    def test_development_and_unplanned_sessions_excluded(self):
        frame, coverage, plan = fixture()
        plan['evaluation_sessions'] = ['NEW']
        self.assertEqual(shadow_rows(frame, coverage, plan).classifier_exclusion.tolist(), ['session_not_in_plan'])
        plan['development_sessions'] = ['S1']
        self.assertEqual(shadow_rows(frame, coverage, plan).classifier_exclusion.tolist(), ['development_session'])

    def test_missing_wrong_or_mixed_model_identity_excluded(self):
        for value in ('unavailable', 'b' * 64, ''):
            frame, coverage, plan = fixture()
            frame['detail'] = frame.detail.str.replace(MODEL, value, regex=False)
            self.assertFalse(shadow_rows(frame, coverage, plan).classifier_eligible.any())
        frame, coverage, plan = fixture()
        extra = frame[frame.event == 'CONFIG'].copy()
        extra['detail'] = extra.detail.str.replace(MODEL, 'b' * 64, regex=False)
        self.assertFalse(shadow_rows(pd.concat([frame, extra]), coverage, plan).classifier_eligible.any())

    def test_missing_paired_verdict_excluded(self):
        frame, coverage, plan = fixture()
        frame['cart_class'] = ''
        self.assertEqual(shadow_rows(frame, coverage, plan).classifier_exclusion.tolist(), ['missing_paired_verdicts'])

    def test_later_success_cannot_replace_failed_first_attempt(self):
        frame, coverage, plan = fixture(received_at=1480, retry_at=1400, ack=False)
        rows = shadow_rows(frame, coverage, plan)
        self.assertEqual(rows.classifier_eligible.tolist(), [True, False])
        self.assertEqual(rows.label.tolist(), [1, 0])
        self.assertEqual(rows.iloc[1].classifier_exclusion, 'later_retry')

    def test_missing_first_outcome_cannot_be_replaced_by_retry(self):
        frame, coverage, plan = fixture(received_at=1480, retry_at=1400, ack=False)
        frame = frame[~((frame.event == 'TX_DONE') & (frame.ms == 1100))]
        rows = shadow_rows(frame, coverage, plan)
        self.assertFalse(rows.classifier_eligible.any())


class FrozenPlan(unittest.TestCase):
    def make_files(self, folder):
        header = folder / 'model.h'
        header.write_text(stamp_header('#ifndef CART_MODEL_H\n#define CART_MODEL_H\n// ARTIFICIAL TEST HEADER\n#endif\n'))
        report = {**freeze_record(header, ['TRAIN', 'VALIDATION', 'DEVELOPMENT-TEST']),
                  'train_source': 'data', 'split': 'session'}
        (folder / 'report.json').write_text(json.dumps(report))
        plan = dict(purpose='independent_baseline_shadow', evaluation_sessions=['EVAL-NEW'],
                    freeze_evidence='ARTIFICIAL TEST FIXTURE', training_report='report.json', model_header='model.h')
        location = folder / 'plan.json'
        location.write_text(json.dumps(plan))
        return location, plan, report

    def test_read_matching_artifacts_and_relative_paths(self):
        with tempfile.TemporaryDirectory() as temp:
            location, plan, report = self.make_files(Path(temp))
            loaded = read_classifier_plan(location)
            self.assertEqual(loaded['model_id'], report['model_id'])
            self.assertEqual(loaded['development_sessions'], ['DEVELOPMENT-TEST', 'TRAIN', 'VALIDATION'])

    def test_training_validation_and_development_test_are_all_forbidden(self):
        with tempfile.TemporaryDirectory() as temp:
            location, plan, report = self.make_files(Path(temp))
            for session in report['development_sessions']:
                plan['evaluation_sessions'] = [session]
                location.write_text(json.dumps(plan))
                with self.assertRaisesRegex(ValueError, 'overlap'):
                    read_classifier_plan(location)

    def test_changed_header_or_missing_provenance_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            location, plan, report = self.make_files(folder)
            with (folder / 'model.h').open('a') as stream:
                stream.write('// changed\n')
            with self.assertRaisesRegex(ValueError, 'does not match'):
                read_classifier_plan(location)
            location, plan, report = self.make_files(folder)
            del report['development_sessions']
            (folder / 'report.json').write_text(json.dumps(report))
            with self.assertRaisesRegex(ValueError, 'every development'):
                read_classifier_plan(location)

    def test_empty_or_duplicate_sessions_and_wrong_protocol_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            location, plan, _ = self.make_files(Path(temp))
            for sessions in ([], [''], ['EVAL', 'EVAL']):
                plan['evaluation_sessions'] = sessions
                location.write_text(json.dumps(plan))
                with self.assertRaises(ValueError):
                    read_classifier_plan(location)
            location, plan, _ = self.make_files(Path(temp))
            plan['purpose'] = 'training'
            location.write_text(json.dumps(plan))
            with self.assertRaises(ValueError):
                read_classifier_plan(location)

    def test_actual_comparison_cli_loads_both_endpoints_and_saves_audit(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            location, plan, report = self.make_files(folder)
            frame, coverage, _ = fixture()
            plan['evaluation_sessions'] = ['S1']
            location.write_text(json.dumps(plan))
            frame['detail'] = frame.detail.str.replace(MODEL, report['model_id'], regex=False)
            frame['pc_epoch_ms'] = frame.ms + 10000
            frame.to_csv(folder / 'capture.csv', index=False)
            (folder / 'coverage.json').write_text(json.dumps(coverage))
            output = folder / 'results.csv'
            script = Path(__file__).resolve().parents[1] / 'analyze_run.py'
            result = subprocess.run([sys.executable, str(script), str(folder / 'capture.csv'),
                '--compare', '--coverage', str(folder / 'coverage.json'),
                '--classifier-plan', str(location), '--table', str(output)],
                capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn('Independent Baseline shadow evaluation', result.stdout)
            audit = pd.read_csv(folder / 'results_classifier_audit.csv')
            self.assertEqual(audit.classifier_eligible.tolist(), [True])
            self.assertEqual(audit.recorded_model_id.tolist(), [report['model_id']])
            self.assertTrue((folder / 'results_kruskal.csv').exists())
            self.assertTrue((folder / 'results_dunn_bonferroni.csv').exists())
            omnibus = pd.read_csv(folder / 'results_kruskal.csv')
            self.assertEqual(set(omnibus.status), {'unrecognised_tier'})


if __name__ == '__main__':
    unittest.main()
