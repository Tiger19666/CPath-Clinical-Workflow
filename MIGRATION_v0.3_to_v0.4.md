# Migration: v0.3 -> v0.4

v0.4 is additive. Existing v0.2/v0.3 artifacts remain reusable.

## Reuse

Do **not** rerun Discovery, Clinical Literature, TRIDENT, feature extraction or multimodal training merely to validate v0.4. Reuse the frozen prediction artifact.

## New validation artifacts

For a completed prediction run, generate:

```text
validation_v04/
  evaluation_contract.yaml
  evaluation_report.yaml
  subgroup_report.yaml            # when requested
  reproducibility_manifest.yaml
  clinical_claim_guard.yaml
  v04_validation_summary.yaml
```

## Covariate contract change

New v0.4 runs may supply frozen train patient IDs. Missingness and constant/variance eligibility are then assessed on train patients only. Each covariate may additionally receive inference-time availability: `AVAILABLE`, `CONDITIONAL`, `UNKNOWN`, or `UNAVAILABLE`.

Old v0.3 covariate contracts are not invalidated solely because these new fields are absent; regenerate them only when the multimodal training route itself is rerun.
