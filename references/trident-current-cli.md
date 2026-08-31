# TRIDENT execution contract used by Clinical v0.2

Clinical v0.2 targets the current TRIDENT command-line contract rather than importing TRIDENT internals.

Expected pipeline:

`tissue segmentation -> patch coordinates -> patch features`

The adapter preserves the encoder-native patch size and magnification stored in `registries/foundation_models.yaml`. It first creates a one-slide sanity command and only then a cohort batch command. The batch command uses a cohort WSI list and TRIDENT's resumable `job_dir` behavior.

Upstream reference: MahmoodLab/TRIDENT main-branch README and quickstart, verified 2026-08-31.
