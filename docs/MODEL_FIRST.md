# No Hack — model-first dataset audit

The user requested model development before Chrome/Windows UI acceptance. This independent branch does not merge or modify draft PR #4/#5, and it does not train a model yet. The existing 15-phase release gates still apply.

## Dataset strategy

- **Primary modern benchmark:** [CICIDS2017 (official UNB)](https://www.unb.ca/cic/datasets/ids-2017.html). Use its labelled MachineLearningCSV exports initially, not the very large PCAP archives.
- **External evaluation, later:** [CSE-CIC-IDS2018 (UNB)](https://www.unb.ca/cic/datasets/ids-2018.html), also described in the [AWS Open Data Registry](https://registry.opendata.aws/cse-cic-ids2018/).
- **Research architecture reproduction:** NSL-KDD, which is **not** a Windows deployment training schema.

The NoHackFlow v1 contract contains **33 fields**. CICFlowMeter fields that sound similar are not automatically the same: packet/header/payload byte counts, flow direction, timestamps, packet inter-arrival calculations and termination vary by implementation. **Do not train a purportedly deployable model by just renaming columns.** If CSV semantics cannot be aligned, we must investigate reproducible labelled PCAP -> NoHackFlow extraction with verified label matching, or keep CSV-trained models research-only.

## Task 1: authorized public CSV intake and compatibility inspection

1. Read CICIDS2017's official usage and citation conditions; download/extract the official labelled `MachineLearningCSV.zip` to `data/raw/cicids2017/` on the **local machine**, or obtain a vetted copy where the original can be verified. Do not commit datasets, browser history, traffic captures or endpoints to Git.
2. Use a clean Python 3.11 checkout of `feature/model-first-dataset-audit`. Install `nohack[dev,capture]` with the repo's pinned development constraints. No GPU or Kaggle session is needed yet.
3. Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_dataset_audit.py -v
.\.venv\Scripts\python.exe scripts/audit_dataset.py --input .\data\raw\cicids2017 --sample-rows 1000 --output .\data\interim\cicids2017-header-audit.json
```

For one actual CSV, pass its path to `--input`. Use `--hash-files` for full SHA-256 file fingerprints once the definitive dataset files are chosen (this takes longer). The audit samples up to 1000 rows **per file**, reports labels/column names/duplicate headers/row-width issues, and never exports raw rows. It explicitly outputs `deployable_mapping_verified: false`.

4. Share only the metadata-only audit JSON, test outcome and Git SHA with ChatGPT. Do not upload IP addresses, private flows or raw PCAPs. The next gate is a semantic mapping review and leakage-safe split design, before model baselines and Kaggle training.

This is **intake evidence**, not proof of model readiness, validation or Windows deployability.
