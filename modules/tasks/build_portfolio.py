from __future__ import annotations
import argparse
from pathlib import Path
import yaml

ROLE_TO_FAMILY={
 'diagnosis':'classification','subtype':'classification','grade':'ordinal_classification','stage':'ordinal_classification',
 'biomarker':'classification','mutation':'classification','molecular_subtype':'classification',
 'overall_survival':'survival','progression_free_survival':'survival','disease_free_survival':'survival','recurrence':'survival',
 'continuous_biomarker':'regression','anatomic_region':'classification','segmentation_target':'segmentation',
 'question_answer':'vqa','pathology_report':'report_generation'
}


def build(label_catalog):
    tasks=[]
    future=[]
    for i,l in enumerate(label_catalog.get('labels') or [],1):
        role=l.get('semantic_role') or 'unknown'
        fam=l.get('task_family') or ROLE_TO_FAMILY.get(role,'classification')
        coverage=l.get('coverage')
        linkage=l.get('linkage_status','UNKNOWN')
        quality=l.get('quality','UNKNOWN')
        locally_supported = l.get('locally_supported', True) is not False
        if not locally_supported:
            future.append({
                'opportunity_id': f'F{i:03d}',
                'name': l.get('name', role),
                'reason': l.get('unsupported_reason') or 'target_or_required_modality_not_available_locally',
                'semantic_role': role,
            })
            continue
        if linkage not in {'VERIFIED','EXPLICIT'}:
            status='CONDITIONAL_GO' if linkage!='FAILED' else 'NO_GO'
            deps=['resolve_label_linkage']
        elif coverage is not None and coverage < 0.2:
            status='CONDITIONAL_GO'; deps=['review_low_label_coverage']
        else:
            status='GO'; deps=[]
        target=l.get('name',role)
        tasks.append({
          'task_id':f'T{len(tasks)+1:03d}','name':f"{target} clinical prediction",
          'clinical_question':l.get('clinical_question') or f"Can pathology data support clinically valid prediction of {target}?",
          'task_family':fam,'prediction_level':l.get('level','patient'),'target':target,
          'label_id':l.get('label_id'), 'label_source':l.get('source') or l.get('label_source') or l.get('label_id'),
          'label_quality':quality,'label_coverage':coverage,
          'required_modalities':l.get('required_modalities') or ['pathology_image'],
          'optional_modalities':l.get('optional_modalities') or [],'status':status,'dependencies':deps,
          'support_tier':'SUPPORTED_TASK'
        })
    return {
        'tasks':tasks,
        'portfolio_size':len(tasks),
        'selection_policy':'retain_all_candidates',
        'future_opportunities':future,
        'future_opportunity_count':len(future),
    }


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('label_catalog'); ap.add_argument('-o','--output',required=True); a=ap.parse_args()
    cat=yaml.safe_load(Path(a.label_catalog).read_text()); Path(a.output).write_text(yaml.safe_dump(build(cat),sort_keys=False),encoding='utf-8')
if __name__=='__main__': main()
