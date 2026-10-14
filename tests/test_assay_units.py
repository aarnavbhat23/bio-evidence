import copy
import json
from pathlib import Path
import unittest
from bio_evidence.assay_units import analyze

class TestTool(unittest.TestCase):
    def setUp(self):
        self.data=copy.deepcopy(json.loads((Path(__file__).resolve().parents[1]/'examples/assay_units/input.json').read_text()))

    def test_censoring_survives(self):
        r=analyze(self.data)['records'][0]
        self.assertEqual((r['status'],r['operator'],r['mg_per_L']),('censored','>',64))
    def test_molar_conversion(self):
        self.assertEqual(analyze(self.data)['records'][1]['mg_per_L'],16)
    def test_no_weight_means_review(self):
        del self.data['rows'][1]['molecular_weight_g_mol']
        self.assertEqual(analyze(self.data)['records'][1]['status'],'manual_review')
    def test_ranges_and_missing_are_not_exact(self):
        r=analyze(self.data)['records']
        self.assertEqual((r[2]['status'],r[3]['status']),('missing','manual_review'))
    def test_chemistry_separates_repeated_keys(self):
        self.assertEqual(analyze(self.data)['repeated_assay_keys'],[['a1','a2']])
    def test_unicode_micro(self):
        self.data['rows'][0]['unit']='μg/mL'
        self.assertEqual(analyze(self.data)['records'][0]['mg_per_L'],64)

if __name__ == '__main__':
    unittest.main()
