# Migration: v0.1 -> v0.2

v0.2 does not replace the v0.1 Clinical Intelligence artifacts. Existing dataset, linkage, label, task, literature, and clinical-readiness outputs should be reused when still fresh.

For a previously validated classification task:

1. Freeze an execution-specific cohort/label mapping.
2. Create the patient-safe split before any model computation.
3. Resolve local TRIDENT and a known FM checkpoint/access contract.
4. Evaluate the dual execution gate.
5. Run one-slide TRIDENT sanity.
6. Only after sanity PASS, run the full cohort.
7. Validate and finalize the known-FM Feature Store.
8. Run mean-pooling and ABMIL clinical baselines.
9. Register artifact hashes; if upstream task/cohort/split/FM inputs change, mark dependents stale.

Unknown legacy embeddings can remain as quick/reference baselines but do not satisfy the primary reproducibility requirement.
