---
name: cpath-clinical-workflow
description: End-to-end clinical computational pathology workflow for dataset discovery, clinical task design, reusable feature auditing, baseline planning/execution, validation, and reproducible clinical artifacts.
---

# CPath-Clinical Workflow Skill v1.0

## Purpose

Use this skill for end-to-end **clinical computational pathology research workflows**. The skill can either discover all defensible clinical tasks from a dataset or execute one/multiple explicitly requested clinical tasks through reproducible baseline evaluation.

Do not use this skill to invent new algorithms. Novel method search, mathematical feature-geometry mining, hypothesis iteration, and autonomous algorithm experimentation belong to CPath-AutoResearch.

## Mandatory entry routing

Before any heavy operation, infer exactly one mode:

### DISCOVERY
Use when the user supplies data but does not specify a clinical target.

Goal: discover **all** defensible clinical tasks, not only the top-ranked task. Produce a Clinical Task Portfolio with `GO`, `CONDITIONAL_GO`, `REDIRECT`, or `NO_GO` for every candidate.

### TASK_SPECIFIED
Use when the user specifies one endpoint/task. Do not rerun broad task discovery as the primary workflow. Validate the specified task and construct its full clinical pipeline.

### MULTI_TASK_SPECIFIED
Use when the user names multiple tasks/endpoints. Build one task spec per endpoint and a shared-asset DAG. Reuse preprocessing/features only when contracts are compatible.

Write `request_spec.yaml` first. It must include `mode`, `requested_tasks`, `execution_intent`, privacy/constraints, and either a single `dataset_root` or a `cohorts:` list. v1.0 records `cohort_mode=SINGLE_COHORT|MULTI_COHORT`.

## Execution intent

Classify intent as:

- `ASSESS_ONLY`: user asks whether a task/data is feasible. Stop after readiness + execution plan.
- `PLAN`: user asks for a pipeline/design but not to run it. Stop before expensive compute.
- `EXECUTE`: user explicitly asks to perform/run/build/train the task. If readiness passes, continue through the standard clinical baseline pipeline.
- `EXECUTE_SELECTED`: discovery mode only; execute only user-approved selected tasks.

Never infer `EXECUTE` merely because a task is technically feasible.

## C0 — Intake and safety

Record dataset root, intended task(s), privacy status, execution intent, allowed external access, and resource constraints. Never upload private data without explicit authorization.

## C1 — Data Intelligence

Inventory raw WSI, tissue-section images, ROI, patches, cell/spatial annotations, text, clinical tables, omics, existing features, model outputs, and preprocessing artifacts.

Do not equate TIFF with WSI without evidence. Track modality certainty (`VERIFIED`, `LIKELY`, `UNKNOWN`).

Build:
- `dataset_manifest.yaml`
- `entity_graph.yaml`
- `data_quality.yaml`
- `existing_feature_manifest.yaml`

### v1.0 multi-cohort registry

When multiple cohorts are supplied, build `shared/cohort_registry.yaml` before cross-cohort task planning. Each cohort keeps its own patient identity namespace, modalities, endpoint signatures, source/site metadata, representation provenance, and declared/verified study role.

Run cross-cohort compatibility per clinical endpoint. Compatibility must consider disease context, endpoint/prediction level, required modalities, label-definition harmonization, and representation/preprocessing compatibility. **Never automatically pool cohorts.** Pooling requires both compatibility and explicit pooling permission.

Assign study roles conservatively:
- `DEVELOPMENT`
- `INTERNAL_VALIDATION`
- `EXTERNAL_VALIDATION` only when independence is explicitly supported
- `VALIDATION_CANDIDATE` when independence is unresolved
- `TRANSFER_ONLY` when the cohort is useful but not directly compatible
- `UNSUPPORTED`

A `VALIDATION_CANDIDATE` must not upgrade the clinical claim to external validation.

## C2 — Label, linkage, and leakage intelligence

