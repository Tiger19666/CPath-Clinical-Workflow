# CPath-Clinical v1.0 Multi-Cohort Black-Box Test

## Recommended user prompt

> 使用 `CPath-Clinical Workflow` 分析这些 cohort，判断它们各自支持哪些临床计算病理任务，并组织成合理的多 cohort 临床研究。不要为了方便自动合并 cohort；如果某个 cohort 能作为外部验证，请说明依据。先完成评估和研究设计，不必把所有大规模实验跑完。

## Expected behavior

1. Build one cohort registry entry per cohort.
2. Keep patient identity/linkage namespaces separate.
3. Build the clinical task portfolio without silently forcing all cohorts into a shared label space.
4. For each selected endpoint, assess cross-cohort endpoint/modality/label compatibility.
5. Assign `DEVELOPMENT`, `INTERNAL_VALIDATION`, `EXTERNAL_VALIDATION`, `VALIDATION_CANDIDATE`, `TRANSFER_ONLY`, or `UNSUPPORTED` conservatively.
6. Do not claim external validation when cohort independence is unresolved.
7. Do not pool cohorts unless compatibility and explicit pooling permission are both present.
8. Reuse compatible representations/features but retain cohort provenance.
9. Produce a study plan that can later feed standard execution/evaluation.
10. For a scientific completed baseline, emit the v1 AutoResearch handoff; for assessment/smoke runs, keep handoff `NOT_READY` with explicit reasons.

## High-value failure cases

- same disease but different endpoint definitions;
- patient-level label in one cohort vs slide-level label in another;
- cohort with no verified patient identity key;
- external-looking cohort whose independence is not documented;
- different encoders/preprocessing contracts presented as one pooled feature store;
- missing target in one cohort;
- stale artifact reused as current evidence.
