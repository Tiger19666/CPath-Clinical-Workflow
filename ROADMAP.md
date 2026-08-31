# Roadmap after v1.0

v1.0 freezes the primary Clinical Skill architecture. Future work should prefer targeted adapters/bug fixes over new core stages.

## Deferred standard adapters

Implement only when a representative clinical task requires them:
- Foundation-model linear/partial/LoRA/PEFT adaptation;
- pathology VLM zero-shot/image-text/VQA/standard PEFT.

## v1.x maintenance priorities

- real-world multi-cohort regression across heterogeneous institutions/datasets;
- additional task-family evaluation contracts (survival, dense prediction, VLM);
- external-validation and temporal/site split adapters;
- stronger source-code/container provenance where the execution environment supports it;
- public export packaging/redaction;
- bug fixes revealed by black-box cohort tests.

## Separate research layer

Novel algorithm development belongs to CPath-Algorithm-AutoResearch and may use CCFA Skills for literature/idea/review/experiment-design orchestration. Clinical v1.0 supplies the frozen clinical contract and evidence boundary.
