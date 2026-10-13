# No Hack data policy

Git tracks this document and empty directory keepers, **not** real network captures or training datasets.

- raw/: immutable original NSL-KDD, CICIDS2017, CSE-CIC-IDS2018 archives and extracted files (locally downloaded after terms/provenance review).
- interim/: intermediate audit and cleanup outputs, not shared publicly.
- processed/: versioned, audited Parquet training-ready data with split manifests recorded separately.
- samples/: deterministic, tiny privacy-safe fixtures only after explicit review; initially empty.

Datasets have independent use, licensing and citation requirements. Do not bundle them with a Windows installer, upload private local capture data to Kaggle, or commit them to Git. Keep flow-only metadata as the default. Exclude raw packet payloads from logs and artifacts.

Future dataset manifests should record origin URL, access date, file hashes, label mapping, split strategy, preprocessing version and NoHackFlow feature schema version. Leakage-sensitive split information must be persisted with every trained model. Public datasets are *not* assumed compatible with live Windows features without verified mapping.
