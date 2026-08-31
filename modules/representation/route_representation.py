from __future__ import annotations
import argparse, yaml
from pathlib import Path


def _route_for(fam, mods):
    if fam in {'vqa','report_generation'} or 'text' in mods or 'pathology_report' in mods:
        return 'VISION_LANGUAGE'
    if 'omics' in mods or 'clinical' in mods or 'structured_clinical' in mods or 'tabular_clinical' in mods:
        return 'MULTIMODAL'
    if fam in {'segmentation','detection'}:
        return 'DENSE_VISION'
    return 'VISION'


def route(task, feature_provenance=None):
    fam=task.get('task_family','classification')
    req={str(x).lower() for x in (task.get('required_modalities') or [])}
    opt={str(x).lower() for x in (task.get('optional_modalities') or [])}
    primary=_route_for(fam, req)
    comparison=[]
    if opt:
        augmented=_route_for(fam, req | opt)
        if augmented != primary:
            comparison.append(augmented)

    fp=feature_provenance or {}
    pclass=fp.get('provenance_class')
    if pclass=='KNOWN_FM_FEATURE':
        strategy='REUSE_KNOWN_FM_FEATURES'
        primary_reproducible=True
    elif pclass=='LEGACY_FEATURE_PROVENANCE_INCOMPLETE':
        strategy='REUSE_LEGACY_FEATURES_FOR_REFERENCE_ONLY'
        primary_reproducible=False
    elif pclass=='NON_FM_FEATURE':
        strategy='REUSE_NON_FM_FEATURES_IF_TASK_COMPATIBLE'
        primary_reproducible=fp.get('reuse_status')=='PRIMARY_REPRODUCIBLE'
    else:
        strategy='SELECT_STANDARD_REPRESENTATION'
        primary_reproducible=False

    return {
        'task_id':task.get('task_id'),
        'route':primary,
        'primary_route':primary,
        'comparison_routes':comparison,
        'representation_strategy':strategy,
        'existing_feature_provenance_class':pclass or 'UNKNOWN_OR_NOT_PROVIDED',
        'existing_features_are_primary_reproducible':primary_reproducible,
        'fm_strategy':'TASK_DEPENDENT',
        'execute_feature_extraction_now':False,
    }


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('task_yaml'); ap.add_argument('--feature-provenance'); ap.add_argument('-o','--output',required=True); a=ap.parse_args()
    task=yaml.safe_load(Path(a.task_yaml).read_text())
    fp=yaml.safe_load(Path(a.feature_provenance).read_text()) if a.feature_provenance else None
    Path(a.output).write_text(yaml.safe_dump(route(task,fp),sort_keys=False),encoding='utf-8')
if __name__=='__main__': main()
