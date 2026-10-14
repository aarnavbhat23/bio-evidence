import json
import unittest
from unittest.mock import patch, MagicMock
from bio_evidence.ollama import infer

class LocalAdapterTests(unittest.TestCase):
    def simulate(self, content):
        case={'id':'a','claim':'Claim','evidence':'Exact quote.','gold':'contradicted'}
        handle=MagicMock()
        handle.__enter__.return_value.read.return_value=json.dumps({'message':{'content':content}}).encode()
        with patch('urllib.request.urlopen',return_value=handle):
            prediction,raw,payload=infer(case,'test-model','http://localhost:11434')
        return prediction,payload
    def test_gold_is_never_sent(self):
        prediction,payload=self.simulate('{"label":"supported","quote":"Exact quote."}')
        user=json.loads(payload['messages'][1]['content'])
        self.assertEqual(set(user),{'claim','evidence'})
        self.assertEqual(prediction['label'],'supported')
    def test_malformed_model_output_abstains(self):
        prediction,_=self.simulate('Not JSON')
        self.assertEqual(prediction,{'id':'a','label':'abstain','quote':''})
    def test_invalid_label_abstains(self):
        prediction,_=self.simulate('{"label":"definitely true","quote":"Exact quote."}')
        self.assertEqual(prediction['label'],'abstain')
