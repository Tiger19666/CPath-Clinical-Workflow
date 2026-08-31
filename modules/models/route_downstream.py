from __future__ import annotations
import argparse, yaml
from pathlib import Path

DEFAULTS={
 'classification': ['mean_pooling','abmil','clam_sb'],
 'ordinal_classification':['abmil','ordinal_head'],
 'survival':['abmil_plus_cox','abmil_plus_discrete_time'],
 'segmentation':['unet','deeplabv3'],
 'vqa':['zero_shot_vlm','lora_vlm'],
 'report_generation':['lora_vlm'],
 'multimodal_prediction':['concatenation','late_fusion','simple_gated_fusion'],
 'regression':['mean_pooling_regressor','abmil_regressor'],
}


def _has_structured_clinical(task):
    mods={str(x).lower() for x in (task.get('required_modalities') or [])+(task.get('optional_modalities') or [])}
    return bool(mods & {'clinical','structured_clinical','tabular_clinical'})


def route(task):
    fam=task.get('task_family','classification')
    baselines=DEFAULTS.get(fam,['task_specific_standard_baseline'])
    groups=[]
    if fam=='survival':
        groups.append({'group':'pathology_only','required':True,'baselines':['abmil_plus_cox','abmil_plus_discrete_time']})
        if _has_structured_clinical(task):
            groups.append({'group':'clinical_only','required':True,'baselines':['cox_clinical','discrete_time_clinical']})
            groups.append({'group':'pathology_plus_clinical','required':True,'baselines':['late_fusion_survival','concat_survival']})
    elif fam=='multimodal_prediction' or _has_structured_clinical(task):
        groups.append({'group':'pathology_only','required':True,'baselines':DEFAULTS.get('classification',['abmil'])})
        groups.append({'group':'clinical_only','required':True,'baselines':['linear_or_mlp_clinical']})
        groups.append({'group':'multimodal_fusion','required':True,'baselines':['concatenation','late_fusion','simple_gated_fusion']})
    else:
        groups.append({'group':'primary_standard_baseline','required':True,'baselines':baselines})
    return {
        'version':'ClinicalBaselineContract-v1',
        'task_id':task.get('task_id'),
        'task_family':fam,
        'standard_baselines':baselines,
        'baseline_comparison_contract':groups,
        'novel_algorithm_allowed_here':False,
        'purpose':'clinical_feasibility_reproducibility_and_incremental_value',
    }


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('task_yaml'); ap.add_argument('-o','--output',required=True); a=ap.parse_args(); task=yaml.safe_load(Path(a.task_yaml).read_text()); Path(a.output).write_text(yaml.safe_dump(route(task),sort_keys=False),encoding='utf-8')
if __name__=='__main__': main()
