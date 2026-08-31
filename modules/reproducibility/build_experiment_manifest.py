from __future__ import annotations
import argparse, hashlib, importlib, json, os, platform, subprocess, sys
from pathlib import Path
import yaml


def sha256_file(p: Path, chunk=1024*1024):
    h=hashlib.sha256()
    with p.open('rb') as f:
        while True:
            b=f.read(chunk)
            if not b: break
            h.update(b)
    return h.hexdigest()

def hash_path(path):
    p=Path(path)
    if not p.exists(): return {'path':str(p),'exists':False}
    if p.is_file(): return {'path':str(p),'exists':True,'kind':'file','sha256':sha256_file(p),'size_bytes':p.stat().st_size}
    h=hashlib.sha256(); files=[]
    for fp in sorted(x for x in p.rglob('*') if x.is_file() and '__pycache__' not in x.parts):
        rel=str(fp.relative_to(p)); digest=sha256_file(fp); files.append({'relative_path':rel,'sha256':digest,'size_bytes':fp.stat().st_size}); h.update((rel+'\0'+digest+'\n').encode())
    return {'path':str(p),'exists':True,'kind':'directory','sha256':h.hexdigest(),'file_count':len(files),'files':files}

def _version(name):
    try: return str(importlib.import_module(name).__version__)
    except Exception: return None

def _git(path):
    p=Path(path)
    try:
        root=subprocess.check_output(['git','-C',str(p),'rev-parse','--show-toplevel'],stderr=subprocess.DEVNULL,text=True).strip()
        commit=subprocess.check_output(['git','-C',root,'rev-parse','HEAD'],stderr=subprocess.DEVNULL,text=True).strip()
        dirty=bool(subprocess.check_output(['git','-C',root,'status','--porcelain'],stderr=subprocess.DEVNULL,text=True).strip())
        return {'root':root,'commit':commit,'dirty':dirty}
    except Exception: return {'root':None,'commit':None,'dirty':None}

def build(task_id, run_scope, inputs=None, outputs=None, skill_root=None, seed=None, extra=None):
    env={'python':sys.version.split()[0],'platform':platform.platform(),'packages':{k:_version(k) for k in ['numpy','pandas','scipy','sklearn','torch','h5py','yaml']}}
    if env['packages'].get('yaml') is None:
        try: env['packages']['pyyaml']=__import__('yaml').__version__
        except Exception: pass
    skill={'version':None,'git':None}
    if skill_root:
        sr=Path(skill_root); vf=sr/'VERSION'; skill['version']=vf.read_text().strip() if vf.exists() else None; skill['git']=_git(sr)
    return {'status':'FROZEN','task_id':task_id,'run_scope':run_scope,'seed':seed,'skill':skill,'environment':env,
            'inputs':{Path(p).name:hash_path(p) for p in (inputs or [])},'outputs':{Path(p).name:hash_path(p) for p in (outputs or [])},'extra':extra or {}}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--task-id',required=True); ap.add_argument('--run-scope',required=True); ap.add_argument('--inputs',nargs='*'); ap.add_argument('--outputs',nargs='*'); ap.add_argument('--skill-root'); ap.add_argument('--seed',type=int); ap.add_argument('-o','--output',required=True)
    a=ap.parse_args(); out=build(a.task_id,a.run_scope,a.inputs,a.outputs,a.skill_root,a.seed)
    p=Path(a.output); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(yaml.safe_dump(out,sort_keys=False,allow_unicode=True),encoding='utf-8')
if __name__=='__main__': main()
