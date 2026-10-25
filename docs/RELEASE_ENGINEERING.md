# No Hack — Release Engineering Tracker

As of 2026-10-25. Statuses are about CODE existence, never claims of live detection. Development branch: feature/release-engineering-2026 based on PR #7.

Legend: DONE = authored source/docs; CODED = implementation exists awaiting integration acceptance; PARTIAL = restricted scope; PENDING = not delivered.

| ID | Deliverable | Status | Evidence / blocker |
|---|---|---|---|
| T01 | Audit PRs and code | DONE | Reviewed PR #7 |
| T02 | Canonical schema | CODED | 33 fields unchanged |
| T03 | Windows capture | CODED | Live post-fix hardware retest pending |
| T04 | Runtime and SQLite | CODED | PR #7 |
| T05 | Dataset provenance and audit | CODED | Requires verified labels |
| T06 | Leakage-safe splitting | CODED | Real group validation pending |
| T07 | Beginner audit notebook | DONE | 01 notebook |
| T08 | EDA notebook | DONE | 02 notebook |
| T09 | Splits notebook | DONE | 03 notebook |
| T10 | Supervised baselines notebook | DONE | 04 notebook |
| T11 | Advanced hybrid notebook | DONE | 05 notebook |
| T12 | Boosting trio | CODED | XGBoost/LightGBM/CatBoost |
| T13 | Anomaly models | CODED | IForest and GMM; DBSCAN deferred |
| T14 | Hybrid OOF stacking | CODED | Real holdout pending |
| T15 | Metrics and group slices | CODED | Helpers and tests |
| T16 | SHAP explainability | PARTIAL | XGB component only |
| T17 | Model artifact integrity | CODED | PR #7 loader |
| T18 | Loopback FastAPI | CODED | Tokened prediction; CI pending |
| T19 | Chrome UI | CODED | 5 tabs, light yellow theme |
| T20 | Native Messaging | CODED | Read-only bridge |
| T21 | MLflow logging | CODED | Genuine runs only |
| T22 | Drift monitoring | CODED | PSI, not accuracy |
| T23 | Chrome source ZIP | CODED | Preview workflow |
| T24 | Windows host packaging | CODED | Preview workflow; installer pending |
| T25 | GitHub Pages site | CODED | Needs Pages setting and deploy check |
| T26 | Security and external acceptance | PENDING | Physical tests and release gates |
| T27 | Merge and release | PENDING | Only after CI and acceptance |

## Resume in Antigravity

1. Check the PR and exact SHA. Run Ruff, format check, pytest, and the Node browser tests.
2. Supply an independently labeled canonical NoHackFlow dataset, not renamed CICFlowMeter columns; go through notebooks/LEARNING_PATH.md.
3. Train, audit held-out performance, and export only a bundle you trained. No dummy artifact is certified.
4. Optionally start the local API with scripts/serve_local_api.py. For manual scoring set an unpredictable NOHACK_API_TOKEN environment variable of at least 24 characters.
5. Record PR-AUC, recall, false positives, calibration, heldout group slices and post-fix Windows Npcap parity; log genuine runs through scripts/log_experiment.py.
6. Enable Pages with GitHub Actions source in repository settings and verify its real deployment. Independently test Chrome Native Messaging registration on Windows.

## Honest delivery boundary

- Chrome cannot inspect operating-system packets or prove a website safe.
- Synthetic test results are not intrusion detection performance metrics.
- Extension and native bridge never start packet capture automatically.
- The public static site is not an ML deployment. No private models/data or Windows credentials should be uploaded.
- A signed Windows installer, validated real detection model and Chrome Web Store publication are NOT complete.
