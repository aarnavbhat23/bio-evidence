"""Offline regressions on the actual worked cases, including abstention/eligibility."""
import importlib
import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]/'studies'

class PublicCaseTests(unittest.TestCase):
    def read(self,name): return json.loads((ROOT/name/'input.json').read_text())
    def test_all_nine_public_cases_execute(self):
        names=['assay_units','embedding_drift','structure_ensemble','perturbation_effects',
               'batch_shortcuts','gene_aliases','claim_scope','model_frontier','dataset_contract']
        for name in names:
            with self.subTest(module=name):
                module=importlib.import_module('bio_evidence.'+name)
                report=module.analyze(self.read(name))
                json.dumps(report,allow_nan=False)
    def test_real_nmr_ensemble_has_complete_correspondence(self):
        data=self.read('structure_ensemble')
        self.assertEqual(len(data['models']),38)
        for model in data['models']: self.assertEqual(len(model['residue_keys']),20)
    def test_real_gene_queries_do_not_invent_ground_truth(self):
        from bio_evidence.gene_aliases import analyze
        result=analyze(self.read('gene_aliases'))
        self.assertEqual(result['n_labeled'],0)
        self.assertIsNone(result['selective_accuracy'])
        self.assertTrue(all(q['prediction'] is None for q in result['queries']))
    def test_real_profile_queries_without_replicates_are_ineligible(self):
        from bio_evidence.batch_shortcuts import analyze
        result=analyze(self.read('batch_shortcuts'))
        self.assertIsNone(result['within_batch']['top1_hit_rate'])
        self.assertEqual(result['within_batch']['n_eligible'],0)
        self.assertGreater(result['cross_batch']['n_eligible'],0)
    def test_deliberate_row_split_is_rejected(self):
        from bio_evidence.dataset_contract import analyze
        result=analyze(self.read('dataset_contract'))
        self.assertFalse(result['passed'])
        self.assertTrue(any(i['type']=='cross_split_group' for i in result['issues']))
