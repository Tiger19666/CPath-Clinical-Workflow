from __future__ import annotations
import argparse
from pathlib import Path
import re
import yaml

ALLOWED_LEVELS = {
    "classification": {"patient", "case", "slide", "section", "roi", "patch", "cell"},
    "ordinal_classification": {"patient", "case", "slide", "section", "roi", "patch"},
    "regression": {"patient", "case", "slide", "section", "roi", "patch"},
    "survival": {"patient", "case"},
    "segmentation": {"pixel", "region", "mask"},
    "detection": {"object", "region", "cell"},
    "vqa": {"question", "image_question", "slide_question", "roi_question"},
    "report_generation": {"slide", "section", "roi", "patient"},
    "multimodal_prediction": {"patient", "case", "slide"},
}


def _looks_multi_target(target: object) -> bool:
    if isinstance(target, (list, tuple, set)):
        return len(target) != 1
    s = str(target or "").strip().lower()
    if not s:
        return False
    return bool(re.search(r"\s+or\s+|\||/", s))


def validate(task: dict) -> dict:
    errors = []
    warnings = []
    fam = str(task.get("task_family") or "").strip()
    level = str(task.get("prediction_level") or "").strip()
    if not str(task.get("clinical_question") or "").strip():
        errors.append("missing_clinical_question")
    if not str(task.get("target") or "").strip():
        errors.append("missing_target")
    if not str(task.get("label_source") or task.get("label_id") or "").strip():
        warnings.append("label_source_not_explicit")
    if _looks_multi_target(task.get("target")):
        errors.append("non_atomic_target")
    if fam not in ALLOWED_LEVELS:
        warnings.append("unregistered_task_family")
    elif level not in ALLOWED_LEVELS[fam]:
        errors.append(f"prediction_level_incompatible_with_{fam}")
    if task.get("targets") and len(task.get("targets")) != 1:
        errors.append("multiple_targets_in_single_task")
    status = "PASS" if not errors else "FAIL"
    return {"version": "ClinicalTaskSemanticValidator-v1", "task_id": task.get("task_id"), "status": status, "errors": errors, "warnings": warnings}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("task_yaml")
    ap.add_argument("-o", "--output", required=True)
    a = ap.parse_args()
    task = yaml.safe_load(Path(a.task_yaml).read_text(encoding="utf-8"))
    Path(a.output).write_text(yaml.safe_dump(validate(task), sort_keys=False), encoding="utf-8")


if __name__ == "__main__":
    main()
