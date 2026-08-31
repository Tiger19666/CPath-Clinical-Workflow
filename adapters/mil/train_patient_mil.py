from __future__ import annotations
import argparse, json, os, random
from collections import defaultdict
from pathlib import Path
import h5py, numpy as np, pandas as pd, torch, torch.nn as nn
from sklearn.metrics import accuracy_score, balanced_accuracy_score, f1_score, roc_auc_score, average_precision_score


def set_seed(seed):
    random.seed(seed); np.random.seed(seed); torch.manual_seed(seed)
    if torch.cuda.is_available(): torch.cuda.manual_seed_all(seed)


def load_bag(fp, max_patches, seed):
    with h5py.File(fp,'r') as f: x=np.asarray(f['features'],dtype=np.float32)
    if len(x)>max_patches:
        rng=np.random.default_rng(seed); idx=np.sort(rng.choice(len(x),max_patches,replace=False)); x=x[idx]
    return torch.from_numpy(x)

class PatientDataset:
    def __init__(self, df, root, split, max_patches, seed):
        self.df=df[df['split']==split].copy(); self.root=Path(root); self.max_patches=max_patches; self.seed=seed
        self.groups=[]
        for pid,g in self.df.groupby('patient_id'):
            labels=g['label_id'].unique()
            if len(labels)!=1: raise ValueError(f'patient {pid} has conflicting labels')
            fps=[self.root/f'{sid}.h5' for sid in g['slide_id'].astype(str)]
            missing=[str(x) for x in fps if not x.exists()]
            if missing: raise FileNotFoundError(f'missing features for patient {pid}: {missing[:3]}')
            self.groups.append((str(pid),int(labels[0]),fps))
    def __len__(self): return len(self.groups)
    def get(self,i):
        pid,y,fps=self.groups[i]
        bags=[load_bag(fp,self.max_patches,self.seed+i*1000+j) for j,fp in enumerate(fps)]
        return pid,y,bags

class ABMIL(nn.Module):
    def __init__(self,d,nc,hidden=256,attn=128,mode='abmil'):
        super().__init__(); self.mode=mode
        self.proj=nn.Sequential(nn.Linear(d,hidden),nn.ReLU())
        self.attn=nn.Sequential(nn.Linear(hidden,attn),nn.Tanh(),nn.Linear(attn,1))
        self.cls=nn.Linear(hidden,nc)
    def slide_embed(self,x):
        h=self.proj(x)
        if self.mode=='mean_pooling': return h.mean(0)
        a=torch.softmax(self.attn(h).squeeze(-1),dim=0); return (a[:,None]*h).sum(0)
    def forward(self,bags):
        zs=[self.slide_embed(x) for x in bags]
        z=torch.stack(zs,0).mean(0)
        return self.cls(z)

def metrics(y,prob):
    y=np.asarray(y); prob=np.asarray(prob); pred=prob.argmax(1)
    out={'accuracy':float(accuracy_score(y,pred)),'balanced_accuracy':float(balanced_accuracy_score(y,pred)),'macro_f1':float(f1_score(y,pred,average='macro'))}
    try:
        if prob.shape[1]==2:
            out['auroc']=float(roc_auc_score(y,prob[:,1])); out['auprc']=float(average_precision_score(y,prob[:,1]))
        else:
            out['auroc_macro_ovr']=float(roc_auc_score(y,prob,multi_class='ovr',average='macro'))
    except ValueError: pass
    return out

def infer(model,ds,device):
    model.eval(); ys=[]; ps=[]; pids=[]
    with torch.no_grad():
        for i in range(len(ds)):
            pid,y,bags=ds.get(i); bags=[x.to(device) for x in bags]; logits=model(bags); prob=torch.softmax(logits,0).cpu().numpy(); ys.append(y); ps.append(prob); pids.append(pid)
    return pids,ys,np.stack(ps) if ps else np.zeros((0,1))

