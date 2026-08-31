from __future__ import annotations
import argparse, json
from pathlib import Path
import yaml


def route(request: dict) -> dict:
    tasks=request.get('requested_tasks') or []
    cohorts=request.get('cohorts') or []
    if len(tasks)==0: mode='DISCOVERY'
    elif len(tasks)==1: mode='TASK_SPECIFIED'
    else: mode='MULTI_TASK_SPECIFIED'
    intent=request.get('execution_intent')
    if not intent:
        intent='ASSESS_ONLY' if mode=='DISCOVERY' else 'PLAN'
    if intent not in {'ASSESS_ONLY','PLAN','EXECUTE','EXECUTE_SELECTED'}:
        raise ValueError(f'unsupported execution_intent: {intent}')
    if mode!='DISCOVERY' and intent=='EXECUTE_SELECTED':
        raise ValueError('EXECUTE_SELECTED is only valid for DISCOVERY')
    cohort_mode='MULTI_COHORT' if len(cohorts)>1 else ('SINGLE_COHORT' if len(cohorts)==1 or request.get('dataset_root') else 'UNRESOLVED')
    source_status='RESOLVED' if request.get('dataset_root') or cohorts else 'UNRESOLVED'
    return {**request,'mode':mode,'execution_intent':intent,'explicit_task_count':len(tasks),'cohort_mode':cohort_mode,'cohort_count':len(cohorts) if cohorts else (1 if request.get('dataset_root') else 0),'data_source_status':source_status}


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('input'); ap.add_argument('-o','--output',required=True); a=ap.parse_args()
    p=Path(a.input); obj=yaml.safe_load(p.read_text()) if p.suffix in {'.yaml','.yml'} else json.loads(p.read_text())
    out=route(obj); Path(a.output).write_text(yaml.safe_dump(out,sort_keys=False),encoding='utf-8')
if __name__=='__main__': main()
