from __future__ import annotations

def assess(task, data_ready=True, environment_ready=True):
    blockers=[]; conditions=[]
    if task.get('status') in {'NO_GO','REDIRECT'}: blockers.append('task_status_not_runnable')
    if not data_ready: blockers.append('data_not_ready')
    if task.get('dependencies'): conditions.extend(task['dependencies'])
    if not environment_ready: conditions.append('environment_or_dependency_not_ready')
    if blockers: status='NOT_READY'
    elif conditions: status='CONDITIONAL_READY'
    else: status='READY_TO_RUN'
    return {'task_id':task.get('task_id'),'readiness':status,'blockers':blockers,'conditions':conditions}
