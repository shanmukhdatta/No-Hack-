# Chrome-only No Hack implementation and Kaggle handoff

## Product contract

Chrome is the **only graphical product** in this revision. There is no
PySide6 desktop application, installer or Chrome Web Store release in scope.
Chrome Manifest V3 cannot read low-level Windows network packets or map each
device flow reliably to a particular browser tab. The authorized, optional
Windows metadata collector and Native Messaging host remain separate.
Browser indicators are deterministic URL metadata rules, never ML verdicts.

The native host only answers `ping`, `status`, and `recent_assessments`.
It cannot remotely launch capture or training. It returns the latest ten
local flow assessments without IP addresses, process IDs or raw features.
The user separately controls the collector and must explicitly authorize it.

## Model architecture

33 canonical NoHackFlow v1 fields -> three supervised models (XGBoost,
LightGBM and CatBoost) + Isolation Forest and diagonal GMM ->
group-aware out-of-fold meta-features -> Logistic Regression stack ->
separate validation calibration and known-threat threshold selection ->
NORMAL / KNOWN_THREAT / NOVEL_ANOMALY / UNCERTAIN. A separate CatBoost
attack-family classifier trains only if multiple adequately represented,
independently labeled attack families are present. No fake attack-family
claims are produced when it is unavailable. DBSCAN remains research-only;
standard DBSCAN has no supported out-of-sample predict contract.

Novel anomaly means unusual behavior, NOT a demonstrated zero-day attack.
The risk index is not a probability of compromise.

## CRITICAL: dataset compatibility

CICIDS2017 MachineLearningCSV was generated with CICFlowMeter, whose fields,
flow direction, packet length and lifetime definitions have not been shown
compatible with NoHackFlow. **Do not rename columns to pretend compatibility.**
Use the CSV header auditor to inspect it, but do not train the deployable model
from its unverified columns. The current training code correctly requires an
exact, independently labeled NoHackFlow v1 dataset. At least eight independent
groups, both benign and attack labels, and no duplicated feature vectors
across splits are required. `group_id` must designate independent
scenarios/hosts/sessions or time periods, NOT an arbitrary ID per flow.

One defensible path is to extract canonical features from authorized
labeled PCAPs. For every completed flow, join the exact `flow_id` to a
trusted annotation table with columns `flow_id,label,group_id`. Do not
mark every flow during an attack day malicious. Verify timestamps, endpoints,
packet drops and flow matching locally. Useful commands:

```powershell
python scripts/audit_dataset.py --input data/raw/cicids2017 --sample-rows 1000 --output data/interim/audit.json
nohack replay-pcap --input data/raw/authorized.pcap --output data/interim/replay.jsonl
python scripts/export_labeled_pcap.py --pcap data/raw/authorized.pcap --annotations data/raw/verified_annotations.csv --output data/interim/labeled_nohackflow.csv
```

Replay JSONL contains endpoint context: keep it private and never upload it
or raw private PCAPs to Kaggle. The annotation flow IDs are deterministic
correlation hashes, not anonymization of identifiers.

## Antigravity: Windows preparation and local scoring

Clone **branch `feature/chrome-only-complete-stack`** and use Python 3.11:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev,capture,ml-core]" -c requirements/dev-py311-constraints.txt
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m mypy src/nohack
```

Prepare group-disjoint labeled data and train on Kaggle (next section).
Copy **only your own verified model bundle** back into a local directory,
such as `artifacts/models/nohack-v1/`. Loading joblib from untrusted
sources can execute code: never download and run random bundles.

For deterministic offline verification after training:

```powershell
.\.venv\Scripts\nohack.exe replay-store --input data/raw/authorized.pcap --database "$HOME\.nohack\observations.db"
.\.venv\Scripts\python.exe scripts/score_observations.py --bundle artifacts/models/nohack-v1 --database "$HOME\.nohack\observations.db" --trust-local-bundle
```

To capture new data for a **finite** interval on a machine/interface you
own or have permission to inspect, use a locally installed Npcap driver
subject to its license, then:

```powershell
.\.venv\Scripts\nohack.exe capture-interfaces
.\.venv\Scripts\python.exe scripts/capture_and_score.py --interface "YOUR-INTERFACE" --seconds 10 --database "$HOME\.nohack\observations.db" --bundle artifacts/models/nohack-v1 --authorized --trust-local-bundle
```

These are user-invoked commands; the extension never starts packet capture.
The model operates on completed network flows. It does not perform full
browser-tab correlation, continuous monitoring, payload inspection or
automatic traffic blocking.

For native host packaging and registration, follow
`docs/CHROME_EXTENSION.md`: build your own trusted executable with
PyInstaller, register it for the exact Chrome extension ID, and view
Companion -> Refresh local assessments. Before training, or without the
host installed, the UI must show unavailable/disconnected rather than
fabricating classifications.

## Kaggle handoff

Use `notebooks/nohack_kaggle.ipynb` and upload an approved, canonical
labeled NoHackFlow dataset to the Kaggle notebook's input. It must have the
33 exact columns plus `label` and `group_id` (optional `attack_family`).
Kaggle GPU hardware may be enabled, but this initial reference trainer uses
CPU-compatible gradient-boosted models unless specifically benchmarked for
GPU. GPU availability does not establish that a model is deployable.

Run:

```bash
python scripts/prepare_nohack.py --input /kaggle/input/YOUR_DATASET/flows.csv --output /kaggle/working/splits
python scripts/train_nohack.py --data /kaggle/working/splits --output /kaggle/working/nohack-model --folds 4
```

Keep the final `hybrid.joblib` and `manifest.json` together, check their
hashes on the target machine, and inspect `metrics.json` and output
predictions before live testing. No public dataset, Kaggle GPU run or trained
artifact has been executed by the code author yet.

## Quality and acceptance gates (user to run later)

1. Linux/Windows CI, lint, mypy and Node tests must pass at the **latest**
   Git SHA. ML smoke tests should run with `.[ml-core]`.
2. Audit datasets, annotation provenance, group/time leakage, model metrics,
   probability calibration, false-positive rates, family taxonomy and drift.
3. Verify the PCAP replay vs actual Windows Npcap NoHackFlow parity and
   post-fix out-of-order packet proportions.
4. Run finite authorized capture + model scoring + Chrome native host on
   your Windows machine; verify no fake browser-domain association.
5. Inspect Chrome permissions, local retention, history deletion, pause,
   accessibility and extension packaging before considering any public release.

The code being present is not the same as an accepted or production-ready
product. Until labeled data has been supplied and models run, all ML
predictions remain unavailable.
