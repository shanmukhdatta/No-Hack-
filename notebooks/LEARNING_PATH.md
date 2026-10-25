# No Hack — Five-Notebook Learning Path

Start with Python 3.11, a repository checkout, and an independently verified canonical NoHackFlow v1 labeled dataset. Train only on your own or explicitly permitted data.

Set environment variable NOHACK_DATASET to CSV/Parquet containing the exact 33 fields plus label and group_id. Optionally set NOHACK_SPLITS and NOHACK_MODEL_DIR.

| Stage | Notebook | What to learn |
|---|---|---|
| 1 | 01_dataset_audit.ipynb | Inspect columns, provenance, labels, nulls and duplicates |
| 2 | 02_exploratory_analysis.ipynb | Feature distributions, imbalance and group structure |
| 3 | 03_leakage_safe_splits.ipynb | Freeze group-disjoint splits and verify hashes |
| 4 | 04_supervised_baselines.ipynb | Simple baselines and validation-only metrics |
| 5 | 05_hybrid_stack_export.ipynb | OOF hybrid training, evaluation and verified local export |

Repeat stages 1–3 on each dataset separately. Combine only semantically compatible NoHackFlow records with real group provenance; never make up labels or silently rename CICFlowMeter fields. After combining, re-run all five stages.

The existing nohack_kaggle.ipynb is an additional CLI handoff. No real dataset or result is distributed with these educational notebooks.

When combining two or more separately audited sources, run scripts/combine_canonical_datasets.py with repeated --source ID=PATH arguments. Inspect provenance and verify feature meaning manually before training. This is a strict merger, NOT a CICFlowMeter converter.
