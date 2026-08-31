from __future__ import annotations
import argparse
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import yaml
from modules.router.route_request import route
from modules.study.build_cohort_registry import build as build_cohort_registry


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('request_yaml'); ap.add_argument('workspace'); a=ap.parse_args()
    req=yaml.safe_load(Path(a.request_yaml).read_text()); req=route(req)
    root=Path(a.workspace)
    (root/'shared'/'representations').mkdir(parents=True,exist_ok=True)
    (root/'shared'/'cohorts').mkdir(parents=True,exist_ok=True)
    (root/'tasks').mkdir(exist_ok=True)
    (root/'runs').mkdir(exist_ok=True)
    (root/'exports').mkdir(exist_ok=True)
    (root/'request_spec.yaml').write_text(yaml.safe_dump(req,sort_keys=False),encoding='utf-8')
    for name in ['dataset_manifest.yaml','entity_graph.yaml','linkage_manifest.yaml','data_quality.yaml','environment_report.yaml','artifact_state.yaml']:
        (root/'shared'/name).write_text('{}\n',encoding='utf-8')
    cohorts=req.get('cohorts') or []
    if cohorts:
        (root/'shared'/'cohort_registry.yaml').write_text(yaml.safe_dump(build_cohort_registry(cohorts),sort_keys=False),encoding='utf-8')
    else:
        (root/'shared'/'cohort_registry.yaml').write_text(yaml.safe_dump({'version':'CohortRegistry-v1','cohort_count':0,'cohorts':[],'default_pooling_policy':'DO_NOT_POOL_WITHOUT_EXPLICIT_COMPATIBILITY_AND_PERMISSION'},sort_keys=False),encoding='utf-8')
    (root/'task_portfolio.yaml').write_text('tasks: []\n',encoding='utf-8')
    print(root)
if __name__=='__main__': main()
