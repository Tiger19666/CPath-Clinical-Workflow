from __future__ import annotations
import argparse, json
from pathlib import Path
import yaml

CLASSIFICATION = {
    'primary_metrics': ['auroc', 'auprc'],
    'secondary_metrics': ['balanced_accuracy', 'macro_f1', 'accuracy', 'sensitivity', 'specificity', 'brier_score', 'ece_10bin'],
    'uncertainty': {'method': 'patient_bootstrap_percentile', 'confidence_level': 0.95, 'default_replicates': 1000},
    'paired_comparison': {'method': 'paired_patient_bootstrap_delta', 'metrics': ['auroc', 'auprc', 'balanced_accuracy', 'macro_f1']},
}
SURVIVAL = {
    'primary_metrics': ['c_index'],
    'secondary_metrics': ['time_dependent_auc', 'brier_score'],
    'uncertainty': {'method': 'patient_bootstrap_percentile', 'confidence_level': 0.95, 'default_replicates': 1000},
    'paired_comparison': {'method': 'paired_patient_bootstrap_delta', 'metrics': ['c_index']},
}

def build(task_family: str, prediction_level: str='patient', study_scope: str='INTERNAL_HOLDOUT',
          primary_model: str|None=None, comparators=None, positive_class: int=1):
    tf = str(task_family).lower()
    if tf in {'classification', 'binary_classification', 'multiclass_classification'}:
        metrics = CLASSIFICATION
    elif tf == 'survival':
        metrics = SURVIVAL
    else:
        metrics = {
            'primary_metrics': [], 'secondary_metrics': [],
            'uncertainty': {'method':'TASK_SPECIFIC_REQUIRED'},
            'paired_comparison': {'method':'TASK_SPECIFIC_REQUIRED','metrics':[]}
        }
    scope = str(study_scope).upper()
    diagnostic_only = scope in {'SMOKE','SMOKE_INTERNAL','EXECUTION_SMOKE'}
    return {
        'status': 'READY' if metrics['primary_metrics'] else 'TASK_SPECIFIC_REVIEW_REQUIRED',
        'task_family': task_family,
        'prediction_level': prediction_level,
        'study_scope': scope,
        'diagnostic_only': diagnostic_only,
        'positive_class': int(positive_class),
        'primary_model': primary_model,
        'comparators': list(comparators or []),
        'metrics': metrics,
        'rules': {
            'unit_of_resampling': prediction_level,
            'paired_comparison_requires_same_patients': True,
            'test_set_re_split_forbidden': True,
            'smoke_metrics_are_performance_claims': False,
            'report_point_estimate_with_interval_when_scientific': True,
        }
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--task-family',required=True)
    ap.add_argument('--prediction-level',default='patient')
    ap.add_argument('--study-scope',default='INTERNAL_HOLDOUT')
    ap.add_argument('--primary-model')
    ap.add_argument('--comparators',nargs='*')
    ap.add_argument('--positive-class',type=int,default=1)
    ap.add_argument('-o','--output',required=True)
    a=ap.parse_args(); out=build(a.task_family,a.prediction_level,a.study_scope,a.primary_model,a.comparators,a.positive_class)
    p=Path(a.output); p.parent.mkdir(parents=True,exist_ok=True)
    if p.suffix.lower()=='.json': p.write_text(json.dumps(out,indent=2),encoding='utf-8')
    else: p.write_text(yaml.safe_dump(out,sort_keys=False,allow_unicode=True),encoding='utf-8')

if __name__=='__main__': main()
