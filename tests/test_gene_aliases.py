import copy
import json
from pathlib import Path
import unittest
from bio_evidence.gene_aliases import analyze

class TestTool(unittest.TestCase):
    def setUp(self):
        self.data=copy.deepcopy(json.loads((Path(__file__).resolve().parents[1]/'examples/gene_aliases/input.json').read_text()))

    def test_ambiguity_abstains(self):
        r=analyze(self.data)['queries'][0]
        self.assertEqual(r['status'],'ambiguous')
        self.assertIsNone(r['prediction'])
    def test_species_resolves_collision(self):
        self.assertEqual(analyze(self.data)['queries'][1]['prediction'],'toy-mouse-1')
    def test_casefold(self):
        self.data['queries'][2]['mention']='toy1'
        self.assertEqual(analyze(self.data)['queries'][2]['prediction'],'toy-human-1')
    def test_coverage_and_selective_accuracy(self):
        r=analyze(self.data)
        self.assertEqual(r['coverage'],.5)
        self.assertEqual(r['selective_accuracy'],1)
    def test_unlabeled_does_not_inflate_accuracy(self):
        for q in self.data['queries']: del q['gold_id']
        self.assertIsNone(analyze(self.data)['selective_accuracy'])
    def test_alias_string_is_not_a_list(self):
        self.data['genes'][0]['aliases']='Shared'
        with self.assertRaises(ValueError): analyze(self.data)

if __name__ == '__main__':
    unittest.main()
