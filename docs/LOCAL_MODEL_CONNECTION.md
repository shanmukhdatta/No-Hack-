# No Hack — Real Model to Chrome Connection

**Current state:** the source code and smoke tests pass CI. **No verified real-world model bundle is committed**; training results must be produced on your approved labeled data. Synthetic fixture scores from CI are never valid security performance evidence.

## 1. Install development dependencies on Windows

Use Python 3.11 and this repository's latest **main** branch:

    git pull origin main
    py -3.11 -m venv .venv
    .\.venv\Scripts\python.exe -m pip install -e ".[dev,capture,ml-core,api]" -c requirements/dev-py311-constraints.txt

Use authorized captures only, and never publish PCAPs or identifiable endpoint metadata.

## 2. Inspect data and produce legitimate group splits

Run the five notebooks in notebooks/LEARNING_PATH.md, or use the CLI after you have a **canonical 33-feature** and independently labeled NoHackFlow v1 dataset:

    python scripts/prepare_nohack.py --input data/interim/labeled_nohackflow.csv --output data/processed/nohack_splits

For each public source, check feature/label provenance and compatibility first. The combine_canonical_datasets script only joins **verified compatible inputs**, preserving group identifiers. It never converts raw CICFlowMeter fields.

## 3. Train and export in Kaggle

The existing notebooks/nohack_kaggle.ipynb is the Kaggle handoff. On a notebook runtime with the repository installed and **your** approved dataset attached:

    python scripts/train_nohack.py --data /kaggle/working/splits --output /kaggle/working/nohack-model --folds 4

Inspect held-out metrics, group leakage, calibration, false-positive rate and quality of label annotation. Export these 3 files together from your OWN training run: hybrid.joblib, manifest.json, metrics.json. Loading untrusted joblib files can execute arbitrary code.

The trainer can use CPU for this first gradient-boosted experiment; GPU availability alone does not prove acceleration or quality.

## 4. Verify on Windows

Copy your verified model directory to artifacts/models/nohack-v1 (ignored by Git). Inspect the manifests and hashes. Start the optional local read-only model-status/inference service:

    .\.venv\Scripts\python.exe scripts/serve_local_api.py --model artifacts/models/nohack-v1 --trust-local-model

This binds **only** 127.0.0.1:8787. Check http://127.0.0.1:8787/model/status on your own machine. It will report model_connected true only after successful trusted model loading.

For manual POST /predict testing, set a long random NOHACK_API_TOKEN and supply it as the X-NoHack-Token header. Do not expose this service on a public network.

## 5. Connect the Chrome companion

Load unpacked extension/ in Chrome; install and register the native host exactly as docs/CHROME_EXTENSION.md describes, allowlisting your exact extension ID. In the extension, open **Model & MLOps** and press **Check model connection**.

- If the Windows native host or local API is unavailable, the view must say **Model not connected**.
- If the native host reaches the fixed local API and that API has loaded a verified model bundle, the view may say **Model connected**.
- Model availability does **not** start packet capture and does not imply that any displayed browser hostname was analyzed by ML.
- To create local assessments, separately run consented finite capture and scoring, or score authorized PCAP observations, using docs/CHROME_ONLY_DEVELOPMENT.md. The read-only companion can then show saved network-flow assessments.

## 6. Optional MLOps and release artifacts

After a genuine training run, log metrics without raw data:

    python scripts/log_experiment.py --model-dir artifacts/models/nohack-v1

MLflow uses a locally configured tracking URI. A UI can be launched locally with mlflow server, binding only to loopback. Generate unlabeled drift reports using scripts/report_drift.py, with a carefully chosen training reference. Drift is **not** live detection accuracy.

GitHub Actions produces a **source preview ZIP** for the Chrome MV3 extension and an **unsigned, unvalidated Windows native-host preview**. These are build artifacts, not certified distribution releases. The static GitHub Pages site is distinct from the local inference service and may require enabling Pages deployment in repository settings.

## 7. Required external acceptance

Record real held-out detection metrics, external dataset performance, post-fix Npcap packet-order behavior, Chrome UI/native host integration, model loading behavior, local API access controls, clean Windows packaging and actual Pages deployment. None of these should be invented or marked complete based solely on CI.