def train(args):
    set_seed(args.seed); df=pd.read_csv(args.cohort); root=Path(args.feature_root)
    first=next(root.glob('*.h5'),None)
    if first is None: raise FileNotFoundError(f'no h5 features in {root}')
    with h5py.File(first,'r') as f: d=int(f['features'].shape[1])
    nc=int(df['label_id'].max())+1; device=torch.device(args.device if args.device!='auto' else ('cuda' if torch.cuda.is_available() else 'cpu'))
    tr=PatientDataset(df,root,'train',args.max_patches_per_slide,args.seed); va=PatientDataset(df,root,'val',args.max_patches_per_slide,args.seed+1); te=PatientDataset(df,root,'test',args.max_patches_per_slide,args.seed+2)
    model=ABMIL(d,nc,args.hidden_dim,args.attn_dim,args.baseline).to(device)
    counts=df[df.split=='train'].drop_duplicates('patient_id')['label_id'].value_counts().sort_index(); weights=np.ones(nc,dtype=np.float32)
    for i in range(nc): weights[i]=len(counts)/(nc*max(int(counts.get(i,1)),1))
    loss_fn=nn.CrossEntropyLoss(weight=torch.tensor(weights,device=device)); opt=torch.optim.AdamW(model.parameters(),lr=args.lr,weight_decay=args.weight_decay)
    best=-1e18; best_state=None; patience=0; history=[]
    for epoch in range(1,args.epochs+1):
        model.train(); order=np.random.default_rng(args.seed+epoch).permutation(len(tr)); losses=[]
        for i in order:
            _,y,bags=tr.get(int(i)); bags=[x.to(device) for x in bags]; opt.zero_grad(); logits=model(bags); loss=loss_fn(logits[None,:],torch.tensor([y],device=device)); loss.backward(); opt.step(); losses.append(float(loss.item()))
        _,vy,vp=infer(model,va,device); vm=metrics(vy,vp) if len(vy) else {}; score=vm.get('auroc',vm.get('macro_f1',-1e9))
        history.append({'epoch':epoch,'train_loss':float(np.mean(losses)) if losses else None,'val':vm})
        if score>best+1e-8: best=score; best_state={k:v.detach().cpu().clone() for k,v in model.state_dict().items()}; patience=0
        else: patience+=1
        if patience>=args.patience: break
    if best_state: model.load_state_dict(best_state)
    out=Path(args.output_dir); out.mkdir(parents=True,exist_ok=True); torch.save({'state_dict':model.state_dict(),'feature_dim':d,'num_classes':nc,'baseline':args.baseline,'seed':args.seed},out/'best.pt')
    results={}
    for split,ds in [('val',va),('test',te)]:
        pids,ys,ps=infer(model,ds,device); mm=metrics(ys,ps) if len(ys) else {}; results[split]=mm
        rows=[]
        for pid,y,p in zip(pids,ys,ps): rows.append({'patient_id':pid,'label_id':y,'prediction':int(np.argmax(p)),**{f'prob_{i}':float(v) for i,v in enumerate(p)}})
        pd.DataFrame(rows).to_csv(out/f'{split}_predictions.csv',index=False)
    meta={'baseline':args.baseline,'device':str(device),'feature_dim':d,'num_classes':nc,'n_train':len(tr),'n_val':len(va),'n_test':len(te),'seed':args.seed,'history':history,'metrics':results}
    (out/'metrics.json').write_text(json.dumps(meta,indent=2)); return meta

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--cohort',required=True); ap.add_argument('--feature-root',required=True); ap.add_argument('--baseline',choices=['mean_pooling','abmil'],default='abmil'); ap.add_argument('--epochs',type=int,default=30); ap.add_argument('--patience',type=int,default=5); ap.add_argument('--lr',type=float,default=1e-4); ap.add_argument('--weight-decay',type=float,default=1e-4); ap.add_argument('--hidden-dim',type=int,default=256); ap.add_argument('--attn-dim',type=int,default=128); ap.add_argument('--max-patches-per-slide',type=int,default=2048); ap.add_argument('--seed',type=int,default=42); ap.add_argument('--device',default='auto'); ap.add_argument('--output-dir',required=True); a=ap.parse_args(); train(a)
if __name__=='__main__': main()
