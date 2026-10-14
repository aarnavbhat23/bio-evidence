import unittest
from bio_evidence.pdb import parse_pdb,parse_ensemble

def atom(i,altloc='',x=0):
    return f'ATOM  {i:5d}  CA {altloc or " "}ALA A{i:4d}    {x:8.3f}{0.:8.3f}{0.:8.3f}  1.00 80.00           C'

class PdbTests(unittest.TestCase):
    def test_alternate_locations_are_selected_once(self):
        text='\n'.join([atom(1,'B',2),atom(1,'A',1),atom(2),atom(3)])
        out=parse_pdb(text,'model')
        self.assertEqual(out['coordinates'][0],[1.,0.,0.])
        self.assertEqual(len(out['residue_keys']),3)
    def test_first_model_only(self):
        text='\n'.join([atom(1),atom(2),atom(3),'ENDMDL',atom(4)])
        self.assertEqual(len(parse_pdb(text,'model')['coordinates']),3)
    def test_duplicate_atom_is_rejected(self):
        text='\n'.join([atom(1),atom(1),atom(2),atom(3)])
        with self.assertRaises(ValueError): parse_pdb(text,'model')
    def test_remark_does_not_split_an_ensemble(self):
        lines=['REMARK 210 ONE MODEL WAS SELECTED','MODEL        1',atom(1),atom(2),atom(3),'ENDMDL',
               'MODEL        2',atom(1),atom(2),atom(3),'ENDMDL']
        self.assertEqual(len(parse_ensemble('\n'.join(lines),'ensemble')),2)
    def test_unterminated_model_fails(self):
        with self.assertRaises(ValueError): parse_ensemble('MODEL        1\n'+atom(1),'ensemble')
