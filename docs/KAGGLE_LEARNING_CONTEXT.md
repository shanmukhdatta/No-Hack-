# Kaggle Learning Context — Companion to `plan.md`

**Purpose:** This is the durable continuation and mentoring contract for the Kaggle intensive, not a Windows-app development tracker.

## Learner objective and baseline (2026-10-26)

- Primary goal: learn **how to solve unfamiliar Kaggle problems independently at a high competitive standard**, across tabular, time series, NLP, computer vision, detection/segmentation, audio, retrieval/ranking, recommendation and new AI task types.
- Aspirational long-term goal: official Kaggle Competition Master/Grandmaster. A 10-day course cannot award tiers or guarantee medals. **Do not assert the learner has earned a title.**
- Previous knowledge: learner says basic pandas EDA is familiar (missing values, duplicates, averages, medians). Avoid unnecessarily spending days re-teaching those basics; focus on *why* and *when* analyses improve CV/generalization.
- Learner requests six substantial work tasks per day, each broken into practical checkboxes, with selected documentation, original research papers and winning-solution reviews.
- User wants hands-on building and deliberate experimentation rather than end-to-end AI-written solutions. AI should be a **technical tutor, code reviewer, debugging assistant and critic**.
- No Hack repository: `https://github.com/shanmukhdatta/No-Hack-`. This intensive may later inform its ML pipeline but **No Hack Windows capture, Chrome extension and packaging are not the 10-day learning priority**.
- Dates: 2026-10-26 through 2026-11-04, Asia/Kolkata. Scheduling is flexible. Include normal sleep, meals and breaks; do not treat "24 hours available" as a requirement to work without sleep.

## Canonical source of truth

1. `plan.md` — 10 days, 6 tasks/day, 3 subtasks/task (60 tasks, 180 checkboxes). Task IDs are `D01.T01` through `D10.T06`.
2. `docs/KAGGLE_LEARNING_CONTEXT.md` — this contextual contract and continuity notes.
3. Real outputs: learner's notebooks, experiment files, notes and Kaggle submissions. **Never fabricate an output merely because a checkbox exists.**

**Baseline progress as of creation:** 0/180 subtasks confirmed by user. Prior work in other projects does not automatically mark these boxes completed.

## Strategy review update (2026-10-26)

The 10-day syllabus was independently cross-checked against the official Kaggle progression guidance and documented NVIDIA Grandmaster methods. See `docs/KAGGLE_STRATEGY_AUDIT.md` for findings, limitations and source links. Maintain the user-requested 60 tasks and 180 checkboxes.

**Active competition through-line:** On D01.T01 select an active medal-eligible competition if a feasible one exists; verify competition-specific rules, evaluation, permitted model/data sources, final entry format and deadline. Maintain a short experiment journal for that same competition throughout D02–D10. Reevaluate at D09.T06; do not present historical Playground results as proof of medal attainment.

**Technique priority:** scientific validation, honest baseline, error analysis and reproducibility before expensive model/tuning options. Optuna and ensembling are conditional on measured benefit; model performance is a property of data/task/CV, not a ranking of libraries. Use an explicit compute/trial budget for every experiment. Days 8–9 contain breadth-first micro-labs; if compute/data are not available, record a BLOCKED status rather than checking off work not completed. Never encourage continuous 24-hour studying; preserve sleep and breaks.

## Teaching workflow when learner returns

When learner asks to "start day 3", "continue D05.T04", or sends a partial notebook:

1. Read the specific task, its three subtasks, artifact and exit gate in `plan.md`.
2. Ask the learner to state their intended approach in 2–5 lines when appropriate. Avoid re-asking information they already supplied.
3. Give the relevant concept briefly (definitions, intuition, when to use, failure modes), with a canonical source.
4. Give **one runnable, bounded mini-exercise** or one incremental implementation target at a time. The learner performs the first attempt. Respect a direct request for full code if they need it, but always explain tradeoffs.
5. Review code/outputs and explain what evidence supports or contradicts the hypothesis.
6. When debugging, request the exact error, relevant code cell and environment only if they aren't available. Diagnose root cause and supply minimal verified fix.
7. Finish with: what passed, what still failed, which checkbox the learner may mark, and the next task ID.
8. Do not claim code was run, a Kaggle submission occurred, or a medal earned unless tool/user evidence actually exists.

**Experiment loop:** hypothesis → baseline → correct folds → one controlled change → measure per-fold metric/time → inspect failures → decide keep/revert → log evidence.

## Competitor mindset: core principles

- **Validation is the strongest defense against false progress.** Choose folds that simulate the hidden evaluation, not a convenient split. Group leakage, time leakage, repeated content and preprocessing/target leakage are red flags.
- Define local scorer matching the competition's evaluation metric, including special treatment for imbalanced labels, ranking groups, detection IoU/mAP and forecasting horizons.
- EDA should generate testable hypotheses, including train-test feature shift, target distributions, label ambiguity, duplicates, temporal/group structure and segment-wise errors. Graphs without questions do not count as evidence.
- Keep feature creation and fit-only transformations inside appropriate training folds. Target/frequency encoding requires particular care.
- Start with cheap baselines and run diverse model families. Use model complexity only if held-out improvements justify it.
- Optuna belongs **after** data audit and stable CV; choose bounded search spaces, trial time caps, TPE/random samplers, early stopping/pruning. It cannot repair leakage or bad labels.
- OOF stacking must never use in-sample predictions as meta-features. Tuning, calibration, threshold selection, pseudo-labeling and blending must follow the same fold/test separation.
- Reproducibility: record dataset version, git revision, input schema, random seed, folds, parameters, software versions, metrics, out-of-fold predictions and runtime.
- The public Kaggle leaderboard is a noisy signal. Preserve a reliable offline validation procedure and do not exhaust submissions just to fit the public score.
- Verify each competition's licensing, pretrained model/external data policy, AI assistance policy, team-size rules, GPU/network constraints and medal eligibility before participating.

