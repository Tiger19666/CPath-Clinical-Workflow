# Changelog

## v1.0.0

Stable Clinical Skill release.

### Added
- multi-cohort request routing (`SINGLE_COHORT` / `MULTI_COHORT`);
- `CohortRegistry-v1` with per-cohort patient identity, modality, label, source and role metadata;
- cross-cohort compatibility checks for endpoint/prediction level, disease context, required modalities and representation/preprocessing differences;
- conservative multi-cohort study-role planner (`DEVELOPMENT`, `INTERNAL_VALIDATION`, `EXTERNAL_VALIDATION`, `VALIDATION_CANDIDATE`, `TRANSFER_ONLY`, `UNSUPPORTED`);
- no-automatic-pooling rule with explicit pooling permission;
- `ClinicalRunManifest-v1` with Skill version/Git state and stable-contract references;
- public-manifest path redaction while retaining hashes;
- hard v1 finalization runner and `AutoResearchHandoff-v1`;
- handoff readiness checks for frozen test split, standard baseline, evaluation contract, frozen reproducibility, claim scope and artifact freshness;
- final-test firewall language in the AutoResearch handoff;
- multi-cohort black-box test protocol.

### Frozen from validated v0.x routes
- v0.1 clinical intelligence/literature/task readiness;
- v0.2 local WSI -> pathology FM -> feature QC -> standard MIL execution;
- v0.3 structured clinical multimodal baseline execution;
- v0.4 evaluation/statistics/subgroup/reproducibility/claim guard.

### Deferred, not removed
- standard pathology FM adaptation route;
- pathology VLM route.

### Policy changes
- smoke execution may validate a route but cannot become an AutoResearch-ready scientific baseline;
- external-validation status requires explicit cohort independence evidence;
- compatible cohorts remain separate unless pooling is explicitly permitted;
- stale artifacts cannot be treated as current handoff evidence.
