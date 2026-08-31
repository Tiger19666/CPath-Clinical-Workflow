# Existing Feature Reuse

Existing pathology embeddings are valuable assets, but they are only reusable when their provenance is adequate.

## Required checks

For each feature collection record:

- inferred or explicit encoder id
- number of feature files
- intended WSI count
- shared slide identifiers
- embedding dimension from sampled files
- whether coordinates exist
- patch geometry if recoverable
- magnification/MPP if recoverable
- extraction version/commit if available
- incomplete/corrupt feature files

## Reuse status

- `REUSE_OK`: provenance and coverage are sufficient for the intended task.
- `REUSE_WITH_WARNING`: usable for exploratory work but one or more provenance fields are unresolved.
- `REEXTRACT_MISSING_ONLY`: most features are valid; complete the missing cohort if the tool supports consistent extraction.
- `REEXTRACT_ALL`: feature contract is incompatible or too uncertain for the claim.
- `UNRESOLVED`: cannot determine what the feature files represent.

## Important

Do not recompute features simply because raw WSI are available.

Do not reuse features simply because the files exist.
