from __future__ import annotations
import argparse
from pathlib import Path
import yaml

REQUIRED_FAMILIES = (
    "clinical_endpoint",
    "pathology_ai_landscape",
    "validation_landscape",
    "dataset_benchmark",
)


def _term(task: dict) -> str:
    target = str(task.get("target") or task.get("name") or "clinical endpoint").strip()
    disease = str(task.get("disease_context") or task.get("organ_context") or "").strip()
    return " ".join(x for x in (disease, target) if x).strip()


def build(task: dict) -> dict:
    base = _term(task)
    name = str(task.get("name") or base).strip()
    question = str(task.get("clinical_question") or "").strip()
    return {
        "version": "ClinicalLiteraturePlan-v1",
        "task_id": task.get("task_id"),
        "clinical_question": question,
        "required_query_families": list(REQUIRED_FAMILIES),
        "queries": [
            {
                "family": "clinical_endpoint",
                "query": f'{base} clinical guideline standard endpoint pathology',
                "purpose": "Define endpoint significance, reference standard, and clinically valid interpretation.",
                "preferred_sources": ["guideline", "PubMed", "official_clinical_source"],
            },
            {
                "family": "pathology_ai_landscape",
                "query": f'{base} H&E whole slide pathology AI prediction {name}',
                "purpose": "Map existing pathology-AI studies for this clinical task without doing algorithm novelty search.",
                "preferred_sources": ["PubMed", "publisher", "DOI"],
            },
            {
                "family": "validation_landscape",
                "query": f'{base} pathology AI external validation multicenter generalization',
                "purpose": "Determine validation expectations, external cohorts, and claim scope.",
                "preferred_sources": ["PubMed", "publisher", "DOI"],
            },
            {
                "family": "dataset_benchmark",
                "query": f'{base} computational pathology dataset benchmark cohort',
                "purpose": "Identify relevant public cohorts/benchmarks and realistic cohort-size expectations.",
                "preferred_sources": ["dataset_site", "PubMed", "publisher"],
            },
        ],
        "completion_rule": {
            "requires_real_search_trace": True,
            "requires_external_resolved_metadata": True,
            "self_declared_complete_is_invalid": True,
        },
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("task_yaml")
    ap.add_argument("-o", "--output", required=True)
    a = ap.parse_args()
    task = yaml.safe_load(Path(a.task_yaml).read_text(encoding="utf-8"))
    Path(a.output).write_text(yaml.safe_dump(build(task), sort_keys=False), encoding="utf-8")


if __name__ == "__main__":
    main()
