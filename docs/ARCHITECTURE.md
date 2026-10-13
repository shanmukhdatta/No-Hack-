# No Hack — system architecture

## Boundaries

No Hack targets one Windows machine as a local-first defensive flow monitor. It is a modular monolith, not a fleet of independent services.

~~~text
Authorized Windows network interface
  -> Npcap / Scapy collector (future phase 2)
  -> packet metadata normalization + bidirectional flow table
  -> NoHackFlow versioned feature contract (phase 1)
  -> schema/type validation
  -> offline-compatible inference pipeline
       -> XGBoost / LightGBM / CatBoost (supervised)
       -> Isolation Forest / Gaussian mixture / DBSCAN (research branch)
       -> leakage-safe OOF stacker, calibrator, uncertainty & decision rules
  -> {NORMAL, KNOWN_THREAT, NOVEL_ANOMALY, UNCERTAIN}
  -> evidence + SHAP / reason codes
  -> local SQLite + bounded event stream
  -> loopback FastAPI -> PySide6 window, tray and notifications
  -> local drift / health monitoring
~~~

Not implemented in Phase 0: every pipeline component after the settings/logging/diagnostics foundation.

## Separation of responsibilities

- config: validated process configuration, structured application logging and deployment defaults.
- capture and collector: native Windows acquisition, permission checks, packet metadata and process context.
- features: NoHackFlow version, direction, timeouts and *shared* offline/live computation.
- datasets and data: external source adapters, provenance, audit and versioned splits.
- preprocessing: fitted, train-fold-only transformations and imbalance handling.
- models and training: model factories, CV, OOF, calibration, tuning, evaluation and export.
- inference: strictly validated, manifest-matched and offline-usable inference interface.
- explainability: feature contributions and human-readable evidence.
- runtime: lifecycle, queue bounds, graceful stop/start and orchestration.
- security: access controls, model integrity, privacy and safe defaults.
- storage: local SQLite repositories, retention and audit.
- alerts: classified events and user notifications (no automatic network blocking).
- api: loopback-only FastAPI boundary with typed request/response schemas.
- ui: PySide6 presentation, no duplicated model logic.
- monitoring: service health, model drift, distribution change and alert statistics.

## Data contract and consistency

The canonical NoHackFlow schema will be versioned in Phase 1, then shared by PCAP, live capture and model training. The README lists intended flow statistics; those are a target, not a deployed schema yet. Offline dataset-specific attributes (especially NSL-KDD) may never silently substitute unavailable live features.

Training uses frozen train/validation/test splits, train-fold preprocessing, out-of-fold meta-features, calibrated confidence where justified, and one final held-out evaluation. A released model bundle carries input column ordering, feature schema version, model version, split/data provenance, and integrity hashes. Runtime fails closed on incompatible or absent models; it must not invent a risk judgment.

## Security and operational posture

Default API host is 127.0.0.1. The collector requires explicit permission and authorized monitored traffic. Persist flow metadata by default, never packet payloads. The log formatter allowlists event/component fields but callers must also avoid putting private packet data in the log message itself. No automatic blocking. Installers should not silently elevate or bundle Npcap without a license review.

## Development environments

- GitHub: permanent versioned source of truth and PR/CI review.
- Antigravity IDE on Windows: native packet capture/UI tests and final installation verification.
- Kaggle: high-compute future training on legally usable datasets; exported artifacts checked against manifest and schema locally.
