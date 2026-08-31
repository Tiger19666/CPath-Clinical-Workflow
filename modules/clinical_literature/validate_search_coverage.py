from __future__ import annotations
import argparse
from pathlib import Path
import yaml
try:
    from .build_search_plan import REQUIRED_FAMILIES
except ImportError:
    from build_search_plan import REQUIRED_FAMILIES


def validate(trace: dict, min_screened: int = 1) -> dict:
    searches = trace.get("searches") or []
    by_family = {str(x.get("family")): x for x in searches if isinstance(x, dict)}
    details = {}
    complete = 0
    for fam in REQUIRED_FAMILIES:
        x = by_family.get(fam) or {}
        executed = x.get("executed") is True
        query_ok = bool(str(x.get("query") or "").strip())
        source_ok = bool(str(x.get("source") or "").strip())
        screened = int(x.get("results_screened") or 0)
        refs = x.get("selected_reference_ids") or []
        ok = executed and query_ok and source_ok and screened >= min_screened and bool(refs)
        details[fam] = {
            "complete": ok,
            "executed": executed,
            "query_present": query_ok,
            "source_present": source_ok,
            "results_screened": screened,
            "selected_reference_count": len(refs),
        }
        complete += int(ok)
    status = "PASS" if complete == len(REQUIRED_FAMILIES) else "INCOMPLETE"
    ceiling = "HIGH" if status == "PASS" else ("MEDIUM" if complete >= 2 else "LOW")
    return {
        "version": "ClinicalLiteratureCoverage-v1",
        "task_id": trace.get("task_id"),
        "status": status,
        "completed_families": complete,
        "required_families": len(REQUIRED_FAMILIES),
        "details": details,
        "clinical_gap_confidence_ceiling": ceiling,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("trace_yaml")
    ap.add_argument("-o", "--output", required=True)
    a = ap.parse_args()
    trace = yaml.safe_load(Path(a.trace_yaml).read_text(encoding="utf-8"))
    Path(a.output).write_text(yaml.safe_dump(validate(trace), sort_keys=False), encoding="utf-8")


if __name__ == "__main__":
    main()
