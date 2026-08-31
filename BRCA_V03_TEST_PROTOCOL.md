# BRCA v0.3 low-cost smoke protocol

Goal: verify the first structured multimodal execution slice without rerunning WSI preprocessing or a full cohort baseline.

Reuse from the successful v0.2 BRCA run:
- T001 task definition;
- frozen patient-safe split or the existing smoke split;
- already extracted UNI2 H5 features;
- original local clinical table and patient linkage.

Recommended smoke flow:
1. Build a clinical covariate contract for a small set of non-target-derived variables (for example age/stage-related variables only when they are clinically appropriate and not target leakage for the selected endpoint).
2. Reuse the existing smoke H5 features; do not rerun TRIDENT.
3. Fit all preprocessing on train patients only.
4. Run pathology-only, clinical-only, concatenation-fusion, and late-fusion baselines.
5. Treat metrics as pipeline diagnostics only for a smoke subset.

Suggested black-box prompt:

> 使用 `CPath-Clinical Workflow` 接着已有 BRCA T001 v0.2 smoke 结果进入 v0.3。复用已经提取的 UNI2 features 和冻结 split，不重新做 Discovery、Literature 或 TRIDENT；从原 clinical table 中选择不会泄漏 T001 目标的结构化临床变量，先建立 covariate contract，再运行 pathology-only、clinical-only 和简单 multimodal fusion baseline。只需要 smoke 跑通，不要求 full cohort。
