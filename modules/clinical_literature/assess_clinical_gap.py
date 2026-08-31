from __future__ import annotations
import argparse
from pathlib import Path
import yaml


def assess(task: dict, coverage: dict, landscape: dict) -> dict:
    counts = landscape.get("evidence_role_counts") or {}
    has_clinical = (counts.get("clinical_background", 0) + counts.get("clinical_standard", 0)) > 0
    has_ai = counts.get("pathology_ai", 0) > 0
    has_validation = counts.get("external_validation", 0) > 0
    cov_pass = coverage.get("status") == "PASS"
    issues = []
    if not cov_pass: issues.append("literature_search_coverage_incomplete")
    if not has_clinical: issues.append("clinical_context_not_verified")
    if not has_ai: issues.append("pathology_ai_landscape_not_verified")
    if not has_validation: issues.append("external_validation_landscape_sparse_or_unverified")
    literature_status = "READY" if not issues else "CONDITIONAL"
    original = task.get("status", "CONDITIONAL_GO")
    recommended = original
    if original == "GO" and literature_status != "READY":
        recommended = "CONDITIONAL_GO"
    return {
        "version": "ClinicalGapAssessment-v1",
        "task_id": task.get("task_id"),
        "literature_readiness": literature_status,
        "issues": issues,
        "original_task_status": original,
        "recommended_task_status": recommended,
        "clinical_gap_confidence_ceiling": coverage.get("clinical_gap_confidence_ceiling", "LOW"),
        "note": "This module assesses clinical evidence readiness, not algorithmic novelty.",
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("task_yaml")
    ap.add_argument("coverage_yaml")
    ap.add_argument("landscape_yaml")
    ap.add_argument("-o", "--output", required=True)
    a = ap.parse_args()
    task = yaml.safe_load(Path(a.task_yaml).read_text(encoding="utf-8"))
    cov = yaml.safe_load(Path(a.coverage_yaml).read_text(encoding="utf-8"))
    land = yaml.safe_load(Path(a.landscape_yaml).read_text(encoding="utf-8"))
    Path(a.output).write_text(yaml.safe_dump(assess(task, cov, land), sort_keys=False), encoding="utf-8")


if __name__ == "__main__":
    main()
