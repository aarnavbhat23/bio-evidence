import copy
import json
from pathlib import Path
import unittest
from bio_evidence.dataset_contract import analyze

class TestTool(unittest.TestCase):
    def setUp(self):
        self.data=copy.deepcopy(json.loads((Path(__file__).resolve().parents[1]/'examples/dataset_contract/input.json').read_text()))

    def test_family_overlap_detected(self):
        r=analyze(self.data)
        self.assertFalse(r['passed'])
        self.assertEqual(r['issues'][0]['type'],'cross_split_group')
    def test_correct_split_passes(self):
        from bio_evidence.dataset_contract import content_hash
        self.data['rows'][2]['split']='train'
        self.data['contract']['sha256']=content_hash(self.data['rows'])
        self.assertTrue(analyze(self.data)['passed'])
    def test_mutation_breaks_hash(self):
        self.data['rows'][0]['sequence']='AAAA'
        self.assertTrue(any(i['type']=='hash_mismatch' for i in analyze(self.data)['issues']))
    def test_groups_enforced_independently(self):
        from bio_evidence.dataset_contract import content_hash
        self.data['rows'][2]['family']='new-family'
        self.data['rows'][2]['paper']='paper-A'
        self.data['contract']['sha256']=content_hash(self.data['rows'])
        r=analyze(self.data)
        self.assertEqual(r['issues'][0]['column'],'paper')
    def test_duplicate_ids_fail(self):
        self.data['rows'][1]['id']='r1'
        self.assertTrue(any(i['type']=='duplicate_id' for i in analyze(self.data)['issues']))

if __name__ == '__main__':
    unittest.main()
