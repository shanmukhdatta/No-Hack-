# No Hack — engineering decisions (ADR ledger)

| ID | Decision | Rationale / implications |
|---|---|---|
| D-001 | Modular Python 3.11 src-layout package, setuptools build | Broad Windows/ML ecosystem support; a small installable core without ML dependencies |
| D-002 | Local-first modular monolith | FastAPI + PySide6 + SQLite in one local application; no Kafka, Kubernetes or cloud inference |
| D-003 | Optional dependency extras (dev, ml, capture, api, ui, packaging) | Avoid unnecessary dependencies, privileges or large installs for Phase 0 |
| D-004 | Environment variables prefixed NOHACK_, no automatic .env load | Simple, testable process configuration; no secret-management dependency introduced |
| D-005 | Reject non-loopback API hosts at configuration boundary | Minimize accidental external exposure; later API authentication still required |
| D-006 | App-owned JSON logs with field allowlist; no root logger mutation | Support machine inspection while preventing uncontrolled extra-field leakage; messages must still be privacy reviewed |
| D-007 | NoHackFlow training-serving contract before deployable model | Modern flow features must be identical offline/live; NSL-KDD original attributes are research-only when incompatible |
| D-008 | Separate model research from runtime inclusion | DBSCAN is included in experiments but not promised as a low-latency online predictor absent evidence |
| D-009 | Out-of-fold stacking and untouched holdout | Avoid stacked-model leakage, misleading metrics and unsafe thresholds |
| D-010 | Four states, including UNCERTAIN | A detector never proves traffic is secure or that novelty is malicious |
| D-011 | GitHub default main stays stable; phase-specific PR branches | Audit trail, reproducible reviews and a safe path to each next phase |
| D-012 | GitHub/Antigravity/Kaggle division of labor | Code and docs on GitHub; native Windows checks locally; heavy training on Kaggle only when appropriate |
| D-013 | Keep original README section 42 intact, add canonical 15-phase ROADMAP | Historical README describes a 13-phase research-first ordering; finalized Phases 0–14 reorganize, not remove, that work |
| D-014 | Ignore datasets, model artifacts, captures, SQLite and secrets | Avoid repository leaks and large binary history |
| D-015 | CI only tests unprivileged foundation code in Phase 0 | Real Windows capture and desktop packaging tests belong to dedicated later phases |
| D-016 | Dev dependencies bounded in pyproject; future fully resolved lock needed | Avoid pretending top-level ranges are a transitive dependency lock; record installed versions with pip freeze on each reviewed test run |

These decisions may be superseded only by a documented ADR with a reason and migration impact.
