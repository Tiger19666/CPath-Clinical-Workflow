from __future__ import annotations
import argparse, re
from pathlib import Path
import sys
SKILL_ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(SKILL_ROOT))
import yaml
try:
    from .assess_cohort_compatibility import assess
except ImportError:
    from modules.study.assess_cohort_compatibility import assess


def _norm(x):
    return re.sub(r'[^a-z0-9]+','_',str(x or '').strip().lower()).strip('_')


def _supports(c,target):
    tk=_norm(target)
    return any(x.get('target_key')==tk or _norm(x.get('target'))==tk or _norm(x.get('semantic_role'))==tk for x in c.get('labels') or [])


def plan(registry: dict,target: str,required_modalities=None,development_cohort_id=None) -> dict:
    cohorts=registry.get('cohorts') or []
    eligible=[c for c in cohorts if _supports(c,target) and c.get('status')!='NOT_READY']
    dev=None
    if development_cohort_id:
        dev=next((c for c in eligible if c['cohort_id']==development_cohort_id),None)
        if dev is None: raise ValueError('requested development cohort does not support target')
    if dev is None:
        dev=next((c for c in eligible if c.get('declared_role')=='DEVELOPMENT'),None)
    if dev is None and eligible: dev=eligible[0]
    assignments=[]; compat=[]
    for c in cohorts:
        if not _supports(c,target):
            role='UNSUPPORTED'; reason='target_not_supported'
        elif dev and c['cohort_id']==dev['cohort_id']:
            role='DEVELOPMENT'; reason='selected_development_cohort'
        elif dev:
            x=assess(dev,c,target,required_modalities); compat.append(x)
            if x['status']=='INCOMPATIBLE': role='TRANSFER_ONLY'; reason='clinical_or_modal_compatibility_failed'
            elif c.get('declared_role')=='EXTERNAL_VALIDATION' or c.get('independence_from_development')=='EXTERNAL':
                role='EXTERNAL_VALIDATION'; reason='explicit_external_independence'
            elif c.get('declared_role')=='INTERNAL_VALIDATION' or c.get('independence_from_development')=='SAME_SOURCE':
                role='INTERNAL_VALIDATION'; reason='same_source_or_declared_internal'
            else:
                role='VALIDATION_CANDIDATE'; reason='independence_not_verified'
        else:
            role='UNSUPPORTED'; reason='no_cohort_supports_target'
        assignments.append({'cohort_id':c['cohort_id'],'role':role,'reason':reason})
    return {
        'version':'MultiCohortStudyPlan-v1','target':target,
        'development_cohort_id':dev['cohort_id'] if dev else None,
        'assignments':assignments,'compatibility_to_development':compat,
        'pooling_policy':'NO_AUTOMATIC_POOLING',
        'external_claim_rule':'EXTERNAL_VALIDATION requires explicit independence evidence; VALIDATION_CANDIDATE cannot upgrade claims',
        'status':'READY' if dev else 'NOT_READY',
    }


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('registry'); ap.add_argument('--target',required=True); ap.add_argument('--development-cohort-id'); ap.add_argument('--required-modalities',nargs='*',default=[]); ap.add_argument('-o','--output',required=True); a=ap.parse_args()
    reg=yaml.safe_load(Path(a.registry).read_text()); out=plan(reg,a.target,a.required_modalities,a.development_cohort_id)
    Path(a.output).write_text(yaml.safe_dump(out,sort_keys=False),encoding='utf-8')
if __name__=='__main__': main()
