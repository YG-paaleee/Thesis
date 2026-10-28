"""Exercise the actual validation-threshold selector without ML installation."""
import ast
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

source = Path(__file__).resolve().parents[1] / 'train_cart.py'
parsed = ast.parse(source.read_text(encoding='utf-8'))
function = next(item for item in parsed.body if isinstance(item, ast.FunctionDef) and item.name == 'select_threshold')
namespace = {'np': np}
exec(compile(ast.Module(body=[function], type_ignores=[]), str(source), 'exec'), namespace)
select_threshold = namespace['select_threshold']


class ThresholdSelection(unittest.TestCase):
    def test_higher_recall_wins_equal_f1_even_farther_from_half(self):
        rows = pd.DataFrame(dict(threshold=[0.5, 0.7], f1=[0.8, 0.8], recall=[0.6, 0.9]))
        self.assertEqual(select_threshold(rows), 0.7)

    def test_f1_remains_primary(self):
        rows = pd.DataFrame(dict(threshold=[0.5, 0.7], f1=[0.9, 0.8], recall=[0.6, 0.9]))
        self.assertEqual(select_threshold(rows), 0.5)

    def test_equal_scores_use_stable_tertiary_rule(self):
        rows = pd.DataFrame(dict(threshold=[0.75, 0.25], f1=[0.8, 0.8], recall=[0.9, 0.9]))
        self.assertEqual(select_threshold(rows), 0.25)
        self.assertEqual(select_threshold(rows.iloc[::-1]), 0.25)

    def test_nearest_half_only_after_both_scores_tie(self):
        rows = pd.DataFrame(dict(threshold=[0.75, 0.5], f1=[0.8, 0.8], recall=[0.9, 0.9]))
        self.assertEqual(select_threshold(rows), 0.5)

    def test_empty_or_nonfinite_validation_is_rejected(self):
        with self.assertRaises(ValueError):
            select_threshold(pd.DataFrame())
        with self.assertRaises(ValueError):
            select_threshold(pd.DataFrame(dict(threshold=[0.5], f1=[np.nan], recall=[0.9])))


if __name__ == '__main__':
    unittest.main()
