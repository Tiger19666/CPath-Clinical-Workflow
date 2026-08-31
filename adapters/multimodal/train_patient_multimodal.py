from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
import h5py
import numpy as np
import pandas as pd
import yaml
from scipy import sparse
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, balanced_accuracy_score, f1_score, roc_auc_score, average_precision_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


def _read_table(path):
    p=Path(path); sep='\t' if p.suffix.lower() in {'.tsv','.txt'} else ','
    return pd.read_csv(p,sep=sep)

def _hash_ids(ids):
    s='\n'.join(sorted(map(str,ids))).encode()
    return hashlib.sha256(s).hexdigest()

def _slide_vector(fp):
    with h5py.File(fp,'r') as f:
        x=np.asarray(f['features'],dtype=np.float32)
    if x.ndim!=2 or x.shape[0]==0: raise ValueError(f'invalid feature bag: {fp}')
    return x.mean(axis=0)

def build_patient_pathology_vectors(cohort, feature_root):
    root=Path(feature_root); rows=[]
    for pid,g in cohort.groupby('patient_id'):
        labels=g['label_id'].unique()
        if len(labels)!=1: raise ValueError(f'conflicting labels for {pid}')
        vs=[]
        for sid in g['slide_id'].astype(str):
            fp=root/f'{sid}.h5'
            if not fp.exists(): raise FileNotFoundError(str(fp))
            vs.append(_slide_vector(fp))
        pv=np.stack(vs).mean(axis=0)
        rows.append((str(pid),int(labels[0]),str(g['split'].iloc[0]),pv,len(vs)))
    return rows

def _metrics(y, prob):
    y=np.asarray(y); prob=np.asarray(prob); pred=np.argmax(prob,axis=1)
    out={
        'accuracy':float(accuracy_score(y,pred)),
        'balanced_accuracy':float(balanced_accuracy_score(y,pred)),
        'macro_f1':float(f1_score(y,pred,average='macro')),
        'n':int(len(y)),
    }
    try:
        if prob.shape[1]==2:
            out['auroc']=float(roc_auc_score(y,prob[:,1]))
            out['auprc']=float(average_precision_score(y,prob[:,1]))
        else:
            out['auroc_macro_ovr']=float(roc_auc_score(y,prob,multi_class='ovr',average='macro'))
    except ValueError:
        pass
    return out

def _clinical_preprocessor(df, numeric, categorical):
    tr=[]
    if numeric:
        tr.append(('num',Pipeline([('imputer',SimpleImputer(strategy='median')),('scaler',StandardScaler())]),numeric))
    if categorical:
        tr.append(('cat',Pipeline([('imputer',SimpleImputer(strategy='most_frequent')),('ohe',OneHotEncoder(handle_unknown='ignore'))]),categorical))
    if not tr: raise ValueError('no clinical covariates')
    return ColumnTransformer(tr,remainder='drop')

def _fit_logistic(X,y,seed):
    model=LogisticRegression(max_iter=2000,class_weight='balanced',random_state=seed)
    model.fit(X,y)
    return model

def _as2d(x):
    return x if sparse.issparse(x) else np.asarray(x)

