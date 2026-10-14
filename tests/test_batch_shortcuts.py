import copy
import json
from pathlib import Path
import unittest
from bio_evidence.batch_shortcuts import analyze

class TestTool(unittest.TestCase):
    def setUp(self):
        self.data=copy.deepcopy(json.loads((Path(__file__).resolve().parents[1]/'examples/batch_shortcuts/input.json').read_text()))

    def test_retrieval_and_classifier(self):
        r=analyze(self.data)
        self.assertEqual(r['within_batch']['top1_hit_rate'],1)
        self.assertEqual(r['cross_batch']['top1_hit_rate'],1)
        self.assertEqual(r['batch_classifier']['accuracy'],1)
    def test_classifier_groups_never_overlap(self):
        for fold in analyze(self.data)['batch_classifier']['folds']:
            self.assertFalse(set(fold['train_perturbations']) & set(fold['test_perturbations']))
    def test_single_batch_has_no_cross_batch_queries(self):
        for row in self.data['rows']: row['batch']='A'
        r=analyze(self.data)
        self.assertEqual(r['cross_batch']['n_eligible'],0)
        self.assertIsNone(r['batch_classifier']['accuracy'])
    def test_zero_vector_fails(self):
        self.data['rows'][0]['features']=[0]*6
        with self.assertRaises(ValueError): analyze(self.data)
    def test_confounded_design_warns(self):
        for r in self.data['rows']: r['batch']=r['perturbation']
        self.assertTrue(analyze(self.data)['warnings'])
    def test_empty_batch_label_fails(self):
        self.data['rows'][0]['batch']=''
        with self.assertRaises(ValueError): analyze(self.data)

if __name__ == '__main__':
    unittest.main()
