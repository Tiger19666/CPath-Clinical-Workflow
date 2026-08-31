from __future__ import annotations
import argparse, json, math
from pathlib import Path
import numpy as np
import pandas as pd
import yaml
from sklearn.metrics import accuracy_score, balanced_accuracy_score, f1_score, roc_auc_score, average_precision_score, confusion_matrix, brier_score_loss


def _binary_metrics(y, prob, threshold=0.5):
    y=np.asarray(y,dtype=int); prob=np.asarray(prob,dtype=float); pred=(prob>=threshold).astype(int)
    bins=np.linspace(0.0,1.0,11); ece=0.0
    for lo,hi in zip(bins[:-1],bins[1:]):
        mask=(prob>=lo)&((prob<hi) if hi<1.0 else (prob<=hi))
        if mask.any():
            ece += float(mask.mean()) * abs(float(y[mask].mean())-float(prob[mask].mean()))
    out={
        'n':int(len(y)),
        'accuracy':float(accuracy_score(y,pred)),
        'balanced_accuracy':float(balanced_accuracy_score(y,pred)),
        'macro_f1':float(f1_score(y,pred,average='macro',zero_division=0)),
        'brier_score':float(brier_score_loss(y,prob)),
        'ece_10bin':float(ece),
    }
    if len(np.unique(y))==2:
        out['auroc']=float(roc_auc_score(y,prob))
        out['auprc']=float(average_precision_score(y,prob))
        cm=confusion_matrix(y,pred,labels=[0,1])
        tn,fp,fn,tp=cm.ravel()
        out['sensitivity']=float(tp/(tp+fn)) if tp+fn else None
        out['specificity']=float(tn/(tn+fp)) if tn+fp else None
    return out


def _percentile(vals, alpha=0.05):
    arr=np.asarray([x for x in vals if x is not None and np.isfinite(x)],dtype=float)
    if len(arr)==0: return None
    return [float(np.quantile(arr,alpha/2)), float(np.quantile(arr,1-alpha/2))]


def _bootstrap(y, prob, reps=1000, seed=42):
    y=np.asarray(y); prob=np.asarray(prob); n=len(y); rng=np.random.default_rng(seed)
    samples={k:[] for k in ['auroc','auprc','balanced_accuracy','macro_f1','accuracy','sensitivity','specificity','brier_score','ece_10bin']}
    valid=0
    for _ in range(int(reps)):
        ii=rng.integers(0,n,size=n)
        if len(np.unique(y[ii]))<2:
            continue
        m=_binary_metrics(y[ii],prob[ii]); valid+=1
        for k in samples:
            v=m.get(k)
            if v is not None: samples[k].append(v)
    return {
        'requested_replicates':int(reps), 'valid_replicates':int(valid),
        'ci95':{k:_percentile(v) for k,v in samples.items() if v}
    }


def _paired_bootstrap(y, p1, p0, metrics, reps=1000, seed=43):
    y=np.asarray(y); p1=np.asarray(p1); p0=np.asarray(p0); n=len(y); rng=np.random.default_rng(seed)
    d={k:[] for k in metrics}; valid=0
    for _ in range(int(reps)):
        ii=rng.integers(0,n,size=n)
        if len(np.unique(y[ii]))<2: continue
        a=_binary_metrics(y[ii],p1[ii]); b=_binary_metrics(y[ii],p0[ii]); valid+=1
        for k in metrics:
            if a.get(k) is not None and b.get(k) is not None:
                d[k].append(a[k]-b[k])
    return {'requested_replicates':int(reps),'valid_replicates':valid,
            'delta_ci95':{k:_percentile(v) for k,v in d.items() if v},
            'delta_mean':{k:float(np.mean(v)) for k,v in d.items() if v}}


def infer_models(df):
    suffix='_prob_1'
    return sorted({c[:-len(suffix)] for c in df.columns if c.endswith(suffix)})


def evaluate(predictions, contract, split='test', bootstrap_reps=None, seed=42):
    df=pd.read_csv(predictions) if not isinstance(predictions,pd.DataFrame) else predictions.copy()
    con=yaml.safe_load(Path(contract).read_text()) if isinstance(contract,(str,Path)) else dict(contract)
    sdf=df[df['split'].astype(str)==str(split)].copy()
    models=infer_models(sdf)
    if len(sdf)==0: raise ValueError(f'no predictions for split={split}')
    reps=int(bootstrap_reps or con.get('metrics',{}).get('uncertainty',{}).get('default_replicates',1000))
    per_model={}
    for m in models:
        prob=sdf[f'{m}_prob_1'].to_numpy(float); y=sdf['label_id'].to_numpy(int)
        per_model[m]={'point':_binary_metrics(y,prob),'bootstrap':_bootstrap(y,prob,reps,seed)}
    primary=con.get('primary_model') or ('concat_fusion' if 'concat_fusion' in models else models[0])
    comps=[x for x in con.get('comparators',[]) if x in models]
    if not comps: comps=[m for m in models if m!=primary]
    metric_names=con.get('metrics',{}).get('paired_comparison',{}).get('metrics',[])
    comparisons={}
    if primary in models:
        for c in comps:
            comparisons[f'{primary}_vs_{c}']=_paired_bootstrap(
                sdf['label_id'].to_numpy(int), sdf[f'{primary}_prob_1'].to_numpy(float), sdf[f'{c}_prob_1'].to_numpy(float), metric_names,reps,seed+1)
    diagnostic=bool(con.get('diagnostic_only',False))
    status='DIAGNOSTIC_ONLY' if diagnostic else 'SCIENTIFIC_EVALUATION_READY'
    return {
        'status':status,'study_scope':con.get('study_scope'),'split':split,
        'n_patients':int(len(sdf)),'models':models,'primary_model':primary,
        'per_model':per_model,'paired_comparisons':comparisons,
        'interpretation_guard': 'Execution diagnostic only; do not make performance claims.' if diagnostic else 'Interpret with the prespecified clinical validation protocol.'
    }


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--predictions',required=True); ap.add_argument('--contract',required=True)
    ap.add_argument('--split',default='test'); ap.add_argument('--bootstrap-reps',type=int); ap.add_argument('--seed',type=int,default=42); ap.add_argument('-o','--output',required=True)
    a=ap.parse_args(); out=evaluate(a.predictions,a.contract,a.split,a.bootstrap_reps,a.seed)
    p=Path(a.output); p.parent.mkdir(parents=True,exist_ok=True)
    if p.suffix.lower()=='.json': p.write_text(json.dumps(out,indent=2),encoding='utf-8')
    else: p.write_text(yaml.safe_dump(out,sort_keys=False,allow_unicode=True),encoding='utf-8')
if __name__=='__main__': main()
