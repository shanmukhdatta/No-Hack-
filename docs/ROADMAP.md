# No Hack — authoritative 15-phase development roadmap

**Status:** active 2026-10-13. This is the agreed execution order, Phases 0–14. The original README section 42 retains an older 13-phase research-oriented sequence for reference. It is not the current phase tracker; all of its promised features remain in scope and are mapped below.

Every phase: inspect the prior branch/commit, implement reusable source and tests, run quality checks, record real evidence in PHASE_LOG, open a reviewable PR, and have Windows-specific behavior checked in Antigravity when necessary. GitHub is the source of truth; Kaggle is used for heavy training when needed, not for production inference.

| Phase | Outcome and deliverables | Exit gate |
|---|---|---|
| **0 — Foundation** | Python 3.11 src-layout install, settings, structured logs, CLI diagnostics, module boundaries, pytest/Ruff/mypy, GitHub CI, data/artifact policy and docs | Package/CLI/checks succeed, CI status recorded, Windows smoke pending/verified explicitly |
| **1 — Canonical features** | Define versioned NoHackFlow schema/manifest, flow direction/time/statistics, schema validation and deterministic offline/live parity fixtures | Identical supported features across both input paths; unsupported NSL-KDD columns cannot enter live model |
| **2 — Windows capture** | Authorized Scapy + Npcap capture, psutil context enrichment, bidirectional flow aggregation, expiry, bounded work and Windows tests | Controlled Windows traffic yields correct NoHackFlow records; no payload persistence |
| **3 — End-to-end skeleton** | Wire collector, feature contracts, service lifecycle and event interfaces, including graceful stops and health reporting; no invented ML predictions | Traceable flow records travel through deterministic pipeline safely |
| **4 — Dataset engineering** | NSL-KDD research adapter and baselines preparation, CICIDS2017 and CSE-CIC-IDS2018 adapters, provenance, audits, EDA, leak-safe split, Parquet | Reproducible dataset reports and frozen splits; label/time/group leakage reviewed |
| **5 — Supervised learning** | Logistic Regression/Random Forest baselines; XGBoost, LightGBM, CatBoost; train-fold-only feature fitting, imbalance studies, Optuna and cross-validation | Validated model probabilities, honest held-out metrics and MLflow provenance |
| **6 — Anomaly research** | Isolation Forest, GMM, DBSCAN with train-only scaling/dimensionality reduction, score normalizing and anomaly evaluation | Comparable out-of-fold anomaly features; DBSCAN only deploys if runtime feasibility is demonstrated |
| **7 — Hybrid fusion** | Strict out-of-fold stacking, agreement/disagreement meta-features, probability calibration, risk thresholds, NORMAL / KNOWN_THREAT / NOVEL_ANOMALY / UNCERTAIN | Leakage-audited fused predictions and explicit uncertainty rules |
| **8 — Evaluation and XAI** | Untouched held-out evaluation, external shift tests, calibration, per-class analysis, ablations, SHAP, permutation and reason codes | Explainable findings and model card without invented precision/accuracy |
| **9 — Runtime inference** | Versioned model bundle, feature/order contract enforcement, integrity manifest/checksums, safe failure, bounded local inference, SQLite persistence and retention | Compatible models load locally; bad/incompatible models fail safely |
| **10 — Local API** | FastAPI/Pydantic on loopback only, validated flow/status/event routes, access controls, health and optional streaming | Tested API/DB/inference contract with no public binding by default |
| **11 — Windows desktop** | PySide6 dashboard, alerts and explanations, tray, notifications, settings, start/stop controls, accessible error states | Real end-to-end UI interaction works on Windows |
| **12 — Monitoring/MLOps** | MLflow tracking, model lineage, drift/reference windows (Evidently or tested checks), latency, service health, alert review | Drift described accurately; unlabeled streams never claim real-time accuracy |
| **13 — Hardening/packaging** | Threat model, permissions, safe local storage, log redaction, CI expansion, reproducible Windows PyInstaller package and Npcap licensing review | Installer and clean Windows machine smoke tests; no secret/dataset distribution |
| **14 — User validation and release** | Usability, stability, controlled detection checks, resource profiling, documentation, honest limitations, installer/release and demo | Tested installable Windows app and reviewable reproducibility evidence |

## Non-negotiable cross-phase contracts

- NoHackFlow features in a deployed model must be obtainable from actual live traffic. NSL-KDD is a research benchmark, not proof of live deployment compatibility.
- Dataset, scenario, period or host-level leakage requires explicit attention. Calibration, meta-features and thresholds must never use untouched test data.
- Inference is local-first; never describe a flow as provably secure or an anomaly as proven zero-day exploitation.
- Use model, feature-schema and data versions plus hashes/manifests. Model artifacts are untrusted until explicitly verified. No arbitrary untrusted pickle execution.
- Protect users: capture only owned/authorized traffic; retain metadata rather than packet payloads. Bind APIs to loopback, minimize sensitive logs, manage retention.
- GitHub branches/PRs track reviewed code. Windows is verified in Antigravity; Kaggle is used only for high-cost ML training and exported verified artifacts.
- No cloud infrastructure, Kafka, Kubernetes or microservices are part of the initial local application.

## Historical README mapping

The original README's phases 1–5 map mainly to current phases 4–8, its modern feature/collector work maps to 1–2, inference maps to 9, API/storage maps to 9–10, UI to 11, monitoring to 12, and packaging/release to 13–14. This is a sequencing change, not a feature deletion.