Identify all clinically meaningful labels and endpoints, including diagnosis, subtype, grade, stage, biomarkers, molecular labels, treatment/response, recurrence, survival, anatomic structures, report/VQA targets, and other supported endpoints.

For every label record level, type, source, coverage, missingness, distribution, quality, temporal meaning, linkage, and leakage risk.

Build:
- `label_catalog.yaml`
- `linkage_manifest.yaml`
- `leakage_audit.yaml`

A task cannot be `GO` if its target cannot be reliably linked to its prediction unit.

## C3 — Clinical Task Portfolio

### DISCOVERY
Generate all defensible tasks supported by verified local data/labels. Do not collapse the portfolio to a single winner. Keep unsupported-but-interesting ideas in a separate `future_opportunities.yaml`; do not mix them with runnable task cards.

Each task card must be **atomic**: one clinical endpoint, one prediction unit, one primary task family. Validate every task with `modules/task_validation/validate_task_spec.py` before literature review.

Each task card must include:
- clinical question
- target and label source
- task family
- prediction unit/level
- required/optional modalities
- cohort estimate
- label quality/distribution
- clinical relevance
- major risks
- execution dependencies
- task status

### TASK_SPECIFIED / MULTI_TASK_SPECIFIED
Create task cards only for requested tasks plus minimal auxiliary tasks required by the pipeline. Other possible tasks may be mentioned as optional, but do not derail execution.

## C4 — Clinical literature and clinical readiness

Literature search here answers clinical questions: endpoint importance, clinical standard, pathology-AI saturation, validation expectations, cohort requirements, and claim scope. Algorithm novelty search belongs to AutoResearch.

For every supported or conditional task, run the Clinical Literature contract:

1. `build_search_plan.py` creates four required query families: clinical endpoint/standard, pathology-AI landscape, validation landscape, and dataset/benchmark landscape.
2. The agent must perform the **real external searches** when web access is allowed and write `search_trace.yaml`. A self-declared `COMPLETE` flag is not evidence.
3. `verify_bibliography.py` accepts `VERIFIED` only when claimed metadata are matched to metadata resolved from an external resolver/source such as PubMed, Crossref/DOI, publisher, guideline, or official dataset/clinical site. LLM-filled claimed and resolved fields without an external resolver are `UNRESOLVED`.
4. `validate_search_coverage.py` checks that all required search families were actually executed and produced selected references.
5. `build_clinical_landscape.py` and `assess_clinical_gap.py` summarize endpoint importance, clinical standard, pathology-AI saturation, validation expectations, cohort requirements, and claim scope.

Algorithm novelty search belongs to AutoResearch. If web access is not allowed, mark bibliographic verification and clinical literature readiness unresolved/conditional rather than inventing citations.

A task that was provisionally `GO` from data readiness must be downgraded to `CONDITIONAL_GO` when its clinical literature stage is incomplete or unverified. Retain all tasks in the portfolio.

## C5 — Cohort, labels, and split freeze

For runnable tasks, construct explicit inclusion/exclusion rules and machine-readable manifests.

Outputs per task:
- `cohort.csv`
- `excluded_cases.csv`
- `label_manifest.csv`
- `cohort_spec.yaml`
- `split_spec.yaml`

Splits must be leakage-safe at the highest identity level available (patient/case before slide/ROI). Support site-safe, temporal, external-validation, and leave-one-center-out designs when clinically appropriate.

The frozen test split is immutable for downstream AutoResearch unless a clinical review reopens the task.

## C6 — Environment and compute readiness

Before execution, audit Python/PyTorch/CUDA, storage, WSI readers, local FM code/weights, TRIDENT or equivalent preprocessing, downstream training framework, and required package versions.

Separate:
- `compute_capability`: what resources actually exist.
- `execution_permission`: whether current user intent permits compute.

Statuses: `READY_TO_RUN`, `CONDITIONAL_READY`, `NOT_READY`.

## C7 — Representation Router

Choose the standard clinical representation route per task:
- vision-only
- vision + structured clinical
- vision + text / VLM
- vision + omics
- dense prediction
- no-FM classical/standard route

