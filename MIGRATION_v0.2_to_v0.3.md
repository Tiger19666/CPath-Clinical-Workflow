# Migration from v0.2 to v0.3

Do not rerun Discovery, clinical literature, cohort construction, split creation, or TRIDENT if the corresponding v0.2 artifacts are still valid.

For the first v0.3 structured-multimodal slice, reuse:
- task specification;
- frozen patient split;
- pathology feature store and QC;
- original patient-to-clinical-table linkage.

Add only:
1. clinical covariate contract;
2. train-only clinical preprocessing;
3. pathology-only / clinical-only / combined baseline comparison;
4. multimodal execution metrics/provenance.

If the pathology feature store is stale or missing, fall back to the v0.2 vision execution route before running multimodal baselines.
