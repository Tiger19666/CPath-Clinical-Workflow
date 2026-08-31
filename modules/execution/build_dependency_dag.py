from __future__ import annotations
from collections import defaultdict


def build(tasks):
    nodes=[]; edges=[]; groups=defaultdict(list)
    for t in tasks:
        tid=t['task_id']; nodes.append({'id':tid,'type':'task'})
        rep=t.get('representation_key')
        if rep: groups[rep].append(tid)
    for rep,tids in sorted(groups.items()):
        rid=rep if str(rep).startswith('REP::') else f'REP::{rep}'
        nodes.append({'id':rid,'type':'shared_representation'})
        for tid in tids: edges.append({'from':rid,'to':tid})
    return {'nodes':nodes,'edges':edges,'shared_representation_groups':dict(groups)}
