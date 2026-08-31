from __future__ import annotations
import argparse, json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import yaml
from modules.handoff.build_autoresearch_handoff import build as build_handoff
from modules.runs.build_run_manifest import build as build_run_manifest


def load(path):
    if not path: return None
    p=Path(path)
    if p.suffix.lower()=='.json': return json.loads(p.read_text())
    return yaml.safe_load(p.read_text())


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--task-spec',required=True)
    ap.add_argument('--split-spec',required=True)
    ap.add_argument('--representation',required=True)
    ap.add_argument('--baselines',required=True)
    ap.add_argument('--claim-scope',required=True)
    ap.add_argument('--evaluation-contract',required=True)
    ap.add_argument('--reproducibility-manifest',required=True)
    ap.add_argument('--subgroup-summary')
    ap.add_argument('--cohort-registry')
    ap.add_argument('--study-plan')
    ap.add_argument('--artifact-state')
    ap.add_argument('--known-failure-modes')
    ap.add_argument('--skill-root',required=True)
    ap.add_argument('--request-spec')
    ap.add_argument('--task-portfolio')
    ap.add_argument('--output-dir',required=True)
    a=ap.parse_args()
    out=Path(a.output_dir); out.mkdir(parents=True,exist_ok=True)
    task=load(a.task_spec); split=load(a.split_spec); rep=load(a.representation); base=load(a.baselines); claim=load(a.claim_scope)
    ev=load(a.evaluation_contract); repro=load(a.reproducibility_manifest); subgroup=load(a.subgroup_summary)
    registry=load(a.cohort_registry); study=load(a.study_plan); state=load(a.artifact_state)
    failures=load(a.known_failure_modes) if a.known_failure_modes else []
    if isinstance(failures,dict): failures=failures.get('known_failure_modes') or failures.get('failures') or []
    handoff=build_handoff(task,split,rep,base,claim,failures,ev,repro,subgroup,registry,study,state)
    hp=out/'autoresearch_handoff.yaml'; hp.write_text(yaml.safe_dump(handoff,sort_keys=False),encoding='utf-8')
    run=build_run_manifest(a.skill_root,a.request_spec,a.cohort_registry,a.task_portfolio,a.artifact_state,
                           notes=['v1 finalization records the frozen clinical contract; it does not change upstream science.'])
    rp=out/'clinical_run_manifest.yaml'; rp.write_text(yaml.safe_dump(run,sort_keys=False),encoding='utf-8')
    summary={
        'version':'CPath-Clinical-v1.0',
        'task_id':task.get('task_id'),
        'clinical_workflow_status':'STABLE_CONTRACT_EMITTED',
        'autoresearch_handoff_status':handoff['status'],
        'autoresearch_readiness_reasons':handoff['readiness_reasons'],
        'outputs':{'autoresearch_handoff':str(hp),'clinical_run_manifest':str(rp)},
    }
    (out/'v1_finalization_summary.yaml').write_text(yaml.safe_dump(summary,sort_keys=False),encoding='utf-8')
    print(yaml.safe_dump(summary,sort_keys=False))
if __name__=='__main__': main()
