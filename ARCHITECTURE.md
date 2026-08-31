# CPath-Clinical Workflow v1.0 Architecture

v1.0 freezes the Clinical Skill as a stable contract from raw clinical-pathology data to a reproducible standard baseline and an evidence-bounded AutoResearch handoff.

## Plane 1 — Clinical design

`Request -> Cohort Registry -> Data/Labels/Linkage -> Atomic Task Portfolio -> Clinical Literature -> Readiness -> Cohort/Split Freeze`

For a single cohort, the registry contains one entry. For multiple cohorts, each cohort remains independently identified and receives a conservative study role. v1.0 never equates “same disease name” with permission to pool data.

### Multi-cohort study roles

- `DEVELOPMENT`: cohort used to develop/train the standard clinical baseline.
- `INTERNAL_VALIDATION`: same-source/internal independent holdout when explicitly declared.
- `EXTERNAL_VALIDATION`: independent external cohort only when independence is supported.
- `VALIDATION_CANDIDATE`: endpoint-compatible but independence is unresolved.
- `TRANSFER_ONLY`: scientifically related but endpoint/modality/definition compatibility is insufficient for direct validation.
- `UNSUPPORTED`: target not supported.

Cross-cohort compatibility checks disease context, endpoint/prediction level, label-definition harmonization, required modalities and representation/preprocessing contracts. Pooling is disabled by default.

## Plane 2 — Standard execution

### Vision route inherited from v0.2

`Frozen task -> Local environment/FM -> TRIDENT/equivalent -> Known-FM Feature Store -> Feature QC -> Standard MIL -> Predictions`

### Structured multimodal route inherited from v0.3

`Frozen task/split -> Pathology Feature Store -> Train-aware Clinical Covariate Contract -> Pathology-only / Clinical-only / Concat / Late Fusion -> Predictions`

FM adaptation and pathology VLM remain deferred standard-route hooks and can be implemented when a representative clinical task requires them.

## Plane 3 — Validation inherited from v0.4

`Frozen predictions -> Evaluation Contract -> Patient Bootstrap/Paired Delta -> Subgroup Support Gate -> Reproducibility Manifest -> Clinical Claim Guard`

Metric magnitude cannot upgrade study-design evidence. Smoke remains diagnostic/execution-only.

## Plane 4 — v1.0 artifact and stability layer

`Upstream artifacts -> SHA256/dependency state -> FRESH|STALE|MISSING -> Run Manifest`

Stale upstream evidence propagates downstream. A stale clinical contract cannot be handed to AutoResearch as current evidence.

`modules/export/redact_public_manifest.py` provides a public-export path that removes local absolute paths while preserving non-sensitive hashes and contract content.

## Plane 5 — v1.0 AutoResearch finalization gate

`Task + frozen split + representation + standard baselines + evaluation contract + FROZEN reproducibility + claim scope + fresh artifact state -> autoresearch_handoff.yaml`

A scientific handoff is `READY_FOR_AUTORESEARCH` only when the baseline is more than a smoke execution diagnostic.

### Immutable

- clinical endpoint/question semantics;
- label definition;
- prediction unit/task family;
- frozen final test split;
- clinical claim scope;
- evaluation contract;
- study-role plan.

### Controlled

- representation changes;
- cohort changes or pooling;
- other substrate changes under an explicitly declared comparison.

### Free

- architecture;
- aggregation;
- loss;
- sampling;
- optimization;
- fusion.

The final test set is not an AutoResearch feedback channel. Algorithm selection and hypothesis revision use development/validation evidence only.
