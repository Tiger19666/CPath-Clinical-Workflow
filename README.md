# CPath-Clinical Workflow v1.0

Stable clinical computational pathology workflow from cohort/data understanding to a reproducible standard baseline, bounded clinical claims, and an AutoResearch-ready handoff.

## What v1.0 freezes

- v0.1: data/label/linkage intelligence, atomic clinical task portfolio, externally traceable clinical literature, readiness.
- v0.2: executable local WSI -> pathology FM -> feature QC -> standard MIL route.
- v0.3: executable pathology + structured-clinical multimodal route with train-aware preprocessing.
- v0.4: evaluation contract, patient-level statistics, subgroup support gates, reproducibility and clinical claim guard.
- v1.0: multi-cohort registry/study roles, stable run manifest, public-export redaction, and a hard AutoResearch finalization gate.

## Multi-cohort principle

Multiple cohorts are not pooled automatically. v1.0 first builds a cohort registry and assigns conservative study roles. `EXTERNAL_VALIDATION` requires explicit evidence of independence; otherwise an endpoint-compatible cohort remains `VALIDATION_CANDIDATE` and cannot upgrade claim scope.

## AutoResearch boundary

`READY_FOR_AUTORESEARCH` requires a frozen clinical task/test split, standard scientific baseline, evaluation contract, frozen reproducibility manifest, explicit claim scope, and non-stale upstream evidence. Smoke runs may validate the Clinical Skill but remain `NOT_READY` for scientific algorithm comparison.

Novel algorithms remain outside this Skill. AutoResearch/CCFA can consume the frozen handoff while respecting immutable/controlled/free change spaces.

## Deferred standard routes

Foundation-model adaptation and pathology VLM routes remain deferred hooks. They are not required for v1.0 unless a real clinical task needs them.

See `SKILL.md`, `ARCHITECTURE.md`, `MULTI_COHORT_V1_TEST_PROTOCOL.md`, and `MIGRATION_v0.4_to_v1.0.md`.
