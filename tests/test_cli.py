import json
from pathlib import Path
import tempfile
import unittest
from bio_evidence.cli import main

class CLITests(unittest.TestCase):
    def test_contract_failure_can_gate_a_pipeline(self):
        fixture = Path(__file__).resolve().parents[1]/'examples/dataset_contract/input.json'
        with tempfile.TemporaryDirectory() as directory:
            output=Path(directory)/'report.json'
            self.assertEqual(main(['dataset-contract',str(fixture),'--output',str(output),'--require-pass']),1)
            self.assertFalse(json.loads(output.read_text())['passed'])
    def test_output_records_input_hash(self):
        fixture=Path(__file__).resolve().parents[1]/'examples/assay_units/input.json'
        with tempfile.TemporaryDirectory() as directory:
            output=Path(directory)/'report.json'
            self.assertEqual(main(['assay-units',str(fixture),'--output',str(output)]),0)
            self.assertEqual(len(json.loads(output.read_text())['input_sha256']),64)
