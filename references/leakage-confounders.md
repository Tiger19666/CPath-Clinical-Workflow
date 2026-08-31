# Leakage and confounder checks

Leakage must be checked at the highest scientifically relevant identity level, not only at the file level.

Minimum hierarchy where available:

```text
question/pair -> slide -> specimen -> case/patient -> site/center
```

Rules:

- slide/item non-overlap does not prove patient independence;
- repeated questions from the same slide must be grouped for image-text/VQA evaluation;
- multiple slides from one patient must remain in one split for patient-independent claims;
- TCGA slide identifiers should be reduced to the patient barcode when auditing cross-partition contamination;
- if a higher-level identity cannot be resolved, report `UNRESOLVED` rather than `PASS`;
- center/site structure must be locally evidenced before using a multi-center scoring modifier.
