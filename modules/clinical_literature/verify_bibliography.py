from __future__ import annotations
import argparse
from difflib import SequenceMatcher
from pathlib import Path
import re
import yaml

EXTERNAL_RESOLVERS = {"pubmed", "crossref", "doi", "publisher", "guideline", "official_dataset_site", "official_clinical_source"}


def norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(s or "").lower()).strip()


def verify_one(p: dict) -> dict:
    claimed = p.get("claimed") or {}
    resolved = p.get("resolved") or {}
    resolver = str(resolved.get("resolver") or "").lower()
    resolver_ok = resolver in EXTERNAL_RESOLVERS
    source_url = str(resolved.get("source_url") or "").strip()
    resolver_record_id = str(resolved.get("resolver_record_id") or resolved.get("pmid") or resolved.get("doi") or "").strip()
    trace_ok = bool(source_url) and bool(resolver_record_id)
    ct, rt = norm(claimed.get("title")), norm(resolved.get("title"))
    title_similarity = SequenceMatcher(None, ct, rt).ratio() if ct and rt else 0.0
    cy, ry = claimed.get("year"), resolved.get("year")
    year_ok = cy in (None, "") or ry in (None, "") or str(cy) == str(ry)
    cd, rd = norm(claimed.get("doi")), norm(resolved.get("doi"))
    doi_ok = not cd or not rd or cd == rd
    if not resolver_ok or not trace_ok or not rt:
        status = "UNRESOLVED"
    elif title_similarity < 0.90 or not year_ok or not doi_ok:
        status = "MISMATCH"
    else:
        status = "VERIFIED"
    return {
        "reference_id": p.get("reference_id"),
        "verification_status": status,
        "external_resolver": resolver or None,
        "external_trace_present": trace_ok,
        "title_similarity": round(title_similarity, 4),
        "year_match": year_ok,
        "doi_match": doi_ok,
        "usable_for_clinical_readiness": status == "VERIFIED",
        "claimed": claimed,
        "resolved": resolved,
    }


def verify(doc: dict) -> dict:
    results = [verify_one(x) for x in (doc.get("references") or [])]
    return {
        "version": "ClinicalBibliographyVerification-v1",
        "task_id": doc.get("task_id"),
        "status": "PASS" if results and all(x["verification_status"] == "VERIFIED" for x in results) else "PARTIAL_OR_FAIL",
        "references": results,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("references_yaml")
    ap.add_argument("-o", "--output", required=True)
    a = ap.parse_args()
    doc = yaml.safe_load(Path(a.references_yaml).read_text(encoding="utf-8"))
    Path(a.output).write_text(yaml.safe_dump(verify(doc), sort_keys=False), encoding="utf-8")


if __name__ == "__main__":
    main()