## What "complete" means

Mark a subtask `[x]` **only** if the learner has produced its requested artifact, independently understood it, and checked the key result.

Task completion = all three subtasks checked + stated artifact saved + learner can explain the method. Day completion = all six tasks have reviewed artifacts and the Day Exit Goal is met. If GPU/time/data access blocks an experiment, mark it as `BLOCKED` in the journal and distinguish a conceptual survey from a trained model.

## Daily evidence artifact directory (suggested, not mandatory)

```text
kaggle_masterclass/
  experiment_log.csv
  progress_journal.md
  day01/ ... day10/
    notebooks/
    figures/
    reports/
    submissions/
  reusable/
    metrics.py
    validation.py
    pipelines.py
    experiments.py
```

For each day record: **completed task IDs, links to artifacts, true measured metrics, bug log, most surprising finding, what you would change next, and the next checkpoint.**

Do not commit licensed/private data, huge weights, API tokens, Kaggle credentials or unauthorized images/records to a public repository. Generated notebooks and reports may be public only when rules and licensing allow.

## Cross-modal compass

| Problem evidence | Start with | Validation risk | Typical next lever |
|---|---|---|---|
| Small/medium tabular classification | linear/logistic + LightGBM/XGB/CatBoost | entity/time leakage | new features, tuned boosting, calibrated blend |
| Tabular regression | median/linear + boosting | hidden grouping/target skew | target transform, residual analysis |
| Time series | naive/seasonal naive + lag model | using future info | rolling CV, horizon-specific error |
| NLP short text | TF-IDF + linear classifier | author/topic duplicates | pretrained transformer |
| CV classification | pretrained ResNet/EfficientNet | near duplicates, subject leakage | augmentations/fine-tuning/TTA |
| CV detection / segmentation | lightweight pretrained detector or mask model | box/mask quality and scene grouping | size-aware errors, mAP/IoU/Dice |
| Audio | log-Mel baseline / pretrained embeddings | same speaker/session leakage | augmentation, robust folds |
| Recommenders/ranking | popularity and retrieval baseline | future interactions / user leakage | candidate generation, NDCG-based reranking |
| Multimodal / generative | independent modality baselines | alignment, subjective evaluation | fused encoders, evaluation reliability |
| Graph | feature baseline | edge/node overlap | graph models where justified |

## Research and practitioner reading ladder

**Competition practice and EDA**
- [Kaggle competition guide](https://www.kaggle.com/learn-guide/kaggle-competitions)
- [Kaggle Learn](https://www.kaggle.com/learn)
- [NVIDIA: 7 battle-tested tabular methods](https://developer.nvidia.com/blog/the-kaggle-grandmasters-playbook-7-battle-tested-modeling-techniques-for-tabular-data)
- [NVIDIA: Grandmaster strategies](https://developer.nvidia.com/blog/kaggle-grandmasters-unveil-winning-strategies-for-data-science-superpowers/)
- [NVIDIA: Competition + community insights](https://developer.nvidia.com/blog/competition-and-community-insights-from-nvidias-kaggle-grandmasters/)
- [NVIDIA: AI-assisted competition experiments (2026)](https://developer.nvidia.com/blog/winning-a-kaggle-competition-with-generative-ai-assisted-coding/)

**Validation and HPO**
- [scikit-learn common pitfalls](https://scikit-learn.org/stable/common_pitfalls)
- [Optuna tutorials](https://optuna.readthedocs.io/en/stable/tutorial/)
- [Optuna: A Next-generation Hyperparameter Optimization Framework](https://arxiv.org/abs/1907.10902)

**Model papers**
- [XGBoost](https://arxiv.org/abs/1603.02754), [LightGBM](https://arxiv.org/abs/1711.01681), [CatBoost](https://arxiv.org/abs/1810.11363)
- [Attention Is All You Need](https://arxiv.org/abs/1706.03762), [BERT](https://arxiv.org/abs/1810.04805)
- [ResNet](https://arxiv.org/abs/1512.03385), [U-Net](https://arxiv.org/abs/1505.04597)
- [Temporal Fusion Transformers](https://arxiv.org/abs/1912.09363)

**Implementation**
- [Hugging Face text classification](https://huggingface.co/docs/transformers/tasks/sequence_classification)
- [Hugging Face image classification](https://huggingface.co/docs/transformers/tasks/image_classification)
- [PyTorch transfer learning](https://docs.pytorch.org/tutorials/beginner/transfer_learning_tutorial)
- [PyTorch audio/domain tutorials](https://docs.pytorch.org/tutorials/domains.html)

Papers need not be read cover-to-cover immediately. For each: identify problem, method, key experiment, assumptions and how to test it on a toy dataset. Keep compute budgets proportional to the available hardware.

## Progress snapshot template

```text
Date:
Current checkpoint: D__.T__
Completed since last chat:
Subtasks: __/180
Artifact paths/links:
Observed metric (if any):
Hypothesis and result:
Bug / uncertainty:
Next proposed action:
```

## Copy-paste prompt for a new chat

> Continue my Kaggle Grandmaster-track 10-day masterclass from the repository `shanmukhdatta/No-Hack-`. Read `plan.md` and `docs/KAGGLE_LEARNING_CONTEXT.md`. My current checkpoint is D__.T__, and these checkboxes are complete: ____. Act as a rigorous Kaggle Grandmaster-level mentor: check my reasoning, teach only the necessary concept, give one hands-on exercise, review my own implementation, detect leakage and invalid evaluation, and identify the exact next checkbox. Do not fabricate runs or claim that I have reached an official Kaggle tier.
