from __future__ import annotations
import argparse, re
from pathlib import Path
import sys
SKILL_ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(SKILL_ROOT))
import yaml


def _norm(x):
    return re.sub(r'[^a-z0-9]+','_',str(x or '').strip().lower()).strip('_')


def _find_label(c, target):
    tk=_norm(target)
    for x in c.get('labels') or []:
        if x.get('target_key')==tk or _norm(x.get('target'))==tk or _norm(x.get('semantic_role'))==tk:
            return x
    return None


def assess(a: dict,b: dict,target: str,required_modalities=None) -> dict:
    required=set(required_modalities or [])
    reasons=[]; blockers=[]
    la,lb=_find_label(a,target),_find_label(b,target)
    if not la or not lb: blockers.append('endpoint_missing_in_one_or_both_cohorts')
    else:
        if la.get('level') and lb.get('level') and la.get('level')!=lb.get('level'):
            blockers.append('prediction_level_mismatch')
        da,db=(la.get('definition') or '').strip(),(lb.get('definition') or '').strip()
        if da and db and _norm(da)!=_norm(db): reasons.append('label_definition_requires_harmonization_review')
    if a.get('disease_context') and b.get('disease_context') and _norm(a['disease_context'])!=_norm(b['disease_context']):
        blockers.append('disease_context_mismatch')
    ma,mb=set(a.get('modalities') or []),set(b.get('modalities') or [])
    if required and (not required.issubset(ma) or not required.issubset(mb)):
        blockers.append('required_modality_missing')
    ra,rb=a.get('representation') or {},b.get('representation') or {}
    if ra and rb:
        if ra.get('encoder') and rb.get('encoder') and ra.get('encoder')!=rb.get('encoder'):
            reasons.append('representation_encoder_differs')
        if ra.get('preprocessing_hash') and rb.get('preprocessing_hash') and ra.get('preprocessing_hash')!=rb.get('preprocessing_hash'):
            reasons.append('preprocessing_contract_differs')
    status='INCOMPATIBLE' if blockers else ('CONDITIONAL' if reasons else 'COMPATIBLE')
    pooling_allowed=(status=='COMPATIBLE' and a.get('pooling_permission') is True and b.get('pooling_permission') is True)
    return {
        'cohort_a':a.get('cohort_id'),'cohort_b':b.get('cohort_id'),'target':target,
        'status':status,'blockers':blockers,'review_items':reasons,
        'pooling_allowed':pooling_allowed,
        'pooling_rule':'explicit_permission_required_even_when_compatible',
    }


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('registry'); ap.add_argument('--cohort-a',required=True); ap.add_argument('--cohort-b',required=True); ap.add_argument('--target',required=True); ap.add_argument('--required-modalities',nargs='*',default=[]); ap.add_argument('-o','--output',required=True); a=ap.parse_args()
    reg=yaml.safe_load(Path(a.registry).read_text()); by={x['cohort_id']:x for x in reg['cohorts']}
    out=assess(by[a.cohort_a],by[a.cohort_b],a.target,a.required_modalities)
    Path(a.output).write_text(yaml.safe_dump(out,sort_keys=False),encoding='utf-8')
if __name__=='__main__': main()
