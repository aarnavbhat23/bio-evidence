"""Nine worked cases from public data; downloads are cached outside the package."""
import argparse
import csv
import gzip
import hashlib
import io
import json
import platform
import tarfile
import time
import tracemalloc
import urllib.request
from collections import Counter
from pathlib import Path
import numpy as np
from bio_evidence import assay_units, embedding_drift, structure_ensemble, perturbation_effects
from bio_evidence import batch_shortcuts, gene_aliases, dataset_contract, model_frontier
from bio_evidence.pdb import parse_ensemble

ROOT=Path(__file__).resolve().parent
SOURCES={
 'assays.tsv':'https://raw.githubusercontent.com/aarnavbhat23/spear-wetlab-false-positive-audit/5ac295c08f48aef43c991ba40a706f0e2fedb5b7/data/df_wetlab_heatmap_results.tsv',
 'hgnc.tsv':'https://storage.googleapis.com/public-download-files/hgnc/tsv/tsv/hgnc_complete_set.txt',
 'trpcage.pdb':'https://files.rcsb.org/download/1L2Y.pdb',
 'scifact.tar.gz':'https://scifact.s3-us-west-2.amazonaws.com/release/latest/data.tar.gz',
 'kang.h5ad':'https://drive.google.com/uc?export=download&id=1r87vhoLLq6PXAYdmyyd89zG90eJOFYLk',
 'atlas-embeddings.json':'https://raw.githubusercontent.com/aarnavbhat23/protein-neighbor-drift/9d0a4e955f2f7b4af2178dc229611f569fc1e2cf/results/esm-public-atlas/input.json'
}
for plate in ('BR00116991','BR00116992'):
 SOURCES[plate+'.csv.gz']=f'https://media.githubusercontent.com/media/jump-cellpainting/2024_Chandrasekaran_NatureMethods_CPJUMP1/56845c7d4dc322652952783d91dae0ffef47829f/profiles/2020_11_04_CPJUMP1/{plate}/{plate}_normalized_feature_select_negcon_batch.csv.gz'

def acquire(cache):
    records={}
    pins=json.loads((ROOT/'sources.json').read_text()) if (ROOT/'sources.json').exists() else {}
    cache.mkdir(parents=True,exist_ok=True)
    for name,url in SOURCES.items():
        path=cache/name
        if not path.exists(): path.write_bytes(urllib.request.urlopen(url,timeout=60).read())
        raw=path.read_bytes(); sha=hashlib.sha256(raw).hexdigest()
        if name in pins and sha != pins[name]['sha256']:
            raise ValueError('Source changed; explicit snapshot update required: '+name)
        records[name]={'url':url,'sha256':sha,'bytes':len(raw)}
    return records

def write_case(name,data,analyzer,source_files,note):
    path=ROOT/name; path.mkdir(parents=True,exist_ok=True)
    data['data_kind']='real public data; transformed by the documented case recipe'
    data['study_note']=note
    report=analyzer(data)
    report['study_note']=note
    report['source_files']=source_files
    for filename,obj in [('input.json',data),('report.json',report)]:
        (path/filename).write_text(json.dumps(obj,indent=2,allow_nan=False)+'\n')
    print(name+' completed',flush=True)
    return report

def units_case(cache):
    raw=list(csv.DictReader((cache/'assays.tsv').open(),delimiter='\t'))
    rows=[]
    for i,r in enumerate(raw,1):
        parsed=assay_units.parse_measurement(r['mic'])
        rows.append({'id':f'assay-{i}','sequence':r['sequence'],'chemistry':'unknown',
                     'source':r['paper_doi'],'organism':'not independently parsed',
                     'condition':r['wetlab_experiment'],
                     'value':(parsed['operator']+str(parsed['value'])) if parsed else r['mic'],
                     'unit':parsed['unit'] if parsed else 'unparsed','raw_mic':r['mic']})
    return write_case('assay_units',{'rows':rows},assay_units.analyze,['assays.tsv'],
                      'Broader extracted assay matrix, not a independently revalidated gold dataset. Chemistry/molecular weight are unavailable: molar-to-mass conversion is deliberately unresolved. Repeated keys are review candidates, not invalid records.')

