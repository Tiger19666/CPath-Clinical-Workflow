from __future__ import annotations
import argparse
from pathlib import Path
import pandas as pd, yaml

def read_table(path):
    p=Path(path)
    if p.suffix.lower()=='.csv': return pd.read_csv(p)
    if p.suffix.lower()=='.tsv': return pd.read_csv(p,sep='\t')
    if p.suffix.lower() in {'.xlsx','.xls'}: return pd.read_excel(p)
    raise ValueError('supported: csv/tsv/xlsx/xls')

def profile(path, max_unique=30):
    df=read_table(path); cols={}
    for c in df.columns:
        s=df[c]; non=int(s.notna().sum()); uniq=int(s.nunique(dropna=True))
        item={'non_missing':non,'missing':int(len(s)-non),'coverage':round(non/max(1,len(s)),4),'unique':uniq,'dtype':str(s.dtype)}
        if uniq<=max_unique:
            item['value_counts']={str(k):int(v) for k,v in s.value_counts(dropna=False).head(max_unique).items()}
        cols[str(c)]=item
    return {'path':str(path),'rows':len(df),'columns':cols}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('table'); ap.add_argument('-o','--output',required=True); a=ap.parse_args()
    Path(a.output).write_text(yaml.safe_dump(profile(a.table),sort_keys=False,allow_unicode=True),encoding='utf-8')
if __name__=='__main__': main()
