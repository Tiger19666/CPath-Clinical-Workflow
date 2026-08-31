from __future__ import annotations
import argparse, copy, os, re
from pathlib import Path
import sys
SKILL_ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(SKILL_ROOT))
import yaml

PATH_KEYS={'path','root','output_path','checkpoint','repo','table','test_manifest','cohort_manifest','split_manifest'}


def _looks_abs_path(v):
    if not isinstance(v,str): return False
    return v.startswith('/') or bool(re.match(r'^[A-Za-z]:[\\/]',v))


def redact(obj, root_map=None):
    root_map=root_map or {}
    def walk(x,key=None):
        if isinstance(x,dict): return {k:walk(v,k) for k,v in x.items()}
        if isinstance(x,list): return [walk(v,key) for v in x]
        if _looks_abs_path(x):
            for real,token in root_map.items():
                real=str(real).rstrip('/')
                if x==real or x.startswith(real+'/'):
                    return token + x[len(real):]
            return f'<LOCAL_PATH>/{Path(x).name}'
        return x
    y=walk(copy.deepcopy(obj))
    if isinstance(y,dict):
        y.setdefault('public_export',{})['absolute_paths_redacted']=True
    return y


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('input'); ap.add_argument('-o','--output',required=True); ap.add_argument('--map',action='append',default=[],help='/real/root=<TOKEN>'); a=ap.parse_args()
    root_map={}
    for item in a.map:
        left,right=item.split('=',1); root_map[left]=right
    obj=yaml.safe_load(Path(a.input).read_text())
    Path(a.output).write_text(yaml.safe_dump(redact(obj,root_map),sort_keys=False),encoding='utf-8')
if __name__=='__main__': main()
