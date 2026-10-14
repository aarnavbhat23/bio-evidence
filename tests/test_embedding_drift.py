import copy
import json
from pathlib import Path
import unittest
from bio_evidence.embedding_drift import analyze

class TestTool(unittest.TestCase):
    def setUp(self):
        self.data=copy.deepcopy(json.loads((Path(__file__).resolve().parents[1]/'examples/embedding_drift/input.json').read_text()))

    def test_changed_neighbors(self):
        r=analyze(self.data)
        self.assertEqual(r['mean_neighbor_overlap'],0)
        self.assertEqual(r['records'][0]['reference_neighbors'],['p2'])
    def test_identical_representation(self):
        for r in self.data['rows']: r['candidate']=r['reference']
        self.assertEqual(analyze(self.data)['mean_neighbor_overlap'],1)
    def test_zero_vector_rejected(self):
        self.data['rows'][0]['reference']=[0,0,0]
        with self.assertRaises(ValueError): analyze(self.data)
    def test_invalid_k(self):
        self.data['k']=len(self.data['rows'])
        with self.assertRaises(ValueError): analyze(self.data)
    def test_self_is_excluded(self):
        for r in analyze(self.data)['records']:
            self.assertNotIn(r['id'],r['reference_neighbors'])

if __name__ == '__main__':
    unittest.main()
