from __future__ import annotations
import argparse, json, shlex, sys
from pathlib import Path
import pandas as pd
import yaml

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from modules.clinical_covariates.build_covariate_contract import build_contract


def _read_table(path, sep=None):
    p=Path(path)
    if sep is None: sep='\t' if p.suffix.lower() in {'.tsv','.txt'} else ','
    return pd.read_csv(p,sep=sep)

def prepare(cfg, output_dir):
    out=Path(output_dir); out.mkdir(parents=True,exist_ok=True)
    clinical_cfg=cfg['clinical']
    df=_read_table(clinical_cfg['table'],clinical_cfg.get('sep'))
    cohort_df=_read_table(cfg['cohort_split'])
    train_ids=cohort_df.loc[cohort_df['split'].astype(str)=='train','patient_id'].astype(str).drop_duplicates().tolist() if {'split','patient_id'} <= set(cohort_df.columns) else None
    contract=build_contract(
        df,
        clinical_cfg['patient_id_col'],
        requested_cols=clinical_cfg.get('covariates'),
        exclude_cols=clinical_cfg.get('exclude_columns'),
        target_cols=clinical_cfg.get('target_columns'),
        max_missing=float(clinical_cfg.get('max_missing_fraction',0.8)),
        extra_leakage_patterns=clinical_cfg.get('extra_leakage_patterns'),
        fit_patient_ids=train_ids,
        availability_overrides=clinical_cfg.get('inference_availability'),
    )
    contract_path=out/'clinical_covariate_contract.yaml'
    contract_path.write_text(yaml.safe_dump(contract,sort_keys=False,allow_unicode=True),encoding='utf-8')
    if contract['status']!='READY':
        summary={'status':'BLOCKED_NO_USABLE_COVARIATES','covariate_contract':str(contract_path)}
        (out/'prepare_summary.yaml').write_text(yaml.safe_dump(summary,sort_keys=False),encoding='utf-8')
        return summary
    result_dir=out/'multimodal_baselines'
    argv=[
        sys.executable,str(ROOT/'adapters/multimodal/train_patient_multimodal.py'),
        '--cohort',str(cfg['cohort_split']),
        '--feature-root',str(cfg['feature_root']),
        '--clinical-table',str(clinical_cfg['table']),
        '--covariate-contract',str(contract_path),
        '--output-dir',str(result_dir),
        '--seed',str(cfg.get('seed',42)),
    ]
    summary={
        'status':'READY',
        'execution_slice':'STRUCTURED_MULTIMODAL_CLASSIFICATION',
        'reuse':{
            'cohort_split':str(cfg['cohort_split']),
            'feature_root':str(cfg['feature_root']),
            'rerun_trident':False,
        },
        'clinical_covariate_contract':str(contract_path),
        'command':{'argv':argv,'shell_preview':' '.join(shlex.quote(x) for x in argv)},
        'output_dir':str(result_dir),
        'metric_interpretation':'SMOKE_DIAGNOSTIC unless a full scientific evaluation protocol is explicitly requested',
    }
    (out/'prepare_summary.yaml').write_text(yaml.safe_dump(summary,sort_keys=False,allow_unicode=True),encoding='utf-8')
    return summary

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('config_yaml'); ap.add_argument('-o','--output-dir',required=True); a=ap.parse_args()
    cfg=yaml.safe_load(Path(a.config_yaml).read_text())
    s=prepare(cfg,a.output_dir); print(json.dumps(s,indent=2))
if __name__=='__main__': main()
