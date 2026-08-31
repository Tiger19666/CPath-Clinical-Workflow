# Structured multimodal baseline adapter

v0.3's first execution slice compares four non-novel patient-level baselines using an existing pathology feature store plus structured clinical covariates:

1. pathology-only logistic baseline on mean-pooled patient pathology vectors;
2. clinical-only logistic baseline;
3. concatenation fusion logistic baseline;
4. equal-weight late probability fusion.

All imputers, encoders and scalers are fit on the training split only. The adapter is for clinical feasibility/incremental-value baselines, not algorithmic novelty.