def run(args):
    cohort=pd.read_csv(args.cohort)
    clinical=_read_table(args.clinical_table)
    contract=yaml.safe_load(Path(args.covariate_contract).read_text())
    accepted=contract.get('accepted_covariates',[])
    numeric=[x['column'] for x in accepted if x.get('type')=='numeric']
    categorical=[x['column'] for x in accepted if x.get('type')=='categorical']
    if not numeric and not categorical: raise ValueError('covariate contract contains no accepted covariates')
    pid_col=contract['patient_id_column']
    clinical=clinical.copy(); clinical[pid_col]=clinical[pid_col].astype(str)
    if clinical[pid_col].duplicated().any():
        dups=clinical.loc[clinical[pid_col].duplicated(),pid_col].head().tolist()
        raise ValueError(f'duplicate clinical patient ids: {dups}')

    patient_rows=build_patient_pathology_vectors(cohort,args.feature_root)
    pdf=pd.DataFrame({'patient_id':[r[0] for r in patient_rows], 'label_id':[r[1] for r in patient_rows], 'split':[r[2] for r in patient_rows], 'n_slides':[r[4] for r in patient_rows]})
    pvec=np.stack([r[3] for r in patient_rows])
    cdf=pdf.merge(clinical[[pid_col]+numeric+categorical],left_on='patient_id',right_on=pid_col,how='left',validate='one_to_one')
    if cdf[numeric+categorical].isna().all(axis=1).any():
        missing=cdf.loc[cdf[numeric+categorical].isna().all(axis=1),'patient_id'].tolist()
        raise ValueError(f'no clinical row/covariates for patients: {missing[:5]}')

    idx={s:np.where(cdf['split'].to_numpy()==s)[0] for s in ['train','val','test']}
    if len(idx['train'])<2: raise ValueError('insufficient train patients')
    y=cdf['label_id'].to_numpy(dtype=int)
    train_ids=cdf.iloc[idx['train']]['patient_id'].tolist()

    # Pathology preprocessing is fitted on train only.
    p_scaler=StandardScaler().fit(pvec[idx['train']])
    pz={s:p_scaler.transform(pvec[ii]) for s,ii in idx.items()}

    # Clinical preprocessing is fitted on train only.
    pre=_clinical_preprocessor(cdf,numeric,categorical)
    pre.fit(cdf.iloc[idx['train']])
    cz={s:pre.transform(cdf.iloc[ii]) for s,ii in idx.items()}

    models={}
    models['pathology_only']=_fit_logistic(pz['train'],y[idx['train']],args.seed)
    models['clinical_only']=_fit_logistic(cz['train'],y[idx['train']],args.seed)
    xcat_train=sparse.hstack([sparse.csr_matrix(pz['train']), sparse.csr_matrix(cz['train'])],format='csr')
    models['concat_fusion']=_fit_logistic(xcat_train,y[idx['train']],args.seed)

    results={}; pred_rows=[]
    for split in ['val','test']:
        if len(idx[split])==0: continue
        Xcat=sparse.hstack([sparse.csr_matrix(pz[split]), sparse.csr_matrix(cz[split])],format='csr')
        probs={
            'pathology_only':models['pathology_only'].predict_proba(pz[split]),
            'clinical_only':models['clinical_only'].predict_proba(cz[split]),
            'concat_fusion':models['concat_fusion'].predict_proba(Xcat),
        }
        probs['late_fusion']=(probs['pathology_only']+probs['clinical_only'])/2.0
        results[split]={k:_metrics(y[idx[split]],v) for k,v in probs.items()}
        for local_j,global_i in enumerate(idx[split]):
            row={'patient_id':cdf.iloc[global_i]['patient_id'],'label_id':int(y[global_i]),'split':split}
            for name,pp in probs.items():
                row[f'{name}_prediction']=int(np.argmax(pp[local_j]))
                for c,v in enumerate(pp[local_j]): row[f'{name}_prob_{c}']=float(v)
            pred_rows.append(row)

    incremental={}
    for split in results:
        for metric in ['auroc','auprc','balanced_accuracy','macro_f1']:
            fusion=results[split]['concat_fusion'].get(metric)
            singles=[results[split][m].get(metric) for m in ['pathology_only','clinical_only']]
            singles=[x for x in singles if x is not None]
            if fusion is not None and singles:
                incremental.setdefault(split,{})[f'concat_delta_vs_best_single_{metric}']=float(fusion-max(singles))

    out=Path(args.output_dir); out.mkdir(parents=True,exist_ok=True)
    pd.DataFrame(pred_rows).to_csv(out/'predictions.csv',index=False)
    meta={
        'status':'PASS',
        'task_type':'patient_level_multimodal_classification',
        'models':['pathology_only','clinical_only','concat_fusion','late_fusion'],
        'n_train':int(len(idx['train'])),'n_val':int(len(idx['val'])),'n_test':int(len(idx['test'])),
        'pathology_feature_dim':int(pvec.shape[1]),
        'clinical_numeric':numeric,'clinical_categorical':categorical,
        'preprocessing_fit_scope':'TRAIN_ONLY',
        'train_patient_ids_sha256':_hash_ids(train_ids),
        'multi_slide_patients':int((cdf['n_slides']>1).sum()),
        'metrics':results,
        'incremental_value_diagnostic':incremental,
        'warning':'Smoke/sample metrics are execution diagnostics unless a full scientific evaluation protocol is explicitly run.'
    }
    (out/'metrics.json').write_text(json.dumps(meta,indent=2),encoding='utf-8')
    # Save lightweight preprocessing provenance, not pickled executable objects.
    prov={
        'patient_id_column':pid_col,
        'numeric_covariates':numeric,
        'categorical_covariates':categorical,
        'fit_scope':'TRAIN_ONLY',
        'train_patient_ids_sha256':meta['train_patient_ids_sha256'],
        'pathology_standardization':'fit_on_train_only',
        'clinical_preprocessing':contract.get('preprocessing_contract',{}),
    }
    (out/'preprocessing_provenance.yaml').write_text(yaml.safe_dump(prov,sort_keys=False),encoding='utf-8')
    return meta

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--cohort',required=True)
    ap.add_argument('--feature-root',required=True)
    ap.add_argument('--clinical-table',required=True)
    ap.add_argument('--covariate-contract',required=True)
    ap.add_argument('--output-dir',required=True)
    ap.add_argument('--seed',type=int,default=42)
    a=ap.parse_args(); run(a)
if __name__=='__main__': main()
