from __future__ import annotations
import argparse, importlib.util, shutil, sys, platform
from pathlib import Path
import yaml

def has(mod): return importlib.util.find_spec(mod) is not None

def audit(path='.', local=None):
    torch_info={'installed':has('torch'),'cuda_available':False,'cuda_device_count':0}
    if torch_info['installed']:
        import torch
        torch_info.update(version=torch.__version__,cuda_available=torch.cuda.is_available(),cuda_device_count=torch.cuda.device_count())
    du=shutil.disk_usage(Path(path).resolve())
    deps={m:has(m) for m in ['openslide','h5py','pandas','sklearn','transformers']}
    res=((local or {}).get('resources') or {})
    tr=res.get('trident') or {}; tr_repo=tr.get('repo')
    trident={'repo':tr_repo,'repo_exists':bool(tr_repo and Path(tr_repo).exists()),'python':tr.get('python')}
    fms={}
    for name,entry in (res.get('foundation_models') or {}).items():
        ck=(entry or {}).get('checkpoint') or (entry or {}).get('weights'); fms[name]={'checkpoint':ck,'checkpoint_exists':bool(ck and Path(ck).exists()),'access_verified':bool((entry or {}).get('access_verified',False))}
    readiness='READY_TO_RUN' if torch_info['installed'] and deps.get('h5py') and deps.get('pandas') and trident['repo_exists'] else 'CONDITIONAL_READY'
    return {'version':'EnvironmentAudit-v2','python':sys.version.split()[0],'platform':platform.platform(),'torch':torch_info,'dependencies':deps,'disk_free_gb':round(du.free/1024**3,2),'executables':{'git':shutil.which('git'),'nvidia_smi':shutil.which('nvidia-smi')},'trident':trident,'foundation_models':fms,'readiness':readiness}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--path',default='.'); ap.add_argument('--local'); ap.add_argument('-o','--output',required=True); a=ap.parse_args(); local=yaml.safe_load(Path(a.local).read_text()) if a.local and Path(a.local).exists() else {}; Path(a.output).write_text(yaml.safe_dump(audit(a.path,local),sort_keys=False),encoding='utf-8')
if __name__=='__main__': main()
