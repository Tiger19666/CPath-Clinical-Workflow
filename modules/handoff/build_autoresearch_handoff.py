from __future__ import annotations


def _claim_level(claim_scope):
    if isinstance(claim_scope,dict):
        return claim_scope.get('maximum_claim_level') or claim_scope.get('claim_level') or claim_scope.get('level')
    return claim_scope


def _artifact_clean(artifact_state):
    if not artifact_state: return None
    if 'all_fresh' in artifact_state: return bool(artifact_state.get('all_fresh'))
    vals=(artifact_state.get('artifacts') or {}).values()
    return all((x.get('state')=='FRESH') for x in vals) if vals else None


def build(task_spec, split_spec, representation, baselines, claim_scope, known_failure_modes=None,
          evaluation_contract=None, reproducibility_manifest=None, subgroup_summary=None,
          cohort_registry=None, study_plan=None, artifact_state=None):
    reasons=[]
    if not task_spec or not task_spec.get('task_id'): reasons.append('task_spec_missing')
    if not split_spec or not split_spec.get('test_manifest'): reasons.append('frozen_test_split_missing')
    if not baselines: reasons.append('standard_baseline_missing')
    if not evaluation_contract: reasons.append('evaluation_contract_missing')
    if not reproducibility_manifest or reproducibility_manifest.get('status')!='FROZEN': reasons.append('reproducibility_manifest_not_frozen')
    level=_claim_level(claim_scope)
    if not level: reasons.append('clinical_claim_scope_missing')
    if level=='EXECUTION_ONLY': reasons.append('smoke_execution_only_not_scientific_baseline')
    fresh=_artifact_clean(artifact_state)
    if fresh is False: reasons.append('stale_upstream_artifacts')
    if study_plan and study_plan.get('status')=='NOT_READY': reasons.append('multicohort_study_plan_not_ready')
    status='READY_FOR_AUTORESEARCH' if not reasons else 'NOT_READY'
    immutable={
        'clinical_endpoint':task_spec.get('target'),
        'clinical_question':task_spec.get('clinical_question'),
        'label_definition':task_spec.get('label_definition'),
        'prediction_level':task_spec.get('prediction_level'),
        'task_family':task_spec.get('task_family'),
        'frozen_test_split':split_spec.get('test_manifest'),
        'clinical_claim_scope':claim_scope,
        'evaluation_contract':evaluation_contract,
        'study_plan':study_plan,
    }
    controlled={
        'representations':representation,
        'cohort_registry':cohort_registry,
        'rule':'representation/cohort changes require an explicitly declared controlled comparison and must not overwrite the frozen baseline contract',
    }
    return {
      'version':'AutoResearchHandoff-v1',
      'task_id':task_spec.get('task_id') if task_spec else None,
      'status':status,
      'readiness_reasons':reasons,
      'immutable':immutable,
      'controlled':controlled,
      'free':{
          'allowed_algorithm_changes':['architecture','aggregation','loss','sampling','optimization','fusion'],
          'test_set_access_rule':'No algorithm choice, hyperparameter selection, debugging decision, or hypothesis revision may use the frozen final test labels/results.',
      },
      'forbidden_changes':[
          'clinical_endpoint','clinical_question_semantics','label_definition','prediction_unit',
          'frozen_test_split','clinical_claim_without_clinical_review','evaluation_contract_without_clinical_review',
          'silent_cohort_redefinition','silent_external_validation_relabeling'
      ],
      'baselines':baselines,
      'evidence':{
          'reproducibility_manifest':reproducibility_manifest,
          'subgroup_summary':subgroup_summary,
          'artifact_state':artifact_state,
      },
      'known_failure_modes':known_failure_modes or [],
      'handoff_policy':{
          'negative_results_must_be_retained':True,
          'new_algorithm_results_must_use_frozen_evaluation_contract':True,
          'claim_upgrades_return_to_clinical_review':True,
      }
    }