def alias_case(cache):
    records=list(csv.DictReader((cache/'hgnc.tsv').open(),delimiter='\t'))
    genes=[]
    for r in records:
        if r['status'] != 'Approved': continue
        aliases=[]
        for column in ('alias_symbol','prev_symbol'):
            aliases.extend(a for a in r[column].strip('"').split('|') if a)
        genes.append({'id':r['hgnc_id'],'species':'human','symbol':r['symbol'],'aliases':sorted(set(aliases))})
    index=gene_aliases.build_index(genes)
    collisions=sorted(a for (species,a),ids in index.items() if len(ids)>1)
    # No contextual gold labels are invented. These are dictionary collision queries.
    queries=[{'id':f'collision-{i}','mention':a,'species':'human'} for i,a in enumerate(collisions[:25],1)]
    return write_case('gene_aliases',{'genes':genes,'queries':queries,'dictionary_version':'HGNC snapshot; SHA-256 in sources.json'},gene_aliases.analyze,['hgnc.tsv'],
                      'Official HGNC approved records, including aliases and previous symbols. The first 25 sorted collision keys exercise abstention. No context-resolved human gold IDs are supplied; accuracy is undefined. HGNC data are CC0.')

def structures_case(cache):
    text=(cache/'trpcage.pdb').read_text()
    models=parse_ensemble(text,'1L2Y')
    return write_case('structure_ensemble',{'models':models},structure_ensemble.analyze,['trpcage.pdb'],
                      'Experimental NMR ensemble for PDB 1L2Y (doi:10.2210/pdb1L2Y/pdb). This checks real coordinate correspondence and rigid alignment; it is not a prediction-seed benchmark or a thermodynamic flexibility estimate.')

def drift_case(cache):
    data=json.loads((cache/'atlas-embeddings.json').read_text())
    return write_case('embedding_drift',data,embedding_drift.analyze,['atlas-embeddings.json'],
                      'Actual pinned ESM-2 8M embeddings versus amino-acid frequency vectors on 100 selected public candidates. Neighborhood change is not activity prediction or representation superiority.')

def perturbation_case(cache):
    import anndata
    adata=anndata.read_h5ad(cache/'kang.h5ad')
    cell_types=sorted(set(adata.obs['cell_type']))
    genes=sorted(str(g) for g in adata.var_names)[:200]
    positions=[adata.var_names.get_loc(g) for g in genes]
    effects={}; counts={}
    for context in cell_types:
        means={}
        for condition in ('control','stimulated'):
            mask=((adata.obs['cell_type']==context)&(adata.obs['condition']==condition)).to_numpy()
            counts[context+':'+condition]=int(mask.sum())
            if not mask.any(): break
            means[condition]=np.asarray(adata.X[mask][:,positions].mean(0)).ravel()
        if len(means)==2: effects[context]=means['stimulated']-means['control']
    if len(effects)<2: raise ValueError('Need at least two observed contexts')
    rows=[]
    for context,observed in effects.items():
        prediction=np.mean([v for k,v in effects.items() if k!=context],axis=0)
        for gene,true,pred in zip(genes,observed,prediction):
            rows.append({'id':context+':'+gene,'context':context,'gene':gene,'perturbation':'IFN-beta',
                         'observed_effect':float(true),'predicted_effect':float(pred)})
    return write_case('perturbation_effects',{'rows':rows,'effect_threshold':.1,
                      'effect_units':'difference in means of source preprocessed log-expression','cell_counts':counts},
                      perturbation_effects.analyze,['kang.h5ad'],
                      'scGen Kang tutorial data. Predict each held-out cell type with mean treatment deltas from the other cell types; first 200 alphabetical genes, fixed before effect inspection. No donor labels are present: this is cell-type holdout, not donor holdout. Source preprocessing and cell independence are not revalidated; no inference about clinical response.')

def morphology_case(cache):
    plates=[]
    for name in ('BR00116991','BR00116992'):
        plates.append(list(csv.DictReader(io.StringIO(gzip.decompress((cache/(name+'.csv.gz')).read_bytes()).decode()))))
    features=sorted(k for k in set(plates[0][0])&set(plates[1][0]) if k.startswith(('Cells_','Cytoplasm_','Nuclei_')))[:128]
    rows=[]; excluded=0
    for records in plates:
        for r in records:
            if r['Metadata_pert_type'] != 'trt' or not r['Metadata_broad_sample']:
                excluded+=1; continue
            try: vector=[float(r[f]) for f in features]
            except ValueError: excluded+=1; continue
            if not np.isfinite(vector).all() or not np.linalg.norm(vector): excluded+=1; continue
            rows.append({'id':r['Metadata_Plate']+':'+r['Metadata_Well'],
                         'batch':r['Metadata_Plate'],'perturbation':r['Metadata_broad_sample'],'features':vector})
    return write_case('batch_shortcuts',{'rows':rows,'features':features,'excluded_wells':excluded},batch_shortcuts.analyze,
                      ['BR00116991.csv.gz','BR00116992.csv.gz'],
                      'JUMP pilot processed CellProfiler profiles from two plates. The batch field is plate identity, not distinct experimental batches. First 128 shared alphabetical features; controls and nonfinite wells excluded. Published preprocessing may use controls across the source batch. Held-out-compound plate classification is a diagnostic, not proof of biological artifacts.')

