# CPath-Clinical Workflow v1.0 Acceptance Tests

## Automated release tests

Run:

```bash
python -m pytest -q
python tests/run_acceptance.py
```

Current release target: all unit/integration tests pass, YAML parses, Python compiles, and the public-package privacy guard passes.

## v1.0 core acceptance

1. v0.1–v0.4 previously validated routes remain callable.
2. Single-cohort requests remain backward compatible.
3. Multi-cohort input creates a distinct registry entry per cohort.
4. Patient identity namespaces are not silently merged.
5. Cross-cohort prediction-level mismatch is incompatible.
6. Cohorts are not pooled without explicit permission even when otherwise compatible.
7. External validation requires explicit independence; unresolved cases remain `VALIDATION_CANDIDATE`.
8. Stale artifact state blocks AutoResearch readiness.
9. `EXECUTION_ONLY` smoke results block scientific AutoResearch readiness.
10. A frozen scientific contract can emit `READY_FOR_AUTORESEARCH`.
11. Public export redacts absolute paths without deleting hashes.
12. v1 workspace creates cohort/run/export structures.

## High-value black-box multi-cohort test

Use `MULTI_COHORT_V1_TEST_PROTOCOL.md`. A good run should organize multiple cohorts into defensible study roles without automatic pooling or unsupported external-validation claims.