Choose FM strategy:
- frozen existing FM
- linear/shallow adaptation
- LoRA/PEFT
- partial/full fine-tuning
- standard VLM adaptation
- train/use domain-specific visual model only when scientifically and operationally justified
- no FM required

Clinical Skill may select and execute standard routes. It must not invent a new architecture as part of baseline execution.

## C8 — Preprocessing, feature extraction, and shared assets

Feature extraction is **task-aware**, not automatic on dataset discovery.

For frozen visual FMs:
`image -> tissue/ROI selection -> patching -> encoder -> feature QC -> shared feature store`.

A shared feature store must record encoder, weights/version, preprocessing contract, magnification/MPP assumptions, patch size/stride, cohort, feature dimension, checksum/provenance, coverage, NaN/empty-bag audit, and creation time.

If existing compatible features are present, first classify provenance with `modules/features/classify_feature_provenance.py`. Distinguish:
- `KNOWN_FM_FEATURE`: encoder/weights identity and preprocessing contract are sufficiently known; can serve as a reproducible primary substrate.
- `LEGACY_FEATURE_PROVENANCE_INCOMPLETE`: embeddings exist but encoder/version/preprocessing is unresolved; may be used only as a quick/reference baseline and must not be described as a known FM feature store.
- `NON_FM_FEATURE`: reuse is task-dependent.
- `NO_EXISTING_FEATURE`: choose a new representation plan.

Prefer reuse only when scientifically compatible. Do not re-extract simply because extraction code is available.

For FM adaptation, create a versioned adapted checkpoint plus provenance and do not mix it with frozen-feature stores.

## C9 — Standard Downstream Model Router

Select standard clinical baselines appropriate to the task, for example:

- WSI classification: mean/max pooling, ABMIL, CLAM, TransMIL or other registered standard baselines.
- Multi-slide patient tasks: standard slide-to-patient aggregation/hierarchical baseline.
- Survival: pathology-only Cox/discrete-time baselines; when structured clinical covariates are available, also require clinical-only and pathology+clinical comparators to measure incremental value.
- Dense tasks: registered segmentation/detection baselines.
- VLM: zero-shot/few-shot/standard PEFT or instruction-tuning baseline.
- Multimodal: require unimodal comparators plus standard concatenation/late fusion/simple gated fusion when the modalities permit it.

Baseline choice is for clinical feasibility and reproducibility, not algorithm novelty.

## C10 — Training

When `execution_intent=EXECUTE` and readiness is satisfied, execute the registered standard pipeline. Save configs, seed(s), environment snapshot, logs, checkpoints, predictions, and failures.

If a required external tool/model is unavailable, do not silently substitute a different scientific pipeline. Mark `BLOCKED_DEPENDENCY` and provide the nearest valid plan.

## C11 — Evaluation, robustness, reproducibility, and clinical claims

Evaluation is a contract, not an afterthought. Before interpreting predictions, create an `evaluation_contract.yaml` that fixes task-appropriate primary/secondary metrics, resampling unit, uncertainty method, paired-comparison rules, study scope, and the primary model/comparators. Patient-level tasks must resample patients rather than slides.

For binary classification, the default v1.0 contract includes AUROC/AUPRC, balanced accuracy, macro-F1, accuracy, sensitivity/specificity, Brier score and a simple ECE diagnostic. Scientific evaluation should report patient-bootstrap confidence intervals where feasible and use paired patient resampling for model deltas. Smoke runs may execute the same code but must be labeled `DIAGNOSTIC_ONLY`.

Run subgroup/robustness analysis only at support levels that permit interpretation. Groups below the configured minimum size or containing one class are descriptive/insufficient, not evidence of robustness. Site/center, demographic and clinical subgroup analyses are task-dependent and must not be overinterpreted from tiny smoke samples.

Freeze a `reproducibility_manifest.yaml` containing hashes of declared inputs/outputs, skill version, environment/package versions, seed, task ID, and run scope. A result whose upstream artifacts change must be treated as stale and re-audited.

