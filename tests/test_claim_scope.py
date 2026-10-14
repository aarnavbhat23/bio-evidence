import copy
import json
from pathlib import Path
import unittest
from bio_evidence.claim_scope import analyze

class TestTool(unittest.TestCase):
    def setUp(self):
        self.data=copy.deepcopy(json.loads((Path(__file__).resolve().parents[1]/'examples/claim_scope/input.json').read_text()))

    def test_fake_quote_is_guarded(self):
        r=analyze(self.data)
        self.assertEqual(r['ledger'][1]['guarded_label'],'abstain')
        self.assertAlmostEqual(r['guarded_coverage'],5/6)
    def test_real_quote_is_not_entailment(self):
        self.data['predictions'][1]['quote']='No animal experiments were performed.'
        r=analyze(self.data)['ledger'][1]
        self.assertTrue(r['quote_occurs'])
        self.assertNotEqual(r['guarded_label'],r['gold'])
    def test_missing_prediction_fails(self):
        self.data['predictions'].pop()
        with self.assertRaises(ValueError): analyze(self.data)
    def test_duplicate_prediction_fails(self):
        self.data['predictions'][0]['id']='c2'
        with self.assertRaises(ValueError): analyze(self.data)
    def test_perfect_labels_score_one(self):
        for c,p in zip(self.data['cases'],self.data['predictions']):
            p['label']=c['gold']; p['quote']=c['evidence']
        self.assertEqual(analyze(self.data)['quote_guarded_metrics']['macro_f1_fixed_three_labels'],1)

if __name__ == '__main__':
    unittest.main()
