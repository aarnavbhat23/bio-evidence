"""Run a small free instruction model on the same SciFact cases, retaining failures."""
import argparse
import json
from pathlib import Path
import torch
from transformers import AutoModelForCausalLM,AutoTokenizer
from bio_evidence.claim_scope import analyze,LABELS
from bio_evidence.ollama import SYSTEM

MODEL='HuggingFaceTB/SmolLM2-135M-Instruct'
REVISION='12fd25f77366fa6b3b4b768ec3050bf629380bac'

def parse_output(text,ident):
    try:
        result=json.loads(text.strip())
        if result.get('label') not in LABELS+('abstain',) or not isinstance(result.get('quote'),str):
            raise ValueError('Invalid response schema')
        return {'id':ident,'label':result['label'],'quote':result['quote']},True
    except (ValueError,AttributeError,TypeError):
        return {'id':ident,'label':'abstain','quote':''},False

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--device',choices=['cpu','cuda','mps'],default='cpu')
    args=p.parse_args()
    path=Path(__file__).resolve().parent/'claim_scope'
    data=json.loads((path/'input.json').read_text())
    tokenizer=AutoTokenizer.from_pretrained(MODEL,revision=REVISION)
    model=AutoModelForCausalLM.from_pretrained(MODEL,revision=REVISION).to(args.device).eval()
    if args.device=='cpu': torch.set_num_threads(4)
    predictions=[]; responses=[]
    with torch.inference_mode():
        for case in data['cases']:
            messages=[{'role':'system','content':SYSTEM},
                      {'role':'user','content':json.dumps({'claim':case['claim'],'evidence':case['evidence']})}]
            prompt=tokenizer.apply_chat_template(messages,tokenize=False,add_generation_prompt=True)
            tokens=tokenizer(prompt,return_tensors='pt',add_special_tokens=False)
            if tokens['input_ids'].shape[1]>1900:
                raise ValueError('Prompt exceeds fixed context budget; do not silently truncate evidence')
            tokens={k:v.to(args.device) for k,v in tokens.items()}
            generated=model.generate(**tokens,max_new_tokens=80,do_sample=False,pad_token_id=tokenizer.eos_token_id)
            output=tokenizer.decode(generated[0,tokens['input_ids'].shape[1]:],skip_special_tokens=True)
            prediction,valid=parse_output(output,case['id'])
            predictions.append(prediction)
            responses.append({'id':case['id'],'request':messages,'response':output,'valid_schema':valid,
                              'prompt_tokens':int(tokens['input_ids'].shape[1]),'generated_tokens':int(generated.shape[1]-tokens['input_ids'].shape[1])})
            (path/'lm_raw.json').write_text(json.dumps(responses,indent=2)+'\n')
    data['predictions']=predictions
    report=analyze(data)
    report['model']={'name':MODEL,'revision':REVISION,'device':args.device,'max_new_tokens':80,'do_sample':False}
    report['valid_schema_fraction']=sum(r['valid_schema'] for r in responses)/len(responses)
    report['study_note']='Actual greedy inference of a very small instruction model on the same 60 balanced SciFact development pairs. This is a failure-case baseline, not a competitive verifier. Invalid JSON/schema becomes abstention. Gold labels are absent from prompts; model pretraining contamination was not audited.'
    (path/'lm_input.json').write_text(json.dumps(data,indent=2)+'\n')
    (path/'lm_report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'metrics':report['raw_metrics'],'valid_schema_fraction':report['valid_schema_fraction'],'guarded_coverage':report['guarded_coverage']}),flush=True)

if __name__=='__main__': main()