Clinical claims are hard-gated by study design. `SMOKE` permits execution claims only; an internal frozen holdout permits retrospective internal-validation claims; independent external cohorts are required for external-validation/generalization claims; prospective validation and clinical-utility claims require their corresponding study designs. Metric magnitude alone can never upgrade claim level.

## C12 — Stable finalization and AutoResearch handoff

v1.0 treats handoff as a hard finalization contract, not an optional prose summary. Run `scripts/finalize_v1_clinical_run.py` after a standard scientific baseline has been frozen.

The handoff freezes:
- atomic clinical endpoint/question, label definition, prediction unit and task family
- frozen final test split
- clinical claim scope
- evaluation contract
- multi-cohort study plan when present
- standard baseline results
- representation/cohort provenance
- reproducibility manifest, subgroup evidence and artifact state
- known failure modes

`READY_FOR_AUTORESEARCH` requires all of the following:
1. a frozen test split;
2. at least one standard baseline;
3. a frozen evaluation contract;
4. `reproducibility_manifest.status=FROZEN`;
5. an explicit clinical claim scope;
6. no stale upstream artifact when artifact state is provided;
7. a scientific baseline rather than `EXECUTION_ONLY` smoke diagnostics.

The handoff declares:
- **IMMUTABLE:** endpoint/question semantics, label definition, prediction unit, frozen final test split, clinical claim scope, evaluation contract, and the clinical study-role plan.
- **CONTROLLED:** representation and cohort changes only under an explicitly declared comparison; they must not silently overwrite the frozen baseline contract.
- **FREE:** architecture, aggregation, loss, sampling, optimization and fusion.

AutoResearch may not use final-test labels/results for algorithm selection, debugging, hyperparameter tuning, or hypothesis revision. Any proposed claim upgrade returns to Clinical review. Negative results remain part of the research ledger.

Also emit `clinical_run_manifest.yaml` so the Skill/version/Git state and key contract artifacts can be tracked independently of individual training code.

## Multi-task orchestration

For multiple clinical tasks, build a dependency DAG before compute. Share assets only when scientifically compatible. Example: ER/PR/HER2 may share the same WSI preprocessing and frozen encoder feature store, while survival may share images but require a different cohort due to endpoint availability.

Never let convenience force incompatible tasks into one cohort or label space.

## Required workspace layout

```text
clinical_workspace/
  request_spec.yaml
  shared/
    cohort_registry.yaml
    cohorts/
    dataset_manifest.yaml
    entity_graph.yaml
    linkage_manifest.yaml
    data_quality.yaml
    environment_report.yaml
    artifact_state.yaml
    representations/
  task_portfolio.yaml
  tasks/
    Txxx_name/
      task_spec.yaml
      literature/
      cohort/
      split/
      representation_plan.yaml
      execution_plan.yaml
      training_runs/
      predictions/
      validation/
      clinical_report.md
      autoresearch_handoff.yaml
  runs/
    clinical_run_manifest.yaml
  exports/
    public_redacted_manifest.yaml
```

## v1.0 stability contract

1. v1.0 is the stable clinical-workflow boundary; new algorithm families are not added here merely to increase coverage.
2. Existing v0.3 deferred FM-adaptation and pathology-VLM routes remain supported design hooks but are not required for v1.0 readiness until a real task needs them.
3. Cohort/endpoint/test-split/evaluation changes create a new clinical contract version rather than silently mutating an AutoResearch-ready run.
4. Artifact reuse is allowed only when the artifact-state audit is fresh and the scientific contract remains compatible.
5. Public exports must redact local absolute paths while retaining hashes/provenance where possible. Use `modules/export/redact_public_manifest.py`.

## Hard boundaries

