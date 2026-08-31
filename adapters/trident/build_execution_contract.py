from __future__ import annotations
import argparse, csv
from pathlib import Path
import pandas as pd, yaml


def build(task_cohort_csv, fm_resolution, local, output_root, feature_store_id, gpus=None):
    cohort=pd.read_csv(task_cohort_csv)
    if cohort.empty: raise ValueError('empty task cohort')
    selected=fm_resolution.get('selected')
    if not selected: return {'version':'TridentExecution-v1','status':'BLOCKED_DEPENDENCY','reason':'no usable foundation model','commands':{}}
    tr=((local.get('resources') or {}).get('trident') or {})
    repo=tr.get('repo'); py=tr.get('python') or 'python'
    if not repo or not Path(repo).exists(): return {'version':'TridentExecution-v1','status':'BLOCKED_DEPENDENCY','reason':'TRIDENT repo unresolved','commands':{}}
    repo=Path(repo); single=repo/'run_single_slide.py'; batch=repo/'run_batch_of_slides.py'
    if not single.exists() or not batch.exists(): return {'version':'TridentExecution-v1','status':'BLOCKED_DEPENDENCY','reason':'TRIDENT entrypoints missing','commands':{}}
    wsi_root=Path(cohort.iloc[0]['slide_path']).parent
    if any(Path(x).parent != wsi_root for x in cohort['slide_path']):
        return {'version':'TridentExecution-v1','status':'BLOCKED_CONFIG','reason':'v0.2 batch contract requires a single WSI root','commands':{}}
    out_root=Path(output_root); out_root.mkdir(parents=True,exist_ok=True)
    custom_list=out_root/'cohort_wsis.csv'
    rels=[Path(x).name for x in cohort['slide_path']]
    pd.DataFrame({'wsi':rels}).drop_duplicates().to_csv(custom_list,index=False)
    tri=selected['trident']; enc=tri['patch_encoder']; mag=tri['magnification']; ps=tri['patch_size']
    ckpt=selected.get('checkpoint')
    job=out_root/'trident_job'
    common=['--job_dir',str(job),'--patch_encoder',enc,'--mag',str(mag),'--patch_size',str(ps)]
    if ckpt: common += ['--patch_encoder_ckpt_path',ckpt]
    gpu_args=[]
    if gpus: gpu_args=['--gpus']+[str(x) for x in gpus]
    sanity=[py,str(single),'--slide_path',str(cohort.iloc[0]['slide_path'])]+common
    full=[py,str(batch),'--task','all','--wsi_dir',str(wsi_root),'--custom_list_of_wsis',str(custom_list)]+common+gpu_args+['--skip_errors']
    feature_dir=job/f"{mag:g}x_{ps}px_0px_overlap"/f"features_{enc}"
    return {'version':'TridentExecution-v1','status':'READY','feature_store_id':feature_store_id,'encoder':enc,'embedding_dim':selected.get('embedding_dim'),'wsi_root':str(wsi_root),'custom_wsi_list':str(custom_list),'job_dir':str(job),'feature_dir':str(feature_dir),'sanity_slide':str(cohort.iloc[0]['slide_path']),'commands':{'sanity':{'cwd':str(repo),'argv':sanity},'full':{'cwd':str(repo),'argv':full}}}


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--cohort',required=True); ap.add_argument('--fm-resolution',required=True); ap.add_argument('--local',required=True); ap.add_argument('--output-root',required=True); ap.add_argument('--feature-store-id',required=True); ap.add_argument('--gpus',nargs='*',type=int); ap.add_argument('-o','--output',required=True); a=ap.parse_args()
    fm=yaml.safe_load(Path(a.fm_resolution).read_text()); local=yaml.safe_load(Path(a.local).read_text()) if Path(a.local).exists() else {}
    obj=build(a.cohort,fm,local,a.output_root,a.feature_store_id,a.gpus)
    Path(a.output).write_text(yaml.safe_dump(obj,sort_keys=False),encoding='utf-8')
if __name__=='__main__': main()
