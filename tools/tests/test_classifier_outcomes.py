"""Classifier comparisons must not infer truth from ACKs or untried links."""
import sys
import unittest
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from analyze_run import labelled_tx, classifier_scores
from test_receiver_labels import recording


class ClassifierOutcomes(unittest.TestCase):
    def with_verdicts(self, **kwargs):
        frame, spec = recording(**kwargs)
        frame['cart_class'] = 'Risky'
        frame['heur_class'] = 'Safe'
        return frame, spec

    def test_no_coverage_never_uses_ack_or_noack(self):
        frame, _ = self.with_verdicts()
        self.assertTrue(labelled_tx(frame).empty)
        frame.loc[frame.event == 'ACK', 'event'] = 'NOACK'
        self.assertTrue(labelled_tx(frame).empty)

    def test_received_packet_is_safe_even_if_ack_was_lost(self):
        frame, spec = self.with_verdicts(ack=False)
        result = labelled_tx(frame, spec)
        self.assertEqual(result.danger.tolist(), [0])
        self.assertEqual(result.cart_class.tolist(), ['Risky'])
        self.assertEqual(result.heur_class.tolist(), ['Safe'])

    def test_non_reception_requires_reviewed_complete_endpoints(self):
        frame, spec = self.with_verdicts(receive=None, ack=False)
        self.assertEqual(labelled_tx(frame, spec).danger.tolist(), [1])
        spec['coverage'] = spec['coverage'][:1]
        self.assertTrue(labelled_tx(frame, spec).empty)

    def test_rejected_delayed_and_conflicting_outcomes_excluded(self):
        for kwargs in ({'receive': 'reject'}, {'received_at': 1250},
                       {'receive': None, 'ack': True}):
            frame, spec = self.with_verdicts(**kwargs)
            self.assertTrue(labelled_tx(frame, spec).empty)

    def test_untried_link_is_not_a_classifier_instance(self):
        frame, spec = self.with_verdicts()
        # Classification/avoidance without an actual data TX is not an outcome.
        frame.loc[frame.event == 'TX', 'event'] = 'AVOID'
        self.assertTrue(labelled_tx(frame, spec).empty)

    def test_verdicts_stay_attached_to_the_actual_chosen_hop(self):
        frame, spec = self.with_verdicts()
        result = labelled_tx(frame, spec)
        self.assertEqual(result.peer.tolist(), [3])
        self.assertEqual(result.id.tolist(), [50])
        self.assertEqual(result.label_basis.tolist(), ['receiver_reconciled_v1'])

    def test_confusion_metrics_use_danger_as_positive(self):
        frame = pd.DataFrame(dict(danger=[1, 1, 0, 0], cart_class=['Risky', 'Safe', 'Risky', 'Safe']))
        result = classifier_scores(frame, 'cart_class')
        self.assertEqual([result[key] for key in ('tp', 'fp', 'fn', 'tn')], [1, 1, 1, 1])
        self.assertEqual(result['recall'], 0.5)
        self.assertEqual(result['f1'], 0.5)

    def test_undefined_recall_and_missing_evidence_remain_visible(self):
        result = classifier_scores(pd.DataFrame(dict(danger=[0], cart_class=['Safe'])), 'cart_class')
        self.assertTrue(pd.isna(result['recall']))
        frame, _ = self.with_verdicts()
        result = labelled_tx(frame)
        self.assertEqual(result.attrs['outcome_audit'][0]['outcome_reason'], 'no_reviewed_coverage')


if __name__ == '__main__':
    unittest.main()
