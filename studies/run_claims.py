"""Evaluate a frozen NLI baseline on real SciFact development claim/evidence pairs."""
import argparse
import json
import tarfile
from pathlib import Path
import numpy as np
import torch
from transformers import AutoModelForSequenceClassification,AutoTokenizer
from bio_evidence.claim_scope import analyze

MODEL='cross-encoder/nli-MiniLM2-L6-H768'
REVISION='b95119ce93d3e065de6214e38cd4a97b0f2f2c6d'
LABELS=['contradicted','supported','insufficient'] # official model-card ordering

def prepare(path):
    with tarfile.open(path) as archive:
        corpus={r['doc_id']:r for r in map(json.loads,archive.extractfile('data/corpus.jsonl'))}
        claims=list(map(json.loads,archive.extractfile('data/claims_dev.jsonl')))
    cases=[]
    for claim in sorted(claims,key=lambda c:c['id']):
        if claim['evidence']:
            doc_id=sorted(claim['evidence'],key=int)[0]
            evidence=claim['evidence'][doc_id]
            labels={e['label'] for e in evidence}
            if len(labels)!=1: continue
            gold='supported' if next(iter(labels))=='SUPPORT' else 'contradicted'
            doc=corpus[int(doc_id)]
        elif claim['cited_doc_ids']:
            doc=corpus[claim['cited_doc_ids'][0]]; gold='insufficient'
        else: continue
        cases.append({'id':str(claim['id']),'claim':claim['claim'],'evidence':' '.join(doc['abstract']),
                      'source_id':str(doc['doc_id']),'scope':'scifact_provided_abstract','gold':gold})
    # Deterministic balanced subset; development diagnostics, not a hidden test leaderboard.
    return [c for label in ('supported','contradicted','insufficient') for c in [r for r in cases if r['gold']==label][:20]]

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--cache',type=Path,default=Path('local-data'))
    p.add_argument('--device',choices=['cpu','cuda','mps'],default='cpu')
    args=p.parse_args()
    cases=prepare(args.cache/'scifact.tar.gz')
    if args.device=='cpu': torch.set_num_threads(4)
    model=AutoModelForSequenceClassification.from_pretrained(MODEL,revision=REVISION).to(args.device).eval()
    tokenizer=AutoTokenizer.from_pretrained(MODEL,revision=REVISION)
    predictions=[]; raw=[]
    with torch.inference_mode():
        for c in cases:
            tokens=tokenizer(c['evidence'],c['claim'],truncation='only_first',max_length=512,return_tensors='pt')
            tokens={k:v.to(args.device) for k,v in tokens.items()}
            probs=torch.softmax(model(**tokens).logits,dim=-1)[0].cpu().numpy()
            prediction=LABELS[int(probs.argmax())]
            # Provenance quote is mechanically selected, not generated or asserted as rationale.
            quote=c['evidence'].split('. ')[0][:160]
            predictions.append({'id':c['id'],'label':prediction,'quote':quote})
            raw.append({'id':c['id'],'scores':{label:float(value) for label,value in zip(LABELS,probs)}})
    data={'data_kind':'real SciFact expert-annotated development pairs; pretrained NLI baseline',
          'cases':cases,'predictions':predictions}
    report=analyze(data)
    report['study_note']='60 balanced development claim/abstract pairs; no fine-tuning, retrieval benchmark or new scope annotations. Neutral uses SciFact cases without labeled evidence and their first cited abstract. Full-abstract NLI is truncated to 512 tokens. Mechanically selected quotes validate occurrence only, not supporting rationale.'
    report['model']={'name':MODEL,'revision':REVISION,'device':args.device,'label_order':LABELS,
                     'torch':torch.__version__,'task':'General-domain pretrained NLI transferred without fitting to SciFact development data'}
    path=Path(__file__).resolve().parent/'claim_scope'; path.mkdir(exist_ok=True)
    for filename,obj in [('input.json',data),('report.json',report),('raw_scores.json',raw)]:
        (path/filename).write_text(json.dumps(obj,indent=2)+'\n')
    print(json.dumps(report['raw_metrics']),flush=True)

if __name__=='__main__': main()
