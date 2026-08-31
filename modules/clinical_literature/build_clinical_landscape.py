from __future__ import annotations
import argparse
from collections import Counter
from pathlib import Path
import yaml

ROLES = {"clinical_background", "clinical_standard", "pathology_ai", "external_validation", "dataset_benchmark"}


def build(task: dict, verification: dict, references: dict) -> dict:
    verified = {x.get("reference_id") for x in (verification.get("references") or []) if x.get("verification_status") == "VERIFIED"}
    items = []
    counts = Counter()
    for r in references.get("references") or []:
        rid = r.get("reference_id")
        if rid not in verified:
            continue
        roles = [x for x in (r.get("evidence_roles") or []) if x in ROLES]
        for role in roles:
            counts[role] += 1
        items.append({"reference_id": rid, "evidence_roles": roles, "key_takeaway": r.get("key_takeaway")})
    return {
        "version": "ClinicalLandscape-v1",
        "task_id": task.get("task_id"),
        "clinical_question": task.get("clinical_question"),
        "verified_reference_count": len(items),
        "evidence_role_counts": dict(counts),
        "verified_evidence": items,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("task_yaml")
    ap.add_argument("verification_yaml")
    ap.add_argument("references_yaml")
    ap.add_argument("-o", "--output", required=True)
    a = ap.parse_args()
    task = yaml.safe_load(Path(a.task_yaml).read_text(encoding="utf-8"))
    ver = yaml.safe_load(Path(a.verification_yaml).read_text(encoding="utf-8"))
    refs = yaml.safe_load(Path(a.references_yaml).read_text(encoding="utf-8"))
    Path(a.output).write_text(yaml.safe_dump(build(task, ver, refs), sort_keys=False), encoding="utf-8")


if __name__ == "__main__":
    main()
