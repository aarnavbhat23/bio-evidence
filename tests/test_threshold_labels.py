import unittest
from bio_evidence.assay_units import parse_measurement, threshold_label

class ThresholdTests(unittest.TestCase):
    def test_censoring_decides_only_one_side(self):
        self.assertEqual(threshold_label('>64 µM'),0)
        self.assertIsNone(threshold_label('>8 µM'))
        self.assertEqual(threshold_label('<8 µM'),1)
        self.assertIsNone(threshold_label('<64 µM'))
    def test_open_closed_boundary(self):
        self.assertEqual(threshold_label('>16 uM'),0)
        self.assertIsNone(threshold_label('>=16 uM'))
        self.assertEqual(threshold_label('<=16 uM'),1)
        self.assertEqual(threshold_label('16 uM'),1)
    def test_molar_unit_conversion(self):
        self.assertEqual(threshold_label('16000 nM'),1)
        self.assertEqual(threshold_label('0.02 mM'),0)
    def test_mass_molar_comparison_is_undefined(self):
        self.assertIsNone(threshold_label('8 ug/mL'))
        self.assertEqual(threshold_label('8 mg/L',unit='ug/mL'),1)
    def test_unicode_inequality(self):
        self.assertEqual(threshold_label('≥32 μM'),0)
    def test_no_parse_of_ranges(self):
        self.assertIsNone(parse_measurement('8-16 uM'))
        self.assertIsNone(threshold_label('ND'))
