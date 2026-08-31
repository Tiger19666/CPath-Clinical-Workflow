# BRCA T001 v0.4 low-cost validation smoke

Goal: validate the v0.4 **evaluation/robustness/reproducibility/claim** plane using an existing T001 v0.3 smoke prediction file. Do not retrain models or rerun WSI processing.

## Required upstream artifacts

- existing `predictions.csv` from the v0.3 multimodal smoke;
- the corresponding small clinical table for subgroup linkage;
- optionally the v0.3 covariate contract / metrics as provenance inputs.

## Example

```bash
python scripts/run_v04_validation.py \
  --task-id T001 \
  --predictions <V03_RUN>/outputs/multimodal_baselines/predictions.csv \
  --clinical-table <V03_RUN>/clinical_smoke.tsv \
  --patient-id-col case_submitter_id \
  --subgroups race ethnicity ajcc_pathologic_stage \
  --primary-model concat_fusion \
  --comparators pathology_only clinical_only \
  --split test \
  --study-scope SMOKE_INTERNAL \
  --bootstrap-reps 200 \
  --min-group-n 20 \
  --skill-root <CPATH_V04_ROOT> \
  --output-dir <V04_RUN>/validation_v04
```

## PASS criteria

- evaluation contract is produced;
- bootstrap/paired code executes at patient level;
- evaluation status is `DIAGNOSTIC_ONLY` for smoke;
- tiny subgroup cells are marked insufficient rather than interpreted;
- reproducibility manifest hashes declared inputs/outputs;
- Clinical Claim Guard returns `EXECUTION_ONLY` for smoke;
- no TRIDENT, FM feature extraction or model training is triggered.
