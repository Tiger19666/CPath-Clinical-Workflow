from __future__ import annotations
import argparse
from pathlib import Path
import yaml

READY = {"READY_TO_RUN"}
CONDITIONAL = {"CONDITIONAL_READY"}


def resolve(mode, intent, readiness, selected=False):
    if intent == "EXECUTE":
        intent_gate = {"status": "PASS", "reason": "explicit_execute_intent"}
    elif intent == "EXECUTE_SELECTED" and mode == "DISCOVERY" and selected:
        intent_gate = {"status": "PASS", "reason": "selected_task_approved"}
    else:
        intent_gate = {"status": "BLOCKED", "reason": f"intent={intent}"}

    if readiness in READY:
        readiness_gate = {"status": "PASS", "reason": "ready_to_run"}
    elif readiness in CONDITIONAL:
        readiness_gate = {"status": "CONDITIONAL", "reason": "conditions_pending"}
    else:
        readiness_gate = {"status": "BLOCKED", "reason": f"readiness={readiness}"}

    allowed = intent_gate["status"] == "PASS" and readiness_gate["status"] == "PASS"
    return {
        "version": "ExecutionPermission-v2-dual-gate",
        "allowed": allowed,
        "reason": "all_gates_pass" if allowed else "blocked_by_intent_or_readiness",
        "intent_gate": intent_gate,
        "readiness_gate": readiness_gate,
        "final_permission": {
            "allowed": allowed,
            "reason": "all_gates_pass" if allowed else "blocked_by_intent_or_readiness",
        },
    }


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--mode',required=True)
    ap.add_argument('--intent',required=True)
    ap.add_argument('--readiness',required=True)
    ap.add_argument('--selected',action='store_true')
    ap.add_argument('-o','--output',required=True)
    a=ap.parse_args()
    Path(a.output).write_text(yaml.safe_dump(resolve(a.mode,a.intent,a.readiness,a.selected),sort_keys=False),encoding='utf-8')

if __name__=='__main__': main()