def contract_case(cache):
    assays=list(csv.DictReader((cache/'assays.tsv').open(),delimiter='\t'))
    rows=[{'id':f'assay-{i}','sequence':r['sequence'],'paper':r['paper_doi'],'mic':r['mic'],
           'split':'test' if i%5==0 else 'train'} for i,r in enumerate(assays,1)]
    contract={'source_uri':SOURCES['assays.tsv'],'license':'source repository MIT; underlying publications retain their rights',
              'version':'5ac295c08f48aef43c991ba40a706f0e2fedb5b7','citation':'SPEAR public assay extraction table',
              'sha256':dataset_contract.content_hash(rows),'required_columns':['sequence','paper','mic'],
              'id_column':'id','split_column':'split','group_columns':['sequence','paper']}
    return write_case('dataset_contract',{'rows':rows,'contract':contract},dataset_contract.analyze,['assays.tsv'],
                      'A deliberately unsafe deterministic row split applied to REAL data, to test that the checker rejects cross-split sequences and papers. It is not an actual upstream published training split. Missing MICs also fail the declared contract. Failure is expected and useful; no upstream defect is alleged.')

def frontier_case(cache):
    original=json.loads((cache/'atlas-embeddings.json').read_text())
    vectors=np.asarray([r['candidate'] for r in original['rows']],dtype=np.float32)
    baseline=embedding_drift.neighbors(vectors,10)
    configurations={'float32':vectors,'float16_roundtrip':vectors.astype(np.float16).astype(np.float32)}
    scale=np.maximum(np.abs(vectors).max(axis=1,keepdims=True),1e-8)/127
    configurations['per_vector_int8_roundtrip']=(np.rint(vectors/scale).clip(-127,127).astype(np.int8)*scale).astype(np.float32)
    runs=[]
    for name,x in configurations.items():
        embedding_drift.neighbors(x,10) # warmup excluded
        times=[]; peaks=[]
        for _ in range(25):
            tracemalloc.start(); start=time.perf_counter_ns()
            n=embedding_drift.neighbors(x,10)
            times.append((time.perf_counter_ns()-start)/1e6)
            peaks.append(tracemalloc.get_traced_memory()[1]); tracemalloc.stop()
        fidelity=float(np.mean([len(set(a)&set(b))/10 for a,b in zip(baseline,n)]))
        runs.append({'id':name,'task':'top10 neighbor fidelity after embedding quantization',
                     'dataset_sha256':hashlib.sha256(vectors.tobytes()).hexdigest(),
                     'hardware':platform.system()+' '+platform.machine(),
                     'measurement_protocol':'100x320 float32 cosine retrieval after storage roundtrip; warmup excluded; 25 serial calls; tracemalloc peak excludes model weights and nontraced native memory',
                     'metric':'mean top10 neighbor overlap with float32 reference (higher better)',
                     'quality':fidelity,'latencies_ms':times,'peak_memory_mb':max(peaks)/1e6,'cost_usd':0})
    return write_case('model_frontier',{'runs':runs},model_frontier.analyze,['atlas-embeddings.json'],
                      'Actual local measurements of saved embedding retrieval, not ESM inference cost. Quality is neighbor fidelity, not biological accuracy; memory is traced allocation peak, not GPU/process RSS. Tiny timing gaps are noisy and no statistical winner is claimed.')

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--cache',type=Path,default=Path('local-data'))
    args=p.parse_args()
    sources=acquire(args.cache)
    (ROOT/'sources.json').write_text(json.dumps(sources,indent=2)+'\n')
    for case in (units_case,alias_case,structures_case,drift_case,perturbation_case,morphology_case,contract_case,frontier_case):
        case(args.cache)
    print('Eight data cases complete; run_claims.py performs the ninth, with real language-model inference.',flush=True)

if __name__=='__main__': main()
