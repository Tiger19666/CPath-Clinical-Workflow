from __future__ import annotations
import argparse, subprocess, sys
from pathlib import Path
import yaml
ROOT=Path(__file__).resolve().parents[1]


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--cohort-split',required=True); ap.add_argument('--feature-root',required=True); ap.add_argument('--feature-qc',required=True); ap.add_argument('--permission',required=True); ap.add_argument('--output-dir',required=True); ap.add_argument('--baselines',nargs='+',default=['mean_pooling','abmil']); ap.add_argument('--epochs',type=int,default=30); ap.add_argument('--execute',action='store_true'); a=ap.parse_args()
    perm=yaml.safe_load(Path(a.permission).read_text()); allowed=(perm.get('final_permission') or perm).get('allowed',False)
    qc=yaml.safe_load(Path(a.feature_qc).read_text()); qc_pass=qc.get('status')=='PASS'
    out=Path(a.output_dir); out.mkdir(parents=True,exist_ok=True)
    plan=[]
    for b in a.baselines:
        cmd=[sys.executable,str(ROOT/'adapters/mil/train_patient_mil.py'),'--cohort',a.cohort_split,'--feature-root',a.feature_root,'--baseline',b,'--epochs',str(a.epochs),'--output-dir',str(out/b)]
        plan.append({'baseline':b,'argv':cmd})
    gate={'permission_pass':allowed,'feature_qc_pass':qc_pass,'allowed':allowed and qc_pass}
    (out/'baseline_execution_plan.yaml').write_text(yaml.safe_dump({'gate':gate,'plan':plan},sort_keys=False),encoding='utf-8')
    if not gate['allowed']:
        print(yaml.safe_dump({'status':'BLOCKED_GATE','gate':gate,'plan':plan},sort_keys=False)); return
    if not a.execute:
        print(yaml.safe_dump({'status':'DRY_RUN','gate':gate,'plan':plan},sort_keys=False)); return
    results={}
    for rec in plan:
        p=subprocess.run(rec['argv']); results[rec['baseline']]={'returncode':p.returncode,'status':'PASS' if p.returncode==0 else 'FAIL'}
        if p.returncode!=0: break
    (out/'baseline_run_summary.yaml').write_text(yaml.safe_dump(results,sort_keys=False),encoding='utf-8')
    print(yaml.safe_dump(results,sort_keys=False))
if __name__=='__main__': main()
