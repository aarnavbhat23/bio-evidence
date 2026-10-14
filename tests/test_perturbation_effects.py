import copy
import json
from pathlib import Path
import unittest
from bio_evidence.perturbation_effects import analyze

class TestTool(unittest.TestCase):
    def setUp(self):
        self.data=copy.deepcopy(json.loads((Path(__file__).resolve().parents[1]/'examples/perturbation_effects/input.json').read_text()))

    def test_sign_and_zero_baseline(self):
        r=analyze(self.data)['pooled']
        self.assertAlmostEqual(r['sign_accuracy_on_observed_effects'],1/3)
        self.assertEqual(r['n_observed_above_threshold'],3)
        self.assertAlmostEqual(r['zero_effect_mae'],.6375)
    def test_perfect_predictions(self):
        for r in self.data['rows']: r['predicted_effect']=r['observed_effect']
        r=analyze(self.data)['pooled']
        self.assertEqual(r['mae'],0)
        self.assertEqual(r['mae_skill_vs_zero'],1)
    def test_zero_observations_do_not_divide_by_zero(self):
        for r in self.data['rows']: r['observed_effect']=0
        r=analyze(self.data)['pooled']
        self.assertIsNone(r['mae_skill_vs_zero'])
        self.assertIsNone(r['sign_accuracy_on_observed_effects'])
    def test_threshold_equality_is_neutral(self):
        self.data['rows'][0]['observed_effect']=.2
        self.assertEqual(analyze(self.data)['pooled']['n_observed_above_threshold'],2)
    def test_invalid_threshold(self):
        self.data['effect_threshold']=-1
        with self.assertRaises(ValueError): analyze(self.data)

if __name__ == '__main__':
    unittest.main()
