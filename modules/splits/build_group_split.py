from __future__ import annotations
import argparse
from pathlib import Path
import pandas as pd, yaml
from sklearn.model_selection import train_test_split


def build(df, group_col, label_col=None, seed=42, ratios=(0.7,0.1,0.2)):
    if abs(sum(ratios)-1)>1e-8: raise ValueError('ratios must sum to 1')
    if group_col not in df: raise ValueError(f'missing group column: {group_col}')
    g=df[[group_col]+([label_col] if label_col else [])].drop_duplicates().copy()
    if label_col:
        nlabels=df.groupby(group_col)[label_col].nunique(dropna=True)
        bad=nlabels[nlabels>1]
        if len(bad): raise ValueError(f'{len(bad)} groups have conflicting labels')
        g=df.groupby(group_col,as_index=False)[label_col].first()
    groups=g[group_col].astype(str).to_numpy(); strat=g[label_col].to_numpy() if label_col else None
    warnings=[]
    try:
        tr_groups,tmp_groups,tr_y,tmp_y=train_test_split(groups,strat,test_size=ratios[1]+ratios[2],random_state=seed,stratify=strat)
        rel_test=ratios[2]/(ratios[1]+ratios[2])
        va_groups,te_groups=train_test_split(tmp_groups,test_size=rel_test,random_state=seed,stratify=tmp_y if label_col else None)
    except ValueError as e:
        warnings.append(f'stratified_split_fallback:{e}')
        tr_groups,tmp_groups=train_test_split(groups,test_size=ratios[1]+ratios[2],random_state=seed)
        rel_test=ratios[2]/(ratios[1]+ratios[2])
        va_groups,te_groups=train_test_split(tmp_groups,test_size=rel_test,random_state=seed)
    sets={'train':set(tr_groups),'val':set(va_groups),'test':set(te_groups)}
    out=df.copy(); out['split']=out[group_col].astype(str).map(lambda x: next((k for k,v in sets.items() if x in v),'excluded'))
    overlaps={f'{a}_{b}':len(sets[a]&sets[b]) for i,a in enumerate(sets) for b in list(sets)[i+1:]}
    summary={'version':'GroupSplit-v2','group_col':group_col,'label_col':label_col,'seed':seed,'ratios':list(ratios),'group_counts':{k:len(v) for k,v in sets.items()},'group_overlap':overlaps,'warnings':warnings}
    if label_col:
        patient_view=out.drop_duplicates(group_col)
        summary['patient_label_counts']={s:{str(k):int(v) for k,v in sub[label_col].value_counts().items()} for s,sub in patient_view.groupby('split')}
    return out,summary


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('csv'); ap.add_argument('--group-col',required=True); ap.add_argument('--label-col'); ap.add_argument('--seed',type=int,default=42); ap.add_argument('--train-ratio',type=float,default=.7); ap.add_argument('--val-ratio',type=float,default=.1); ap.add_argument('--test-ratio',type=float,default=.2); ap.add_argument('--out-csv',required=True); ap.add_argument('--out-yaml',required=True); a=ap.parse_args()
    df=pd.read_csv(a.csv); out,s=build(df,a.group_col,a.label_col,a.seed,(a.train_ratio,a.val_ratio,a.test_ratio)); out.to_csv(a.out_csv,index=False); Path(a.out_yaml).write_text(yaml.safe_dump(s,sort_keys=False),encoding='utf-8')
if __name__=='__main__': main()
