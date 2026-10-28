"""Artificial run summaries only; no thesis measurements are generated."""
import math
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from posthoc_stats import rank_comparisons, run_statistics, FORMAL_CONFIGS, PAIR_COLUMNS


def artificial_runs(tier='low'):
    return pd.DataFrame([dict(config=config, tier=tier, session=f'{config}-{tier}-{trial}',
        pdr=(10 * group + trial) / 50, pqa=(10 * group + trial) / 50,
        latency_ms=100 * group + trial)
        for group, config in enumerate(FORMAL_CONFIGS) for trial in range(10)])


class DunnBonferroni(unittest.TestCase):
    def test_known_untied_normal_tail_and_multiplicity(self):
        result, pairs = rank_comparisons({'C': range(21, 31), 'A': range(1, 11), 'B': range(11, 21)})
        self.assertEqual(result['posthoc'], 'dunn_bonferroni')
        self.assertEqual(len(pairs), 3)
        pair = next(p for p in pairs if (p['config_a'], p['config_b']) == ('A', 'C'))
        # Independently derived ranks: means 5.5 and 25.5, N=30, nA=nC=10.
        expected_raw = math.erfc(20 / math.sqrt(31))
        self.assertAlmostEqual(pair['p_raw'], expected_raw, places=12)
        self.assertAlmostEqual(pair['p_bonferroni'], expected_raw * 3, places=12)

    def test_ties_use_corrected_rank_variance(self):
        _, pairs = rank_comparisons({'A': [0]*5, 'B': [1]*5, 'C': [2]*5})
        pair = next(p for p in pairs if (p['config_a'], p['config_b']) == ('A', 'C'))
        # Rank means 3 and 13; tie-corrected variance gives z=sqrt(14).
        self.assertAlmostEqual(pair['p_raw'], math.erfc(math.sqrt(7)), places=12)
        self.assertAlmostEqual(pair['p_bonferroni'], 3 * math.erfc(math.sqrt(7)), places=12)

    def test_nonsignificant_omnibus_does_not_call_dunn(self):
        with patch('scikit_posthocs.posthoc_dunn', side_effect=AssertionError('Dunn must not run')):
            result, pairs = rank_comparisons({'A': [1,3,5,7,9], 'B': [2,4,6,8,10]})
        self.assertAlmostEqual(result['p'], 0.6015081344405895)
        self.assertEqual(result['posthoc'], 'not_significant')
        self.assertEqual(pairs, [])

    def test_identical_values_are_explicitly_unavailable(self):
        result, pairs = rank_comparisons({'A': [1]*5, 'B': [1]*5})
        self.assertEqual(result['status'], 'all_values_identical')
        self.assertTrue(math.isnan(result['p']))
        self.assertEqual(pairs, [])

    def test_missing_nonfinite_and_text_values_are_counted(self):
        result, _ = rank_comparisons({'A': [1,2,3,4,5,None,np.nan,np.inf,-np.inf,'bad'], 'B': range(10,15)})
        self.assertEqual(result['n'], {'A': 5, 'B': 5})
        self.assertEqual(result['excluded'], {'A': 5, 'B': 0})

    def test_small_or_empty_groups_not_silently_removed(self):
        for values in ([], [1,2,3,4]):
            result, pairs = rank_comparisons({'A': values, 'B': range(10), 'C': range(20,30)})
            self.assertEqual(result['status'], 'insufficient_runs')
            self.assertEqual(result['comparisons'], 3)
            self.assertEqual(pairs, [])
        self.assertEqual(rank_comparisons({'A': range(10)})[0]['status'], 'insufficient_groups')

    def test_adjusted_probabilities_capped_and_labels_not_positions(self):
        _, pairs = rank_comparisons({'z-full': [1,2,3,4,5], 'a-base': [2,3,4,5,6], 'm-other': range(40,45)})
        self.assertEqual({p['config_a'] for p in pairs} | {p['config_b'] for p in pairs}, {'z-full', 'a-base', 'm-other'})
        self.assertTrue(all(0 <= p['p_raw'] <= p['p_bonferroni'] <= 1 for p in pairs))
        self.assertTrue(any(p['p_bonferroni'] == 1 for p in pairs))

    def test_invalid_options_rejected(self):
        for alpha in (-1, 0, 1, np.nan, np.inf):
            with self.assertRaises(ValueError):
                rank_comparisons({}, alpha=alpha)
        with self.assertRaises(ValueError):
            rank_comparisons({}, min_group_size=4)


class FormalRunFamilies(unittest.TestCase):
    def test_three_metrics_and_ten_pairs_each(self):
        omnibus, pairs = run_statistics(artificial_runs())
        self.assertEqual(len(omnibus), 3)
        self.assertEqual(set(omnibus.posthoc), {'dunn_bonferroni'})
        self.assertEqual(len(pairs), 30)
        self.assertEqual(set(pairs.comparisons), {10})
        self.assertEqual(list(pairs.columns), PAIR_COLUMNS)

    def test_traffic_tiers_are_separate_families(self):
        omnibus, pairs = run_statistics(pd.concat([artificial_runs('low'), artificial_runs('high')]))
        self.assertEqual(len(omnibus), 6)
        self.assertEqual(len(pairs), 60)
        self.assertEqual(set(pairs.comparisons), {10})

    def test_absent_formal_configuration_blocks_formal_comparison(self):
        runs = artificial_runs()
        omnibus, pairs = run_statistics(runs[runs.config != 'full'])
        self.assertEqual(set(omnibus.status), {'insufficient_runs'})
        self.assertTrue(pairs.empty)

    def test_unknown_tier_or_insufficient_metric_does_not_produce_pvalues(self):
        omnibus, pairs = run_statistics(artificial_runs('unspecified'))
        self.assertEqual(set(omnibus.status), {'unrecognised_tier'})
        self.assertTrue(pairs.empty)
        runs = artificial_runs()
        runs.loc[runs.config == 'full', 'pqa'] = np.nan
        omnibus, pairs = run_statistics(runs)
        self.assertEqual(omnibus.set_index('metric').loc['pqa', 'status'], 'insufficient_runs')
        self.assertNotIn('pqa', set(pairs.metric))

    def test_duplicate_or_missing_run_identity_blocks_tests(self):
        runs = artificial_runs()
        for frame in (pd.concat([runs, runs.iloc[:1]]), runs.assign(session='')):
            omnibus, pairs = run_statistics(frame)
            self.assertTrue(set(omnibus.status) <= {'duplicate_run_identity', 'missing_run_identity'})
            self.assertTrue(pairs.empty)

    def test_nonformal_configuration_does_not_change_five_group_family(self):
        runs = artificial_runs()
        extra = runs.iloc[:10].assign(config='range-survey', pdr=999999)
        _, expected = run_statistics(runs)
        summary, actual = run_statistics(pd.concat([runs, extra]))
        pd.testing.assert_frame_equal(actual, expected)
        self.assertEqual(set(summary.excluded_configs), {'range-survey'})


if __name__ == '__main__':
    unittest.main()
