# Privacy and De-identification

## Principle

Treat raw clinical metadata and report text as potentially sensitive.

Do not mutate raw files by default.

Recommended pattern:

`raw/ (read-only) -> deidentified_working/ -> research outputs`

## Candidate direct identifiers

Examples include:

- patient name
- government ID / national ID
- medical record number
- phone
- email
- full address
- account number
- explicit free-text identifiers

Column names alone are imperfect. Flag candidates; do not claim complete de-identification from keyword matching.

## Pseudonymous linkage

Preserve a research-safe linkage key when needed:

`anonymous_patient_id`

The purpose is to maintain patient-level grouping without retaining direct identifiers in downstream research files.

## Clinical text

Before using diagnosis/report text:

- remove direct identifiers
- check dates/locations and other quasi-identifiers according to local policy
- separate text used as input from text used to derive the target
- prevent target leakage

Do not send private report text to public literature-search queries.

## Human review

Automatic privacy checks are screening aids, not legal certification. Require local governance/ethics procedures where applicable.
