# No Hack — Consolidated Component Implementation

Source-code map for later editing, not a certificate of model accuracy or public deployment.

## Ownership: edit the relevant component directly

| Component | Existing/new source |
|---|---|
| Data capture and replay | src/nohack/capture/ |
| 33-feature contract | src/nohack/features/ |
| Private PCAP flow annotation review | scripts/review_pcap_annotations.py |
| Verified PCAP CSV exporter | scripts/export_labeled_pcap.py |
| Multiple dataset provenance merge | scripts/combine_canonical_datasets.py |
| Audit and group-isolated splits | src/nohack/datasets/prepare.py |
| Five study notebooks | notebooks/ |
| Supervised Logistic/RandomForest baselines | src/nohack/models/baselines.py |
| XGBoost LightGBM CatBoost and IF/GMM | src/nohack/models/hybrid.py |
| Group OOF stacking/calibration | src/nohack/training/hybrid.py |
| One-command genuine experiment | scripts/run_experiment.py |
| Synthetic-only software demo | scripts/demo_model_pipeline.py |
| Safe local model loading/inference | src/nohack/inference/hybrid.py |
| SQLite local batch scoring | src/nohack/inference/scoring.py |
| Honest heldout metrics | src/nohack/evaluation/report.py |
| Calibration diagnosis | src/nohack/evaluation/calibration.py |
| Measured latency benchmarks | src/nohack/evaluation/latency.py |
| XGBoost component SHAP | src/nohack/explainability/shap_report.py |
| MLflow run import | scripts/log_experiment.py |
| Population drift PSI | src/nohack/monitoring/drift.py |
| Assessment aggregation | src/nohack/monitoring/assessment_metrics.py |
| Alert debouncing | src/nohack/monitoring/alerts.py |
| SQLite observation and prediction stores | src/nohack/storage/ |
| Fixed loopback API | src/nohack/api/app.py |
| Chrome Native Messaging | src/nohack/native_host.py |
| Chrome popup/dashboard | extension/ |
| Optional desktop preview | src/nohack/ui/desktop.py |
| Public static site | site/ |
| Unsigned preview packaging | scripts/package_extension.py |
| GitHub Actions checks | .github/workflows/ |
| Security/privacy review | docs/SECURITY_REVIEW.md |
| Code inventory and evidence gate | src/nohack/engineering/readiness.py |

## One complete engineering flow

1. Run `python scripts/check_project.py` to verify source presence (not deployment).
2. Run `python scripts/demo_model_pipeline.py --output-dir artifacts/demo/nohack-smoke` for a labeled-SYNTHETIC software smoke, never real IDS accuracy.
3. For genuine data: use only an authorized raw PCAP, `scripts/review_pcap_annotations.py` template/approve, then `scripts/export_labeled_pcap.py`. Exact flow-level evidence is required; filenames and attack-day labels are not evidence.
4. Run `python scripts/run_experiment.py --input VERIFIED.csv --output artifacts/experiments/RUN01` for separate grouped splits, supervised baselines, OOF hybrid training, metrics and export.
5. Run `python scripts/benchmark_inference.py --bundle artifacts/experiments/RUN01/model --input VERIFIED.csv --output artifacts/reports/latency.json --trust-local-bundle` for measured device latency.
6. Optionally log to local MLflow using `scripts/log_experiment.py`; check PSI through `scripts/report_drift.py`. Neither computes real accuracy without ground truth.
7. Run `python scripts/serve_local_api.py --model artifacts/experiments/RUN01/model --trust-local-model`, register the exact Native Messaging origin, then open Chrome's Model & MLOps panel.
8. Optional local UI preview: `python scripts/desktop_preview.py` with PySide6 installed. It is not a signed Windows release and never starts capture.

## Scope and edit policy

- Preserve the canonical 33-feature contract and version changes instead of relabeling incompatible CICFlowMeter columns.
- Do not add object detection for tabular NoHackFlow records: bounding-box object detection is a different ML task. Supervised binary and family classification is implemented instead.
- Raw PCAP, endpoint addresses, experiment databases, private labels, signed release keys and real data stay out of Git.
- Local risk index is not probability of compromise; component SHAP is not a causal full-stack explanation.
- Model code, testing, UI, packaging and site can be complete as source without being clinically/operationally or security validated.
- Release still requires independent labeled test traffic, false-positive review, physical Windows/Npcap parity, Chrome host tests, public site deployment, store publishing and packaging review.
- `docs/release_evidence.example.json` is only a human evidence collection template. No self-attestation proves security certification.

## Extension points

Each component has a Python module or documented frontend folder. Keep modifications small, preserve public contracts, include a test and update the release tracker. Use a new reviewed PR for changes. Do not overwrite historical tests or fabricate evaluation measurements.
