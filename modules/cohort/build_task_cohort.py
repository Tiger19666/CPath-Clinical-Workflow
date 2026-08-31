from __future__ import annotations
import argparse, re
from pathlib import Path
import pandas as pd, yaml

TCGA_RE=re.compile(r'^(TCGA-[A-Za-z0-9]{2}-[A-Za-z0-9]{4})')

def parse_patient_id(name, parser='tcga_patient'):
    if parser=='tcga_patient':
        m=TCGA_RE.match(Path(name).name)
        return m.group(1) if m else None
    if parser=='stem': return Path(name).stem
    raise ValueError(f'unsupported patient parser: {parser}')


def _resolve_patient_labels(df, patient_col, label_col):
    rows=[]; conflicts=[]
    for pid,g in df.groupby(patient_col,dropna=False):
        vals=[str(v).strip() for v in g[label_col].tolist() if str(v).strip() and str(v).lower()!='nan']
        uniq=sorted(set(vals))
        if not pid or str(pid).lower()=='nan': continue
        if len(uniq)==1: rows.append((str(pid),uniq[0]))
        elif len(uniq)>1: conflicts.append({'patient_id':str(pid),'labels':uniq})
    return dict(rows), conflicts


def build(config):
    slide_dir=Path(config['slides']['root'])
    exts={x.lower() for x in config['slides'].get('extensions',['.svs','.tif','.tiff','.ndpi','.mrxs'])}
    recursive=bool(config['slides'].get('recursive',False))
    files=(slide_dir.rglob('*') if recursive else slide_dir.iterdir())
    slide_paths=sorted(p for p in files if p.is_file() and p.suffix.lower() in exts)
    parser=config['slides'].get('patient_parser','tcga_patient')

    tab=config['labels']
    sep=tab.get('sep','\t')
    cdf=pd.read_csv(tab['table'],sep=sep,dtype=str).fillna('')
    label_by_patient, conflicts=_resolve_patient_labels(cdf,tab['patient_col'],tab['label_col'])
    mapping=tab.get('mapping') or {}
    exclude_unmapped=bool(tab.get('exclude_unmapped',True))

    records=[]; excluded=[]
    for sp in slide_paths:
        pid=parse_patient_id(sp.name,parser)
        if not pid:
            excluded.append({'slide_path':str(sp),'reason':'patient_id_unresolved'}); continue
        raw=label_by_patient.get(pid)
        if raw is None:
            excluded.append({'slide_path':str(sp),'patient_id':pid,'reason':'label_missing'}); continue
        mapped=mapping.get(raw, raw if not mapping else None)
        if mapped is None and exclude_unmapped:
            excluded.append({'slide_path':str(sp),'patient_id':pid,'raw_label':raw,'reason':'label_unmapped'}); continue
        records.append({'patient_id':pid,'slide_id':sp.stem,'slide_path':str(sp),'raw_label':raw,'label':mapped})
    out=pd.DataFrame(records)
    if not out.empty:
        labels=sorted(out['label'].dropna().unique().tolist())
        label_to_id={x:i for i,x in enumerate(labels)}
        out['label_id']=out['label'].map(label_to_id)
    else:
        label_to_id={}
    summary={
        'version':'TaskCohort-v1',
        'slide_root':str(slide_dir),
        'clinical_table':str(tab['table']),
        'label_column':tab['label_col'],
        'slides_included':int(len(out)),
        'patients_included':int(out['patient_id'].nunique()) if not out.empty else 0,
        'label_to_id':label_to_id,
        'patient_label_counts':({str(k):int(v) for k,v in out.drop_duplicates('patient_id')['label'].value_counts().items()} if not out.empty else {}),
        'excluded_slides':len(excluded),
        'clinical_label_conflicts':conflicts[:100],
        'clinical_label_conflict_count':len(conflicts),
    }
    return out,pd.DataFrame(excluded),summary


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('config'); ap.add_argument('--out-csv',required=True); ap.add_argument('--excluded-csv',required=True); ap.add_argument('--summary-yaml',required=True); a=ap.parse_args()
    cfg=yaml.safe_load(Path(a.config).read_text())
    out,exc,s=build(cfg)
    Path(a.out_csv).parent.mkdir(parents=True,exist_ok=True); out.to_csv(a.out_csv,index=False); exc.to_csv(a.excluded_csv,index=False)
    Path(a.summary_yaml).write_text(yaml.safe_dump(s,sort_keys=False,allow_unicode=True),encoding='utf-8')
if __name__=='__main__': main()
