from __future__ import annotations
import argparse, hashlib
from pathlib import Path
import yaml


def sha256_path(path: str | Path) -> str | None:
    p=Path(path)
    if not p.exists() or not p.is_file():
        return None
    h=hashlib.sha256()
    with p.open('rb') as f:
        for chunk in iter(lambda: f.read(1024*1024), b''):
            h.update(chunk)
    return h.hexdigest()


def register(artifact_id, output_path, inputs, producer=None):
    return {
        'artifact_id': artifact_id,
        'output_path': str(output_path),
        'output_hash': sha256_path(output_path),
        'producer': producer,
        'inputs': {name: {'path': str(path), 'hash': sha256_path(path)} for name,path in inputs.items()},
        'state': 'FRESH',
    }


def audit(manifest):
    artifacts=manifest.get('artifacts',{})
    states={}
    # direct file/input staleness
    for aid,rec in artifacts.items():
        if not Path(rec.get('output_path','')).exists():
            states[aid]={'state':'MISSING','reasons':['output_missing']}
            continue
        reasons=[]
        for name,inp in (rec.get('inputs') or {}).items():
            cur=sha256_path(inp.get('path',''))
            if cur != inp.get('hash'):
                reasons.append(f'input_changed:{name}')
        if sha256_path(rec['output_path']) != rec.get('output_hash'):
            reasons.append('output_changed_outside_registered_run')
        states[aid]={'state':'STALE' if reasons else 'FRESH','reasons':reasons}
    # dependency propagation
    changed=True
    while changed:
        changed=False
        for aid,rec in artifacts.items():
            if states.get(aid,{}).get('state') in {'MISSING','STALE'}:
                continue
            deps=rec.get('artifact_dependencies') or []
            bad=[d for d in deps if states.get(d,{}).get('state') in {'MISSING','STALE'}]
            if bad:
                states[aid]={'state':'STALE','reasons':[f'upstream_stale:{d}' for d in bad]}
                changed=True
    return {'version':'ArtifactState-v1','artifacts':states,'all_fresh':all(x['state']=='FRESH' for x in states.values())}


def main():
    ap=argparse.ArgumentParser(); sub=ap.add_subparsers(dest='cmd',required=True)
    a=sub.add_parser('audit'); a.add_argument('manifest'); a.add_argument('-o','--output',required=True)
    args=ap.parse_args()
    obj=yaml.safe_load(Path(args.manifest).read_text())
    Path(args.output).write_text(yaml.safe_dump(audit(obj),sort_keys=False),encoding='utf-8')
if __name__=='__main__': main()
