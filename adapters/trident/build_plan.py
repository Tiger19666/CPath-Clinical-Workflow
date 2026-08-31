from __future__ import annotations

def build(config, local):
    repo=(local.get('resources') or {}).get('trident',{}).get('repo')
    py=(local.get('resources') or {}).get('trident',{}).get('python') or 'python'
    if not repo: return {'status':'BLOCKED_DEPENDENCY','reason':'TRIDENT repo unresolved','command':None}
    return {'status':'PLANNED','cwd':repo,'command':[py, config.get('entrypoint','run_batch_of_slides.py')]+list(config.get('args') or [])}
