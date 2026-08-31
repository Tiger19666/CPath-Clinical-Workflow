from __future__ import annotations
import argparse, json
from pathlib import Path
import yaml

LEVELS={
 'SMOKE': ('EXECUTION_ONLY', ['pipeline_execution','artifact_generation'], ['performance','generalization','clinical_utility','deployment']),
 'SMOKE_INTERNAL': ('EXECUTION_ONLY', ['pipeline_execution','artifact_generation'], ['performance','generalization','clinical_utility','deployment']),
 'EXECUTION_SMOKE': ('EXECUTION_ONLY', ['pipeline_execution','artifact_generation'], ['performance','generalization','clinical_utility','deployment']),
 'INTERNAL_HOLDOUT': ('RETROSPECTIVE_INTERNAL_VALIDATION', ['internal_performance','retrospective_association'], ['external_generalization','prospective_validity','clinical_utility','deployment']),
 'TEMPORAL_INTERNAL': ('TEMPORAL_INTERNAL_VALIDATION', ['temporal_internal_performance','retrospective_association'], ['external_generalization','clinical_utility','deployment']),
 'EXTERNAL': ('RETROSPECTIVE_EXTERNAL_VALIDATION', ['external_validation_performance','retrospective_generalization_to_evaluated_cohort'], ['prospective_validity','clinical_utility','deployment']),
 'MULTICENTER_EXTERNAL': ('MULTICENTER_EXTERNAL_VALIDATION', ['multicenter_external_validation'], ['prospective_validity','clinical_utility','deployment']),
 'PROSPECTIVE': ('PROSPECTIVE_VALIDATION', ['prospective_validation_performance'], ['clinical_utility','deployment']),
 'CLINICAL_UTILITY_STUDY': ('CLINICAL_UTILITY_EVIDENCE', ['clinical_utility_within_studied_workflow'], ['deployment_readiness_without_implementation_validation']),
}

def guard(study_scope, evaluation_status=None, external_independent=False, prospective=False, utility_study=False):
    scope=str(study_scope).upper()
    if utility_study: scope='CLINICAL_UTILITY_STUDY'
    elif prospective: scope='PROSPECTIVE'
    elif external_independent and scope not in {'MULTICENTER_EXTERNAL'}: scope='EXTERNAL'
    level,allow,forbid=LEVELS.get(scope,LEVELS['INTERNAL_HOLDOUT'])
    if evaluation_status=='DIAGNOSTIC_ONLY':
        level,allow,forbid=LEVELS['SMOKE_INTERNAL']
        scope='SMOKE_INTERNAL'
    language={
      'EXECUTION_ONLY':'The pipeline executed successfully on the smoke subset; reported metrics are execution diagnostics only.',
      'RETROSPECTIVE_INTERNAL_VALIDATION':'Report performance as retrospective internal validation on the frozen held-out cohort.',
      'TEMPORAL_INTERNAL_VALIDATION':'Report performance as temporal internal validation within the studied institution/data source.',
      'RETROSPECTIVE_EXTERNAL_VALIDATION':'Report performance as retrospective external validation limited to the independently evaluated cohort.',
      'MULTICENTER_EXTERNAL_VALIDATION':'Report multicenter external validation limited to the evaluated centers and retrospective setting.',
      'PROSPECTIVE_VALIDATION':'Report prospective validation performance; do not equate validation with demonstrated clinical utility.',
      'CLINICAL_UTILITY_EVIDENCE':'Clinical utility claims must remain limited to the prespecified studied workflow and endpoints.'
    }[level]
    return {'status':'PASS','study_scope':scope,'maximum_claim_level':level,'allowed_claim_classes':allow,'forbidden_claim_classes':forbid,'recommended_language':language,
            'hard_rules':['Do not upgrade claim level from metric magnitude alone.','External/generalization claims require independent external evidence.','Clinical utility requires an explicit utility study; retrospective AUROC is insufficient.']}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--study-scope',required=True); ap.add_argument('--evaluation-status'); ap.add_argument('--external-independent',action='store_true'); ap.add_argument('--prospective',action='store_true'); ap.add_argument('--utility-study',action='store_true'); ap.add_argument('-o','--output',required=True)
    a=ap.parse_args(); out=guard(a.study_scope,a.evaluation_status,a.external_independent,a.prospective,a.utility_study)
    p=Path(a.output); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(yaml.safe_dump(out,sort_keys=False,allow_unicode=True),encoding='utf-8')
if __name__=='__main__': main()
