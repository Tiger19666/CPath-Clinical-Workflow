from __future__ import annotations
import argparse, json
from pathlib import Path
import numpy as np
import pandas as pd
import yaml
from sklearn.metrics import roc_auc_score, average_precision_score, balanced_accuracy_score


def _read(path):
    p=Path(path); return pd.read_csv(p,sep='\t' if p.suffix.lower() in {'.tsv','.txt'} else ',')

def _metrics(g, prob_col):
    y=g['label_id'].to_numpy(int); p=g[prob_col].to_numpy(float); pred=(p>=0.5).astype(int)
    out={'n':int(len(g)),'class_counts':{str(k):int(v) for k,v in g['label_id'].value_counts().sort_index().items()}}
    if len(np.unique(y))<2:
        out['status']='SINGLE_CLASS'; return out
    out.update({'status':'OK','auroc':float(roc_auc_score(y,p)),'auprc':float(average_precision_score(y,p)),
                'balanced_accuracy':float(balanced_accuracy_score(y,pred))})
    return out

def build(predictions, clinical_table, patient_id_col, subgroup_cols, model='concat_fusion', split='test', min_group_n=20):
    pred=pd.read_csv(predictions); clin=_read(clinical_table); clin=clin.copy(); clin[patient_id_col]=clin[patient_id_col].astype(str)
    p=pred[pred['split'].astype(str)==str(split)].copy(); p['patient_id']=p['patient_id'].astype(str)
    prob_col=f'{model}_prob_1'
    if prob_col not in p.columns: raise ValueError(f'missing model probability: {prob_col}')
    cols=[c for c in subgroup_cols if c in clin.columns]
    m=p.merge(clin[[patient_id_col]+cols],left_on='patient_id',right_on=patient_id_col,how='left',validate='one_to_one')
    reports={}
    for c in cols:
        groups={}
        for val,g in m.groupby(c,dropna=False):
            key='<MISSING>' if pd.isna(val) else str(val)
            base={'n':int(len(g)),'eligible_for_metric':int(len(g))>=int(min_group_n)}
            if len(g)<int(min_group_n):
                base['status']='INSUFFICIENT_GROUP_SIZE'
                base['class_counts']={str(k):int(v) for k,v in g['label_id'].value_counts().sort_index().items()}
            else: base.update(_metrics(g,prob_col))
            groups[key]=base
        reports[c]={'groups':groups,'missing_fraction':float(m[c].isna().mean())}
    return {
        'status':'PASS','split':split,'model':model,'n_patients':int(len(m)),'min_group_n':int(min_group_n),
        'subgroups':reports,
        'interpretation_guard':'Subgroups below the minimum support are descriptive only; smoke-sized groups must not be interpreted as robustness evidence.'
    }

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--predictions',required=True); ap.add_argument('--clinical-table',required=True); ap.add_argument('--patient-id-col',required=True)
    ap.add_argument('--subgroups',nargs='+',required=True); ap.add_argument('--model',default='concat_fusion'); ap.add_argument('--split',default='test'); ap.add_argument('--min-group-n',type=int,default=20); ap.add_argument('-o','--output',required=True)
    a=ap.parse_args(); out=build(a.predictions,a.clinical_table,a.patient_id_col,a.subgroups,a.model,a.split,a.min_group_n)
    p=Path(a.output); p.parent.mkdir(parents=True,exist_ok=True)
    if p.suffix.lower()=='.json': p.write_text(json.dumps(out,indent=2),encoding='utf-8')
    else: p.write_text(yaml.safe_dump(out,sort_keys=False,allow_unicode=True),encoding='utf-8')
if __name__=='__main__': main()
