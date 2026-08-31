from __future__ import annotations
import argparse, json, sys
from pathlib import Path
import yaml
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from modules.evaluation.build_evaluation_contract import build as build_eval_contract
from modules.evaluation.evaluate_predictions import evaluate
from modules.robustness.build_subgroup_report import build as build_subgroups
from modules.reproducibility.build_experiment_manifest import build as build_manifest
from modules.claims.guard_clinical_claims import guard as claim_guard


def run(args):
    out=Path(args.output_dir); out.mkdir(parents=True,exist_ok=True)
    contract=build_eval_contract('classification','patient',args.study_scope,args.primary_model,args.comparators,1)
    cp=out/'evaluation_contract.yaml'; cp.write_text(yaml.safe_dump(contract,sort_keys=False),encoding='utf-8')
    ev=evaluate(args.predictions,contract,args.split,args.bootstrap_reps,args.seed)
    ep=out/'evaluation_report.yaml'; ep.write_text(yaml.safe_dump(ev,sort_keys=False),encoding='utf-8')
    sg=None; sp=None
    if args.clinical_table and args.patient_id_col and args.subgroups:
        sg=build_subgroups(args.predictions,args.clinical_table,args.patient_id_col,args.subgroups,args.primary_model,args.split,args.min_group_n)
        sp=out/'subgroup_report.yaml'; sp.write_text(yaml.safe_dump(sg,sort_keys=False),encoding='utf-8')
    claims=claim_guard(args.study_scope,ev['status'])
    clp=out/'clinical_claim_guard.yaml'; clp.write_text(yaml.safe_dump(claims,sort_keys=False),encoding='utf-8')
    outputs=[cp,ep,clp]+([sp] if sp else [])
    inputs=[args.predictions]+([args.clinical_table] if args.clinical_table else [])+list(args.upstream_inputs or [])
    manifest=build_manifest(args.task_id,args.study_scope,inputs,outputs,args.skill_root,args.seed,extra={'evaluation_split':args.split,'primary_model':args.primary_model})
    mp=out/'reproducibility_manifest.yaml'; mp.write_text(yaml.safe_dump(manifest,sort_keys=False),encoding='utf-8')
    summary={'status':'PASS','task_id':args.task_id,'study_scope':args.study_scope,'evaluation_status':ev['status'],'claim_level':claims['maximum_claim_level'],'subgroup_status':sg['status'] if sg else 'NOT_REQUESTED','reproducibility_status':manifest['status']}
    (out/'v04_validation_summary.yaml').write_text(yaml.safe_dump(summary,sort_keys=False),encoding='utf-8')
    return summary

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--task-id',required=True); ap.add_argument('--predictions',required=True); ap.add_argument('--clinical-table'); ap.add_argument('--patient-id-col'); ap.add_argument('--subgroups',nargs='*'); ap.add_argument('--primary-model',default='concat_fusion'); ap.add_argument('--comparators',nargs='*',default=['pathology_only','clinical_only']); ap.add_argument('--split',default='test'); ap.add_argument('--study-scope',default='SMOKE_INTERNAL'); ap.add_argument('--bootstrap-reps',type=int,default=200); ap.add_argument('--min-group-n',type=int,default=20); ap.add_argument('--seed',type=int,default=42); ap.add_argument('--upstream-inputs',nargs='*'); ap.add_argument('--skill-root'); ap.add_argument('--output-dir',required=True)
    a=ap.parse_args(); print(yaml.safe_dump(run(a),sort_keys=False))
if __name__=='__main__': main()
