from __future__ import annotations
import argparse, sys
from pathlib import Path
import yaml
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from modules.cohort.build_task_cohort import build as build_cohort
from modules.splits.build_group_split import build as build_split
from modules.foundation_models.resolve_visual_fm import resolve as resolve_fm
from modules.execution.resolve_execution_permission import resolve as resolve_permission
from adapters.trident.build_execution_contract import build as build_trident
from modules.artifacts.state import register


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--config',required=True); ap.add_argument('--local',required=True); ap.add_argument('--output-dir',required=True); a=ap.parse_args()
    cfg=yaml.safe_load(Path(a.config).read_text()); local=yaml.safe_load(Path(a.local).read_text()) if Path(a.local).exists() else {}
    out=Path(a.output_dir); out.mkdir(parents=True,exist_ok=True)
    cohort,excluded,csummary=build_cohort(cfg['cohort']); cohort_fp=out/'cohort.csv'; excluded_fp=out/'excluded.csv'; csum_fp=out/'cohort_summary.yaml'
    cohort.to_csv(cohort_fp,index=False); excluded.to_csv(excluded_fp,index=False); csum_fp.write_text(yaml.safe_dump(csummary,sort_keys=False,allow_unicode=True),encoding='utf-8')
    split_cfg=cfg.get('split') or {}; split_df,ss=build_split(cohort,split_cfg.get('group_col','patient_id'),split_cfg.get('label_col','label_id'),split_cfg.get('seed',42),(split_cfg.get('train_ratio',.7),split_cfg.get('val_ratio',.1),split_cfg.get('test_ratio',.2)))
    split_fp=out/'cohort_split.csv'; split_summary_fp=out/'split_summary.yaml'; split_df.to_csv(split_fp,index=False); split_summary_fp.write_text(yaml.safe_dump(ss,sort_keys=False),encoding='utf-8')
    reg=yaml.safe_load((ROOT/'registries/foundation_models.yaml').read_text())
    fmcfg=cfg.get('foundation_model') or {}; fm=resolve_fm(reg,local,fmcfg.get('preferences',['uni_v2','uni_v1']),bool(fmcfg.get('allow_remote',False))); fm_fp=out/'foundation_model_resolution.yaml'; fm_fp.write_text(yaml.safe_dump(fm,sort_keys=False),encoding='utf-8')
    tcfg=cfg.get('trident') or {}; tr=build_trident(split_fp,fm,local,tcfg.get('output_root') or str(out/'representation'),tcfg.get('feature_store_id','PRIMARY_KNOWN_FM'),tcfg.get('gpus') or [0]); tr_fp=out/'trident_execution_contract.yaml'; tr_fp.write_text(yaml.safe_dump(tr,sort_keys=False),encoding='utf-8')
    readiness='READY_TO_RUN' if len(cohort)>0 and tr.get('status')=='READY' else 'NOT_READY'
    req=cfg.get('request') or {}; perm=resolve_permission(req.get('mode','TASK_SPECIFIED'),req.get('execution_intent','PLAN'),readiness,selected=True); perm_fp=out/'execution_permission.yaml'; perm_fp.write_text(yaml.safe_dump(perm,sort_keys=False),encoding='utf-8')
    manifest={'version':'ClinicalV02ArtifactManifest-v1','artifacts':{}}
    manifest['artifacts']['cohort']=register('cohort',cohort_fp,{'config':a.config},'modules/cohort/build_task_cohort.py')
    manifest['artifacts']['split']=register('split',split_fp,{'cohort':cohort_fp,'config':a.config},'modules/splits/build_group_split.py'); manifest['artifacts']['split']['artifact_dependencies']=['cohort']
    manifest['artifacts']['fm_resolution']=register('fm_resolution',fm_fp,{'local':a.local,'registry':ROOT/'registries/foundation_models.yaml'},'modules/foundation_models/resolve_visual_fm.py')
    manifest['artifacts']['trident_contract']=register('trident_contract',tr_fp,{'split':split_fp,'fm_resolution':fm_fp,'local':a.local},'adapters/trident/build_execution_contract.py'); manifest['artifacts']['trident_contract']['artifact_dependencies']=['split','fm_resolution']
    (out/'artifact_manifest.yaml').write_text(yaml.safe_dump(manifest,sort_keys=False),encoding='utf-8')
    summary={'status':'READY_FOR_SANITY' if perm['allowed'] else 'STOPPED_AT_GATE','cohort_patients':csummary['patients_included'],'cohort_slides':csummary['slides_included'],'fm_status':fm['status'],'trident_status':tr.get('status'),'execution_permission':perm}
    (out/'prepare_summary.yaml').write_text(yaml.safe_dump(summary,sort_keys=False),encoding='utf-8')
    print(yaml.safe_dump(summary,sort_keys=False))
if __name__=='__main__': main()
