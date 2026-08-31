from __future__ import annotations
import argparse, subprocess, time
from pathlib import Path
import yaml


def run(contract, phase, permission, execute=False, sanity_result=None):
    final=(permission.get('final_permission') or permission)
    if not final.get('allowed',False):
        return {'status':'BLOCKED_PERMISSION','phase':phase,'returncode':None,'elapsed_sec':0}
    if phase=='full':
        if not sanity_result or sanity_result.get('status')!='PASS':
            return {'status':'BLOCKED_SANITY','phase':phase,'reason':'full batch requires recorded sanity PASS','returncode':None,'elapsed_sec':0}
    cmd=(contract.get('commands') or {}).get(phase)
    if not cmd: return {'status':'BLOCKED_CONFIG','phase':phase,'returncode':None,'elapsed_sec':0}
    if not execute: return {'status':'DRY_RUN','phase':phase,'cwd':cmd['cwd'],'argv':cmd['argv'],'returncode':None,'elapsed_sec':0}
    t=time.time(); p=subprocess.run(cmd['argv'],cwd=cmd['cwd']); return {'status':'PASS' if p.returncode==0 else 'FAIL','phase':phase,'cwd':cmd['cwd'],'argv':cmd['argv'],'returncode':p.returncode,'elapsed_sec':round(time.time()-t,2)}


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--contract',required=True); ap.add_argument('--permission',required=True); ap.add_argument('--phase',choices=['sanity','full'],required=True); ap.add_argument('--sanity-result'); ap.add_argument('--execute',action='store_true'); ap.add_argument('-o','--output',required=True); a=ap.parse_args()
    c=yaml.safe_load(Path(a.contract).read_text()); p=yaml.safe_load(Path(a.permission).read_text()); sr=yaml.safe_load(Path(a.sanity_result).read_text()) if a.sanity_result and Path(a.sanity_result).exists() else None
    obj=run(c,a.phase,p,a.execute,sr); Path(a.output).write_text(yaml.safe_dump(obj,sort_keys=False),encoding='utf-8')
if __name__=='__main__': main()
