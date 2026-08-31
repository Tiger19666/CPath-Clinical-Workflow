from __future__ import annotations
import argparse, json, re
from pathlib import Path
import pandas as pd
import yaml

ID_PATTERNS = [r'(^|_)id($|_)', r'(^|_)patient(_|$)', r'(^|_)slide(_|$)', r'(^|_)case(_|$)', r'barcode', r'filename', r'file_path', r'filepath', r'directory', r'(^|_)uri(_|$)']
DEFAULT_LEAKAGE_PATTERNS = [r'(^|_)label(_|$)', r'(^|_)target(_|$)', r'prediction', r'ground.?truth', r'histolog', r'morpholog', r'(^|_)subtype(_|$)']
VALID_AVAILABILITY={'AVAILABLE','CONDITIONAL','UNAVAILABLE','UNKNOWN'}

def _matches(name, patterns):
    s=str(name).lower(); return any(re.search(p,s) for p in patterns)

def build_contract(df: pd.DataFrame, patient_id_col: str, requested_cols=None, exclude_cols=None,
                   target_cols=None, max_missing=0.8, extra_leakage_patterns=None,
                   fit_patient_ids=None, availability_overrides=None):
    if patient_id_col not in df.columns: raise ValueError(f'patient id column not found: {patient_id_col}')
    requested=list(requested_cols or []); exclude=set(exclude_cols or [])|{patient_id_col}; targets=set(target_cols or [])
    leakage_patterns=DEFAULT_LEAKAGE_PATTERNS+list(extra_leakage_patterns or []); avail=availability_overrides or {}
    if requested:
        candidates=[c for c in requested if c in df.columns]; missing_requested=[c for c in requested if c not in df.columns]
    else:
        candidates=[c for c in df.columns if c not in exclude]; missing_requested=[]
    assess=df.copy(); assessment_scope='ALL_AVAILABLE'
    if fit_patient_ids is not None:
        ids={str(x) for x in fit_patient_ids}; assess=df[df[patient_id_col].astype(str).isin(ids)].copy(); assessment_scope='TRAIN_ONLY'
        if len(assess)==0: raise ValueError('no clinical rows matched fit_patient_ids')
    accepted=[]; rejected=[]
    for c in candidates:
        a=str(avail.get(c,'UNKNOWN')).upper()
        if a not in VALID_AVAILABILITY: raise ValueError(f'invalid availability for {c}: {a}')
        if c in exclude: rejected.append({'column':c,'reason':'EXPLICITLY_EXCLUDED'}); continue
        if c in targets: rejected.append({'column':c,'reason':'TARGET_COLUMN'}); continue
        if _matches(c,ID_PATTERNS): rejected.append({'column':c,'reason':'IDENTIFIER_LIKE'}); continue
        if _matches(c,leakage_patterns): rejected.append({'column':c,'reason':'POTENTIAL_TARGET_LEAKAGE'}); continue
        if a=='UNAVAILABLE': rejected.append({'column':c,'reason':'UNAVAILABLE_AT_INFERENCE','availability':a}); continue
        miss=float(assess[c].isna().mean())
        if miss>max_missing: rejected.append({'column':c,'reason':'EXCESSIVE_MISSINGNESS','missing_fraction':miss}); continue
        nunique=int(assess[c].nunique(dropna=True))
        if nunique<=1: rejected.append({'column':c,'reason':'CONSTANT_OR_EMPTY_IN_ASSESSMENT_SET','nunique':nunique,'assessment_scope':assessment_scope}); continue
        kind='numeric' if pd.api.types.is_numeric_dtype(df[c]) else 'categorical'
        accepted.append({'column':c,'type':kind,'missing_fraction':miss,'nunique':nunique,'availability':a,'assessment_scope':assessment_scope})
    status='READY' if accepted else 'NO_USABLE_COVARIATES'
    return {'status':status,'patient_id_column':patient_id_col,'requested_columns':requested,'missing_requested_columns':missing_requested,
            'assessment_scope':assessment_scope,'assessment_patient_count':int(assess[patient_id_col].nunique()),
            'accepted_covariates':accepted,'rejected_covariates':rejected,
            'preprocessing_contract':{'fit_scope':'TRAIN_ONLY','numeric':'median_imputation_then_standardization','categorical':'most_frequent_imputation_then_one_hot_ignore_unknown','test_fit_forbidden':True},
            'availability_contract':{'allowed':['AVAILABLE','CONDITIONAL','UNKNOWN'],'rejected':['UNAVAILABLE'],'unknown_requires_clinical_review':True},
            'notes':['Clinical covariates are baseline inputs, not algorithmic novelty.','When train patient IDs are supplied, missingness/variance eligibility is assessed on train only.','Inference-time availability is distinct from target leakage and should be reviewed task-wise.']}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--clinical-table',required=True); ap.add_argument('--patient-id-col',required=True); ap.add_argument('--columns',nargs='*'); ap.add_argument('--exclude',nargs='*'); ap.add_argument('--targets',nargs='*'); ap.add_argument('--max-missing',type=float,default=0.8); ap.add_argument('--train-patient-ids'); ap.add_argument('--availability-yaml'); ap.add_argument('-o','--output',required=True)
    a=ap.parse_args(); p=Path(a.clinical_table); sep='\t' if p.suffix.lower() in {'.tsv','.txt'} else ','; df=pd.read_csv(p,sep=sep)
    fit_ids=None
    if a.train_patient_ids:
        ip=Path(a.train_patient_ids); iddf=pd.read_csv(ip,sep='\t' if ip.suffix.lower() in {'.tsv','.txt'} else ',')
        col=a.patient_id_col if a.patient_id_col in iddf.columns else iddf.columns[0]; fit_ids=iddf[col].astype(str).tolist()
    availability=yaml.safe_load(Path(a.availability_yaml).read_text()) if a.availability_yaml else None
    out=build_contract(df,a.patient_id_col,a.columns,a.exclude,a.targets,a.max_missing,fit_patient_ids=fit_ids,availability_overrides=availability)
    op=Path(a.output); op.parent.mkdir(parents=True,exist_ok=True)
    if op.suffix.lower()=='.json': op.write_text(json.dumps(out,indent=2),encoding='utf-8')
    else: op.write_text(yaml.safe_dump(out,sort_keys=False,allow_unicode=True),encoding='utf-8')
if __name__=='__main__': main()
