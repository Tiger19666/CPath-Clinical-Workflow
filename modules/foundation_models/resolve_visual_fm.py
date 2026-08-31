from __future__ import annotations
import argparse
from pathlib import Path
import yaml


def _resource_entry(local, key):
    fm=((local or {}).get('resources') or {}).get('foundation_models') or {}
    for k,v in fm.items():
        if k.lower()==key.lower(): return v or {}
    return {}


def resolve(registry, local, preferences, allow_remote=False):
    patch=registry.get('patch_encoders') or {}
    candidates=[]
    for key in preferences:
        if key not in patch: continue
        meta=patch[key]; loc=_resource_entry(local,key)
        ckpt=loc.get('checkpoint') or loc.get('weights')
        ckpt_exists=bool(ckpt and Path(ckpt).exists())
        access_verified=bool(loc.get('access_verified',False))
        if ckpt_exists:
            status='AVAILABLE_LOCAL'; usable=True
        elif allow_remote and access_verified:
            status='AVAILABLE_REMOTE_ALLOWED'; usable=True
        else:
            status='UNAVAILABLE_OR_UNVERIFIED'; usable=False
        candidates.append({'encoder_key':key,'display_name':meta.get('display_name'), 'status':status,'usable':usable,'checkpoint':str(ckpt) if ckpt else None,'embedding_dim':meta.get('embedding_dim'),'trident':meta.get('trident'),'license':meta.get('license'),'access':meta.get('access')})
    selected=next((x for x in candidates if x['usable']),None)
    return {'version':'VisualFMResolver-v1','selected':selected,'candidates':candidates,'allow_remote':bool(allow_remote),'status':'READY' if selected else 'NOT_READY'}


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--registry',required=True); ap.add_argument('--local',required=True); ap.add_argument('--prefer',nargs='+',default=['uni_v2','uni_v1']); ap.add_argument('--allow-remote',action='store_true'); ap.add_argument('-o','--output',required=True); a=ap.parse_args()
    reg=yaml.safe_load(Path(a.registry).read_text()); local=yaml.safe_load(Path(a.local).read_text()) if Path(a.local).exists() else {}
    Path(a.output).write_text(yaml.safe_dump(resolve(reg,local,a.prefer,a.allow_remote),sort_keys=False),encoding='utf-8')
if __name__=='__main__': main()
