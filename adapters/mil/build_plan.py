from __future__ import annotations

def build(task_id, baseline, config, local):
    res=(local.get('resources') or {}).get('mil_framework',{})
    ep=res.get('train_entrypoint'); repo=res.get('repo')
    if not ep: return {'status':'BLOCKED_DEPENDENCY','reason':'MIL train entrypoint unresolved','command':None}
    return {'status':'PLANNED','cwd':repo,'command':['python',ep,'--task-id',task_id,'--model',baseline,'--config',config]}
