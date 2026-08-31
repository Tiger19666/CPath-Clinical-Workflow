# Public release policy — CPath-Clinical Workflow v1.0

The Skill package may contain workflow code, schemas, registries, templates, tests and documentation.

It must not contain:
- private datasets or clinical tables;
- WSI/ROI/patch files;
- extracted H5/PT features from private projects;
- model weights/checkpoints;
- private run outputs;
- private absolute server paths, credentials or access tokens.

Local external dependencies (TRIDENT, pathology foundation models, CUDA/conda environments) remain outside the Skill. The Skill may detect, validate and record their versions/provenance.

For sharing a reproducibility/run manifest, use `modules/export/redact_public_manifest.py` so local absolute paths are replaced while hashes and non-sensitive scientific contracts are retained.
