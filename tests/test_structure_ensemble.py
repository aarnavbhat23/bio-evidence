import copy
import json
from pathlib import Path
import unittest
from bio_evidence.structure_ensemble import analyze

class TestTool(unittest.TestCase):
    def setUp(self):
        self.data=copy.deepcopy(json.loads((Path(__file__).resolve().parents[1]/'examples/structure_ensemble/input.json').read_text()))

    def test_rigid_transform_invariance(self):
        result=analyze(self.data)
        self.assertLess(result['pairs'][0]['ca_rmsd_angstrom'],1e-10)
        self.assertGreater(result['pairs'][1]['ca_rmsd_angstrom'],.1)
    def test_residue_mismatch_fails(self):
        self.data['models'][1]['residue_keys'][0]='B:1:'
        with self.assertRaises(ValueError): analyze(self.data)
    def test_sequence_mismatch_fails(self):
        self.data['models'][1]['residue_names'][0]='TRP'
        with self.assertRaises(ValueError): analyze(self.data)
    def test_reflection_is_not_allowed(self):
        from bio_evidence.structure_ensemble import superpose
        import numpy as np
        x=np.array(self.data['models'][0]['coordinates'])
        _,d=superpose(x,x*[-1,1,1])
        self.assertGreater(float(np.mean(d)),.1)
    def test_nonfinite_fails(self):
        self.data['models'][0]['coordinates'][0][0]=float('nan')
        with self.assertRaises(ValueError): analyze(self.data)

if __name__ == '__main__':
    unittest.main()