1. Do not hide unsupported tasks; retain them as `NO_GO`/`REDIRECT` with reasons.
2. Do not execute expensive compute in DISCOVERY merely because a task is `GO`.
3. Do not re-split the frozen test set to improve results.
4. Do not call an invented architecture a standard clinical baseline.
5. Do not upload private data or artifacts without explicit authorization.
6. If data/label linkage is unresolved, stop the affected task before training.
7. Do not mark clinical literature complete without a real search trace and externally resolved bibliographic metadata.
8. Do not allow non-atomic task cards (for example, `report generation OR VQA` or `molecular subtype OR survival`).
9. Do not call an unknown legacy embedding a reproducible FM feature store.
10. For survival/multimodal clinical studies, do not claim added value without appropriate unimodal/clinical comparators when those covariates exist.

## v0.2 executable vision baseline profile

The v0.2 vision profile remains available unchanged for patient/slide classification from H&E WSI using a known patch foundation model, TRIDENT, feature QC, mean pooling, and ABMIL. It may be reused without rerunning clinical discovery or literature.

## v0.3 structured multimodal execution profile

The first v0.3 execution slice adds **structured clinical covariates** on top of an already valid pathology feature store. It is deliberately a baseline layer, not an algorithm-innovation layer.

Mandatory order:

`frozen task/split -> reusable pathology feature store -> clinical covariate contract -> train-only preprocessing -> pathology-only baseline -> clinical-only baseline -> concat fusion -> late fusion -> incremental-value diagnostic`.

Rules:
- Reuse v0.2 pathology features when feature QC/provenance is acceptable; do not rerun TRIDENT merely to test multimodal execution.
- Clinical covariates must be reviewed for identifiers, target-derived fields, and obvious leakage before modeling.
- Numeric imputation/scaling and categorical imputation/one-hot encoding are fit on **train patients only**.
- The pathology-only and clinical-only comparators are mandatory before interpreting a combined model.
- v0.3's default fusion implementations are standard non-novel baselines: feature concatenation with logistic classification and equal-weight late probability fusion.
- Smoke metrics prove execution only; they are not clinical performance claims.
- The clinical endpoint, label mapping, patient split, and pathology feature provenance remain frozen inputs to this execution slice.

### Current v0.3 scope

Executable now:
- vision-only classification inherited from v0.2;
- structured-clinical-only classification;
- pathology + structured-clinical concatenation baseline;
- pathology + structured-clinical late-fusion baseline.

Still planning-only in this initial v0.3 slice:
- pathology + omics;
- VLM/vision + free text;
- LoRA/PEFT and foundation-model fine-tuning;
- survival multimodal execution;
- dense prediction.

These should be added only after representative smoke regression, without changing the frozen clinical contract.

## v0.4 validation and reproducibility profile

The v0.4 execution slice consumes already-generated predictions; it does not require retraining or feature extraction.

Mandatory order:

`frozen predictions -> evaluation contract -> patient-level point metrics -> patient bootstrap / paired deltas -> subgroup support audit -> reproducibility manifest -> clinical claim guard`.

Rules:
- Preserve the frozen clinical endpoint, cohort/split identity, prediction rows and model names while validating a run.
- For smoke runs, compute statistics only to test code paths and label the result `DIAGNOSTIC_ONLY`; do not infer scientific performance from tiny samples.
- Bootstrap and paired comparisons use the prediction unit (patient for patient-level tasks), never individual patches/slides as pseudo-independent samples.
- Calibration diagnostics are part of the standard classification evaluation contract, but tiny smoke samples are not calibration evidence.
- Subgroups below the configured support threshold or with a single observed class are `INSUFFICIENT_GROUP_SIZE` / `SINGLE_CLASS` rather than silently producing unstable clinical claims.
- Reproducibility manifests hash declared inputs/outputs and record the local environment; private datasets/model weights remain external and are never bundled into the public Skill.
- Claim level is determined by study design, not AUROC magnitude.
- Structured clinical covariate eligibility can now be assessed on train patients only when a frozen split is provided, and inference-time availability is tracked separately from target leakage.

### Deferred v0.3 routes

Standard foundation-model adaptation (linear/partial/LoRA/PEFT) and pathology VLM execution remain intentionally deferred. They are not required for v0.4 validation and should be implemented only when a representative clinical task needs them.

