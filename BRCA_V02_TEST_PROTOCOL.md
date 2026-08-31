# BRCA v0.2 regression protocol

Use the same local BRCA dataset as the v0.1 run. Do not repeat Discovery or literature search.

Primary execution target: `T001 Histologic subtype prediction`, with a frozen major-subtype binary execution contract:

- `Infiltrating duct carcinoma, NOS -> ductal`
- `Lobular carcinoma, NOS -> lobular`
- mixed/rare labels excluded and logged
- patient-safe stratified train/val/test split

Recommended black-box prompt:

> 使用 `CPath-Clinical Workflow` 接着已有 BRCA 临床任务结果，对 T001 进行 v0.2 执行回归。复用已有数据理解、临床文献和任务定义，不重新做 Discovery；先冻结 ductal vs lobular patient-safe cohort/split，检查 TRIDENT 与本地基础模型环境，先执行单张 WSI sanity，再在通过后生成/复用 provenance 完整的 feature store，并训练 mean-pooling 与 ABMIL 标准 baseline。不要修改冻结的 test split；若本地基础模型或 TRIDENT 依赖缺失，明确停在对应 gate，不要自动下载模型。

Expected stages:

1. Cohort freeze
2. Patient-safe split freeze
3. Dual execution permission gate
4. Local FM resolution
5. One-slide TRIDENT sanity
6. Full feature-store extraction only after sanity PASS
7. H5 feature-store QC
8. Mean-pooling reference baseline
9. ABMIL baseline
10. Test metrics + predictions + provenance

For token-efficient regression, reuse v0.1 artifacts and do not re-run clinical literature.
