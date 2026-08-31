# Migration: v0.4 -> v1.0

v1.0 does not replace the validated v0.4 evaluation plane. It freezes it and adds stable orchestration around it.

## New artifacts

- `shared/cohort_registry.yaml`
- task-level `multicohort_study_plan.yaml` when more than one cohort is present
- `runs/clinical_run_manifest.yaml`
- final `autoresearch_handoff.yaml` generated through the v1 finalization gate
- optional public redacted manifest

## Backward compatibility

A single `dataset_root` continues to work. Multi-cohort requests may instead provide `cohorts:`. Existing v0.2/v0.3/v0.4 execution artifacts can be reused if their artifact-state audit remains fresh and their clinical contract is compatible.

## Changed handoff semantics

v0.4 could construct a handoff with relatively weak readiness checks. v1.0 requires frozen evaluation/reproducibility/claim evidence and rejects `EXECUTION_ONLY` smoke runs as scientific AutoResearch baselines.

## No automatic pooling

Cohort pooling is opt-in and requires compatibility plus explicit permission. Endpoint-compatible but independence-unverified cohorts remain validation candidates rather than external validation cohorts.
