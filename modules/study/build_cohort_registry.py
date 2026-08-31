from __future__ import annotations
import argparse, re
from pathlib import Path
import sys
SKILL_ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(SKILL_ROOT))
import yaml

VALID_ROLES={
    'DEVELOPMENT','INTERNAL_VALIDATION','EXTERNAL_VALIDATION','VALIDATION_CANDIDATE',
    'TRANSFER_ONLY','UNSUPPORTED','UNASSIGNED'
}


def _norm(x):
    return re.sub(r'[^a-z0-9]+','_',str(x or '').strip().lower()).strip('_')


def _label_signature(label: dict) -> dict:
    return {
        'target': label.get('target') or label.get('name') or label.get('semantic_role'),
        'target_key': _norm(label.get('target') or label.get('name') or label.get('semantic_role')),
        'semantic_role': label.get('semantic_role'),
        'level': label.get('level') or label.get('prediction_level'),
        'definition': label.get('definition') or label.get('label_definition'),
        'availability': label.get('availability','UNKNOWN'),
    }


def build(cohorts: list[dict]) -> dict:
    out=[]
    seen=set()
    for i,c in enumerate(cohorts or [],1):
        cid=str(c.get('cohort_id') or f'C{i:03d}')
        if cid in seen:
            raise ValueError(f'duplicate cohort_id: {cid}')
        seen.add(cid)
        role=str(c.get('declared_role') or c.get('study_role') or 'UNASSIGNED').upper()
        if role not in VALID_ROLES:
            raise ValueError(f'unsupported cohort role: {role}')
        modalities=sorted({str(x) for x in (c.get('modalities') or c.get('modality_signature') or [])})
        labels=[_label_signature(x) for x in (c.get('labels') or [])]
        issues=[]
        if not modalities: issues.append('modalities_unresolved')
        if not c.get('patient_identity_key'): issues.append('patient_identity_key_unresolved')
        if not c.get('disease_context'): issues.append('disease_context_unresolved')
        if not labels: issues.append('clinical_labels_unresolved')
        out.append({
            'cohort_id':cid,
            'name':c.get('name') or cid,
            'root':c.get('root'),
            'disease_context':c.get('disease_context'),
            'source_site':c.get('source_site') or c.get('institution'),
            'source_family':c.get('source_family'),
            'independence_from_development':str(c.get('independence_from_development','UNKNOWN')).upper(),
            'patient_identity_key':c.get('patient_identity_key'),
            'modalities':modalities,
            'labels':labels,
            'representation':c.get('representation'),
            'declared_role':role,
            'pooling_permission':bool(c.get('pooling_permission',False)),
            'status':'READY' if not issues else 'CONDITIONAL',
            'issues':issues,
        })
    return {
        'version':'CohortRegistry-v1',
        'cohort_count':len(out),
        'cohorts':out,
        'default_pooling_policy':'DO_NOT_POOL_WITHOUT_EXPLICIT_COMPATIBILITY_AND_PERMISSION',
    }


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('input'); ap.add_argument('-o','--output',required=True); a=ap.parse_args()
    obj=yaml.safe_load(Path(a.input).read_text()) or {}
    cohorts=obj.get('cohorts') if isinstance(obj,dict) else obj
    Path(a.output).write_text(yaml.safe_dump(build(cohorts),sort_keys=False),encoding='utf-8')
if __name__=='__main__': main()
