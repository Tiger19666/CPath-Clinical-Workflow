from __future__ import annotations
import argparse, hashlib
from pathlib import Path
import yaml


def hash_file(path):
    p=Path(path)
    if not p.exists(): return None
    h=hashlib.sha256()
    with p.open('rb') as f:
        for c in iter(lambda:f.read(1024*1024),b''): h.update(c)
    return h.hexdigest()

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--fm-resolution',required=True); ap.add_argument('--trident-contract',required=True); ap.add_argument('--feature-qc',required=True); ap.add_argument('--cohort-split',required=True); ap.add_argument('-o','--output',required=True); a=ap.parse_args()
    fm=yaml.safe_load(Path(a.fm_resolution).read_text()); tr=yaml.safe_load(Path(a.trident_contract).read_text()); qc=yaml.safe_load(Path(a.feature_qc).read_text()); sel=fm.get('selected') or {}
    if qc.get('status')!='PASS': raise SystemExit('feature QC must PASS before finalizing a primary store')
    ck=sel.get('checkpoint')
    obj={'version':'FeatureStore-v0.2','store_id':tr.get('feature_store_id'),'source_type':'foundation_model','status':'READY','encoder':sel.get('encoder_key'),'display_name':sel.get('display_name'),'embedding_dim':sel.get('embedding_dim'),'weights':{'checkpoint_path':ck,'sha256':hash_file(ck) if ck else None,'access_mode':sel.get('status')},'preprocessing_contract':{'magnification':(sel.get('trident') or {}).get('magnification'),'patch_size':(sel.get('trident') or {}).get('patch_size'),'overlap':0,'tool':'TRIDENT'},'feature_root':tr.get('feature_dir'),'cohort_split':str(a.cohort_split),'coverage':qc.get('coverage'),'provenance_status':'COMPLETE' if sel.get('encoder_key') and (ck or sel.get('status')=='AVAILABLE_REMOTE_ALLOWED') else 'PARTIAL'}
    Path(a.output).write_text(yaml.safe_dump(obj,sort_keys=False),encoding='utf-8')
if __name__=='__main__': main()
