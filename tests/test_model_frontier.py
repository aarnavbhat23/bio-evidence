import copy
import json
from pathlib import Path
import unittest
from bio_evidence.model_frontier import analyze

class TestTool(unittest.TestCase):
    def setUp(self):
        self.data=copy.deepcopy(json.loads((Path(__file__).resolve().parents[1]/'examples/model_frontier/input.json').read_text()))

    def test_dominated_point_removed(self):
        r=analyze(self.data)
        cpu=next(g for g in r['groups'] if g['comparison_contract']['hardware']=='toy-CPU')
        self.assertEqual(cpu['frontier_ids'],['baseline','small-encoder'])
    def test_hardware_never_combined(self):
        self.assertEqual(len(analyze(self.data)['groups']),2)
    def test_remove_limit_restores_large_model(self):
        self.data['limits']={}
        r=analyze(self.data)
        cpu=next(g for g in r['groups'] if g['comparison_contract']['hardware']=='toy-CPU')
        self.assertIn('large-encoder',cpu['frontier_ids'])
    def test_negative_resource_fails(self):
        self.data['runs'][0]['cost_usd']=-1
        with self.assertRaises(ValueError): analyze(self.data)
    def test_identical_points_remain(self):
        import copy
        r=copy.deepcopy(self.data['runs'][0]); r['id']='tied'
        self.data['runs'].append(r)
        self.assertTrue(any('tied' in g['frontier_ids'] for g in analyze(self.data)['groups']))

if __name__ == '__main__':
    unittest.main()
