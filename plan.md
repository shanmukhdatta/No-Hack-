# Kaggle Grandmaster-Track: 10-Day Hands-on Masterclass

> **Start:** 2026-10-26 (Asia/Kolkata) · **Finish:** 2026-11-04 · **Priority:** Kaggle skills, not the No Hack Windows app.
> **Outcome:** A reusable, evidence-based competition-solving workflow across modalities. **Not a promise of attaining Kaggle Grandmaster status in 10 days.** Official tiers require medals from eligible competitions and cannot be granted by completing a curriculum.

## Rules of the masterclass

- There are **10 days × 6 tasks = 60 tasks**, each with **3 checkable subtasks = 180 checkpoints**. Keep the boxes unchecked until you complete the work.
- You already know mean/median, ordinary null/duplicate handling and basic EDA. Day 1 is a structured **review**, not a beginner course.
- Use the full day for learning, implementation and recovery; **do not work 24 hours continuously**. Aim for roughly 7–10 focused hours if sustainable, with normal sleep, meals and breaks.
- The process for **every** task is: read just enough theory → make a hypothesis → build a tiny test → implement yourself → inspect results → record failures and next steps.
- Never optimize repeatedly against the public leaderboard. Use correct competition-local validation, respect licenses/rules and keep any test labels unavailable for selection.
- This plan spans *all major competition modalities*, but **10 days is an introductory intensive to each modality**, not full professional mastery of every field. Specialize through future eligible competitions.
- **No Hack usage:** its ML system may serve as a later independent case study; do not spend this sprint on Chrome/Windows deployment.
- **AI policy:** You write the first attempt. Ask an assistant for explanations, critiques, examples and debugging **only after recording your current reasoning**. Verify all AI-generated claims and tests.

## Reusable experiment evidence

Maintain `experiments.csv` (one experiment per row): `id, day, competition, modality, dataset_version, fold_scheme, seed, metric, hypothesis, change, model, hyperparameters, runtime, fold_scores, mean_score, std_score, delta_vs_baseline, decision, failure_notes, artifact_path`. Keep a short daily journal of *why* an idea worked or failed.

**HPO rule:** Optuna is a search tool, not a substitute for data understanding. Tune only after establishing stable folds, a clear metric, a trustworthy baseline and a compute budget; use pruning/early stopping as appropriate. Freeze the final configuration before evaluating on a true holdout.

## Competition selection and medals

Kaggle's current progression has Competitions, Code and Datasets tracks. A Competitions Grandmaster is earned by qualifying competition medals; typically Getting Started, Playground and Community competitions do **not** award points/medals. Always read an individual competition's overview for eligibility. See [official progression](https://www.kaggle.com/progression/competitions) and [competition guide](https://www.kaggle.com/learn-guide/kaggle-competitions). An excellent 10-day outcome is several reproducible mini-projects and one independently reasoned competition solution.

## Cross-checked execution strategy (2026-10-26)

See [the Kaggle strategy audit](docs/KAGGLE_STRATEGY_AUDIT.md) for the full review and sources.

**Primary competition thread:** On Day 1, identify an active contest and determine whether it is medal-eligible. Set up the contest's permitted data, metric, folds, budget and baseline. Revisit this *same* competition for a short, documented session on each subsequent day, even as daily labs introduce other task types. A Playground/Getting Started contest is valid practice, **not** a medal shortcut.

**Core sequence for every modality:** (1) understand task/rules and target; (2) audit data and label provenance; (3) choose folds matching hidden-test construction; (4) build the simplest complete baseline; (5) do controlled feature/model/hyperparameter experiments; (6) compare per-fold gains, runtime and error slices; (7) only then blend/stack; (8) freeze and produce reproducible submissions. Avoid training complex models before validation works.

**Study priorities:** P0 = valid folds, metrics, baseline, error analysis, reproducibility; P1 = targeted feature engineering, strong models, calibrated/tuned experiments, proper OOF ensembles; P2 = expensive multi-level stacks, pseudo-labeling, RAPIDS acceleration and speculative deep architectures. If a P2 activity cannot be finished on available compute, record the blocker, demonstrate a smaller equivalent, and keep uncompleted boxes unchecked.

**Optuna budgets:** start with a tiny toy study (5–15 trials), then run bounded studies per model/task only once the baseline is stable. Log trial counts, runtime, best CV score, seed and fold variability; do not infer that Optuna is universally better than manual decisions or that tuning fixes leakage.

**Deep-learning feasibility:** Days 6–8 combine small hands-on studies and model/format surveys. Prioritize at least one carefully validated training experiment; use pretrained inference demonstrations for additional modalities when time/GPUs are constrained. Do not treat brief exposure to a model as mastery.

**Daily closing check (not an extra task):** Log one application/limitation relevant to your Day-1 competition, what changed, and whether any submission or score was actually measured. Reserve time for sleep, food and breaks rather than continuous 24-hour work.

## Daily task checklists

## Day 01 — Advanced foundations: EDA, ML, metrics, tuning and competition anatomy

**Date:** 2026-10-26  
**Day exit goal:** Build one reusable competition skeleton and demonstrate that you understand why each part exists.

### D01.T01 — Competition reconnaissance

- [ ] Read an active competition's Overview, Data, Evaluation, Rules, Timeline and Code tabs; record rules on external data and AI assistance.
- [ ] Write down task type, data modality, target, prediction unit, metric, runtime constraints, final submission format.
- [ ] Contrast Getting Started, Playground and medal-eligible competitions; identify one active eligible contest, record its rules/deadline and choose a continuing competition thread without treating practice ranks as medals.

**Artifact:** `competition_brief.md`

### D01.T02 — Revise the full EDA taxonomy

- [ ] Build a checklist of univariate: numeric/categorical distributions, tails, missingness, outliers, unique cardinality.
- [ ] Review bivariate: feature-target association, category vs target, nonlinear relationships; multivariate: interactions, correlation clusters, segments.
- [ ] Demonstrate three plots/statistics that answer actual hypotheses rather than plotting every column.

**Artifact:** `eda_taxonomy.md + three hypothesis-driven graphs`

### D01.T03 — Review ML task and method taxonomy

- [ ] Make a decision tree for classification, regression, ranking, forecasting, detection, segmentation, retrieval, anomaly detection and generation.
- [ ] Distinguish supervised, unsupervised, semi/self-supervised and transfer learning with one appropriate example each.
- [ ] For each task, name a naive baseline, stronger model family, common leakage source and correct metric.

**Artifact:** `model_selection_map.md`

### D01.T04 — Metrics and validation bootcamp

- [ ] Implement or verify accuracy/F1/PR-AUC/ROC-AUC/logloss/RMSE/MAE/SMAPE/NDCG/IoU; note when each is appropriate.
- [ ] Revise holdout, stratified, repeated K-fold, GroupKFold, chronological split and nested CV.
- [ ] Make a toy repeated-group dataset and show how an inappropriate random split inflates the result.

**Artifact:** `metric_and_split_lab.ipynb`

### D01.T05 — Tuning and experiment science

- [ ] Contrast manual sweep, grid search, random search, Bayesian/TPE optimization, early stopping and pruning.
- [ ] Run an Optuna toy objective with fixed budget and saved trials; plot parameter importance and optimization history.
- [ ] Write an experiment log schema: hypothesis, folds, seed, metric, budget, change, result, interpretation and next experiment.

**Artifact:** `optuna_intro.ipynb + experiments.csv`

### D01.T06 — First independent competition workflow

- [ ] Create a versioned Kaggle notebook or local template: load, inspect, split, baseline, evaluate, fit, predict, export.
- [ ] Produce a valid practice submission (where competition rules permit) and independently inspect prediction rows/IDs.
- [ ] Write a one-page retrospective with at least three things the baseline taught you.

**Artifact:** `baseline_submission.csv + day01_review.md`

**Read / reference (skim with a specific experiment in mind):**
- [Kaggle Learn catalogue](https://www.kaggle.com/learn)
- [Kaggle competition guide](https://www.kaggle.com/learn-guide/kaggle-competitions)
- [scikit-learn pitfalls](https://scikit-learn.org/stable/common_pitfalls)
- [NVIDIA Grandmaster strategies](https://developer.nvidia.com/blog/kaggle-grandmasters-unveil-winning-strategies-for-data-science-superpowers/)

**Exit gate:** explain the day's major choices from your own experiment evidence before starting the next day.

---

## Day 02 — Grandmaster-style EDA and tabular feature engineering

**Date:** 2026-10-27  
**Day exit goal:** Turn a messy tabular dataset into documented, testable hypotheses and stronger features.

### D02.T01 — Forensic data profiling

- [ ] Identify primary key, observation granularity, target generation and collection period; make a data dictionary.
- [ ] Audit null patterns, sentinel values, duplicate/near-duplicate rows, high cardinality, rare classes, label ambiguity and suspicious columns.
- [ ] Use pandas and optionally Polars to save an automated data quality report.

**Artifact:** `data_dictionary.csv + audit_report.md`

### D02.T02 — Univariate and bivariate deep dive

- [ ] Compare skewness, quantiles, multimodal shapes, long tails and missingness by target.
- [ ] Inspect category-frequency vs target, feature interactions, target encoding leakage risks and outlier impacts.
- [ ] Create at least six labeled charts that support or reject written hypotheses.

**Artifact:** `eda_v2.ipynb`

### D02.T03 — Train-test / domain-shift analysis

- [ ] Compare train and test numeric distributions and category coverage without inspecting unavailable labels.
- [ ] Build a train-versus-test adversarial-validation classifier as a diagnostic; inspect its highest-impact features.
- [ ] Write down how distribution shift affects your CV scheme and which findings may be dataset artifacts.

**Artifact:** `shift_diagnostics.md`

### D02.T04 — Feature engineering lab

- [ ] Test counts, group aggregates, ratios, interactions, datetime decomposition, frequency encoding and missing flags.
- [ ] Use fold-aware target encoding and leakage-safe aggregation where group/time context demands it.
- [ ] Run an ablation table: baseline vs each feature family on unchanged validation folds.

**Artifact:** `feature_ablation.csv`

### D02.T05 — Robust preprocessing and scaling

- [ ] Compare imputation strategies; never fit imputer/scaler/selector on validation or test.
- [ ] Compare OneHotEncoder, ordinal encoding, count/frequency encoding and suitable native categorical handling.
- [ ] Implement train/inference feature parity checks in a reusable pipeline.

**Artifact:** `preprocess_pipeline.py + tests`

### D02.T06 — Read, reproduce, and challenge a top solution

- [ ] Read the NVIDIA tabular playbook; identify validation, feature, ensemble and pseudo-label recommendations.
- [ ] Reproduce one small permitted technique on your chosen practice dataset with a fixed evaluation protocol.
- [ ] Write whether it improved performance, why it might not transfer, and what experiment comes next.

**Artifact:** `day02_solution_critique.md`

**Read / reference (skim with a specific experiment in mind):**
- [NVIDIA tabular Grandmaster playbook](https://developer.nvidia.com/blog/the-kaggle-grandmasters-playbook-7-battle-tested-modeling-techniques-for-tabular-data)
- [Kaggle Feature Engineering](https://www.kaggle.com/learn/feature-engineering)
- [Kaggle Data Cleaning](https://www.kaggle.com/learn/data-cleaning)

**Exit gate:** explain the day's major choices from your own experiment evidence before starting the next day.

---

## Day 03 — Validation, leakage detection, statistical reasoning and Optuna

**Date:** 2026-10-28  
**Day exit goal:** Be able to tell a real improvement from CV noise and leakage.

### D03.T01 — Validation scheme stress-test

- [ ] Implement stratified, grouped and temporal splits for separate toy or real datasets.
- [ ] Check overlap of IDs, users, sessions, content hashes and timestamps across folds.
- [ ] Write a one-page validation choice rationale tied to the competition's test-generation process.

**Artifact:** `cv_contract.md + split_checks.py`

### D03.T02 — Recreate leakage failures

- [ ] Demonstrate preprocessing leakage with scaler/feature selection fitted before split.
- [ ] Demonstrate target leakage using a post-outcome feature and near-duplicate/entity overlap.
- [ ] Repair both using train-fold-only fit and report metric deltas.

**Artifact:** `leakage_lab.ipynb`

### D03.T03 — Metric behavior and uncertainty

- [ ] Construct confusion matrices at multiple thresholds and quantify precision/recall tradeoffs.
- [ ] Evaluate seed and fold variability; show mean, standard deviation and paired model deltas.
- [ ] For the competition metric, implement a local scorer and test edge cases.

**Artifact:** `metric_unit_tests.py + fold_report.csv`

### D03.T04 — Optuna objective design

- [ ] Write an objective that trains only on training folds and returns mean target metric.
- [ ] Compare RandomSampler and TPESampler under the same small time/trial budget; record optimization traces.
- [ ] Study pruning and early stopping; ensure validation evidence does not leak into final test decisions.

**Artifact:** `optuna_cv_study.py`

### D03.T05 — Tuning search spaces and budgets

- [ ] Tune one simple model's regularization/depth/learning rate using narrow justified ranges.
- [ ] Benchmark runtime, best score and score variance; plot hyperparameter response.
- [ ] Freeze the chosen configuration and assess it on a separate untouched holdout.

**Artifact:** `tuning_study_report.md`

### D03.T06 — Submission calibration and audit

- [ ] Compare local CV with public leaderboard only as an external diagnostic, not as optimization ground truth.
- [ ] Simulate public/private holdouts where labels permit and measure ranking volatility.
- [ ] Write five rules that will prevent leaderboard chasing and invalid submissions.

**Artifact:** `lb_safety_checklist.md`

**Read / reference (skim with a specific experiment in mind):**
- [scikit-learn common pitfalls](https://scikit-learn.org/stable/common_pitfalls)
- [Optuna official tutorials](https://optuna.readthedocs.io/en/stable/tutorial/)
- [Kaggle Intermediate ML](https://www.kaggle.com/learn/intermediate-machine-learning)

**Exit gate:** explain the day's major choices from your own experiment evidence before starting the next day.

---

## Day 04 — Advanced tabular ML, tuning, OOF stacks and ensembling

**Date:** 2026-10-29  
**Day exit goal:** Build a reusable, independently tested competition-grade tabular pipeline.

### D04.T01 — Diverse model baselines

- [ ] Train dummy, regularized linear, random forest and histogram boosting baselines.
- [ ] Train XGBoost, LightGBM and CatBoost with identical frozen folds and metric.
- [ ] Compare training time, prediction time, per-fold metrics, overfit gap and major errors.

**Artifact:** `tabular_benchmark.csv`

### D04.T02 — Optuna per-model tuning

- [ ] Create three separate Optuna studies for XGBoost/LightGBM/CatBoost, with reproducible search spaces.
- [ ] Tune learning rate, tree depth/leaves, iterations, subsampling and regularization with early stopping.
- [ ] Compare tuned vs default using the same folds, documenting compute budget and whether improvement is stable.

**Artifact:** `optuna_boosters.py + studies/`

### D04.T03 — Feature selection and interpretability

- [ ] Compare permutation importance, SHAP for suitable tree models and simple correlation screening.
- [ ] Remove suspected leakage and noise features; confirm effects using repeated CV.
- [ ] Record interactions and residual error slices that motivate the next feature test.

**Artifact:** `importance_and_errors.ipynb`

### D04.T04 — OOF prediction library

- [ ] Generate strictly OOF train predictions and fold-averaged test predictions for multiple learners.
- [ ] Write assertions that every OOF value was produced by a model not trained on that sample.
- [ ] Compare simple average, rank average, optimized blend weights and a shallow stacker.

**Artifact:** `oof_ensemble.py + unit_tests`

### D04.T05 — Grandmaster-style advanced experiments

- [ ] Ablate seed averaging, residual models, target transformations and permitted extra data if relevant.
- [ ] Study pseudo-labeling as an optional technique; reject it when leakage, rules or stability invalidate it.
- [ ] Review NVIDIA case studies and document which techniques were actually validated.

**Artifact:** `advanced_ablation.md`

### D04.T06 — Competition submission and postmortem

- [ ] Choose best method by validated metric and stability, not only peak fold or public LB.
- [ ] Generate a reproducible prediction file; check ordering, formatting, null/inf and range.
- [ ] Write a clear solution explanation and at least five error-analysis findings.

**Artifact:** `tabular_solution.md + valid_submission.csv`

**Read / reference (skim with a specific experiment in mind):**
- [XGBoost paper](https://arxiv.org/abs/1603.02754)
- [LightGBM paper](https://arxiv.org/abs/1711.01681)
- [CatBoost paper](https://arxiv.org/abs/1810.11363)
- [NVIDIA stacking case study](https://developer.nvidia.com/blog/grandmaster-pro-tip-winning-first-place-in-a-kaggle-competition-with-stacking-using-cuml/)

**Exit gate:** explain the day's major choices from your own experiment evidence before starting the next day.

---

## Day 05 — Time series, demand forecasting and spatial data

**Date:** 2026-10-30  
**Day exit goal:** Handle time-dependent problems without future leakage.

### D05.T01 — Time-series EDA

- [ ] Audit frequency, gaps, seasonality, trend, holidays, spikes, changing variance and time-zone issues.
- [ ] Identify prediction horizon, entity/store hierarchy and data available at forecast time.
- [ ] Visualize rolling statistics and per-series slices with clear labels.

**Artifact:** `forecast_eda.ipynb`

### D05.T02 — Leakage-safe lag features

- [ ] Create lag, rolling, expanding, seasonal, grouped and calendar features using past information only.
- [ ] Make a test proving each row's features use data available at its prediction timestamp.
- [ ] Compare direct vs recursive multi-step forecasting and explain error propagation.

**Artifact:** `lag_features.py + tests`

### D05.T03 — Forecast validation and metrics

- [ ] Implement walk-forward/rolling-origin validation with an appropriate temporal gap.
- [ ] Compare naive, seasonal naive, mean/linear and tree-based baselines.
- [ ] Evaluate RMSLE/RMSE/MAE/SMAPE or requested metric carefully, including zeros.

**Artifact:** `walk_forward_cv.py`

### D05.T04 — Strong forecasting models

- [ ] Train a lag-feature LightGBM or CatBoost baseline and compare to simple statistical models.
- [ ] Compare global vs per-series models and inspect errors by store, item and horizon.
- [ ] Survey hierarchical reconciliation and probabilistic intervals, explaining when they matter.

**Artifact:** `forecast_comparison.csv`

### D05.T05 — Optuna for time series

- [ ] Tune lag window sizes and LightGBM depth/learning rate under rolling validation.
- [ ] Use early stopping/pruning only on valid temporal folds and respect forecast horizon.
- [ ] Analyze trial stability across multiple forecast origins.

**Artifact:** `ts_optuna.py + study_report.md`

### D05.T06 — Geospatial and forecasting competition practice

- [ ] Inspect coordinate/location features, nearby group structure and spatial leakage.
- [ ] Build one spatial aggregate or distance feature with validation that respects location groups.
- [ ] Run or reproduce a Store Sales practice submission; write forecasts and geographic error review.

**Artifact:** `day05_spatiotemporal_review.md`

**Read / reference (skim with a specific experiment in mind):**
- [Kaggle Time Series](https://www.kaggle.com/learn/time-series)
- [Kaggle Store Sales competition](https://www.kaggle.com/competitions/store-sales-time-series-forecasting)
- [Temporal Fusion Transformers paper](https://arxiv.org/abs/1912.09363)

**Exit gate:** explain the day's major choices from your own experiment evidence before starting the next day.

---

## Day 06 — NLP: text EDA, classical baselines and transformer fine-tuning

**Date:** 2026-10-31  
**Day exit goal:** Train, tune and diagnose two different text-classification approaches.

### D06.T01 — Text data audit

- [ ] Profile lengths, languages, empty text, label disagreement, near-duplicates, sources and group clusters.
- [ ] Check train/test vocabulary differences and whether users/authors/topics could leak.
- [ ] Select text cleaning rules based on their measurable effect rather than habit.

**Artifact:** `nlp_eda.ipynb`

### D06.T02 — TF-IDF foundation

- [ ] Implement word/character TF-IDF, n-grams and logistic regression or linear SVM.
- [ ] Compare alternative tokenization and vocabulary limits on fixed folds.
- [ ] Inspect top positive/negative terms, misclassifications and hard negations.

**Artifact:** `tfidf_baseline.ipynb`

### D06.T03 — Transformer foundations

- [ ] Explain embeddings, subword tokens, attention, padding, truncation and transfer learning.
- [ ] Run a pretrained DistilBERT/BERT-family inference baseline with permitted weights.
- [ ] Prepare datasets/tokenizer/collator and verify the label-to-ID mapping.

**Artifact:** `transformer_data_checks.py`

### D06.T04 — Fine-tune a small transformer

- [ ] Fine-tune a small sequence classifier on a suitable subset with seed, checkpoints and held-out evaluation.
- [ ] Compare frozen embeddings + linear head against end-to-end fine-tuning if feasible.
- [ ] Measure memory/runtime and review loss curves for overfitting.

**Artifact:** `nlp_finetune.ipynb`

### D06.T05 — NLP hyperparameter studies

- [ ] Compare learning rate, epochs, max length, batch size and weight decay using a very small budget.
- [ ] Use early stopping and validation-only selection; avoid expensive broad sweeps.
- [ ] Run error slices by text length, topic, repeated phrases and source.

**Artifact:** `nlp_hpo_and_errors.md`

### D06.T06 — Competition practice and generalization

- [ ] Create a valid Disaster Tweets submission where allowed.
- [ ] Survey multi-label classification, NER, QA, embeddings/retrieval, text generation and evaluation differences.
- [ ] Write a model-selection decision tree for short text, long text, multilingual text and limited GPU.

**Artifact:** `nlp_competition_review.md`

**Read / reference (skim with a specific experiment in mind):**
- [Kaggle Disaster Tweets](https://www.kaggle.com/competitions/nlp-getting-started)
- [Hugging Face classification guide](https://huggingface.co/docs/transformers/tasks/sequence_classification)
- [Attention Is All You Need](https://arxiv.org/abs/1706.03762)
- [BERT paper](https://arxiv.org/abs/1810.04805)

**Exit gate:** explain the day's major choices from your own experiment evidence before starting the next day.

---

## Day 07 — Computer vision classification and rigorous image validation

**Date:** 2026-11-01  
**Day exit goal:** Deliver a clean pretrained-image baseline with tested augmentations and cross-validation.

### D07.T01 — Image EDA and leakage audit

- [ ] Inspect image size, aspect ratio, channels, classes, corrupt files, label noise and source bias.
- [ ] Detect exact/near duplicates and group images from the same subject/location/session across folds.
- [ ] Create a balanced montage of representative and difficult images.

**Artifact:** `image_audit.ipynb`

### D07.T02 — Image preprocessing and augmentation

- [ ] Build reproducible resize, normalization and augmentation pipelines.
- [ ] Contrast benign transformations such as flips/color jitter with task-invalid transforms.
- [ ] Visualize original and augmented pairs to check class semantics.

**Artifact:** `augmentations.ipynb`

### D07.T03 — Transfer learning baseline

- [ ] Train a pretrained ResNet/EfficientNet-family classifier with a frozen feature backbone.
- [ ] Unfreeze selectively and compare small fine-tuning under the same folds.
- [ ] Implement checkpoint saving, reproducible loading and inference.

**Artifact:** `vision_baselines.ipynb`

### D07.T04 — Deep learning optimization

- [ ] Study batch normalization, AdamW, learning rate scheduling, mixed precision, weight decay and gradient accumulation.
- [ ] Compare two sensible learning-rate/schedule configurations.
- [ ] Use early stopping and inspect learning curves plus GPU utilization.

**Artifact:** `vision_training_report.md`

### D07.T05 — Optuna for vision

- [ ] Set a constrained HPO budget for learning rate, dropout, image size or augmentation intensity.
- [ ] Compare against a manually chosen baseline and keep the frozen validation protocol.
- [ ] Evaluate class-wise performance and inspect false positives and false negatives.

**Artifact:** `vision_optuna_review.md`

### D07.T06 — Inference and competition deliverable

- [ ] Test-time augmentation and seed averaging only if validation shows a reproducible gain.
- [ ] Run a real image classification prediction pipeline and verify prediction ordering.
- [ ] Write what changes for multilabel classification, ordinal labels and severe class imbalance.

**Artifact:** `vision_solution.md`

**Read / reference (skim with a specific experiment in mind):**
- [Kaggle Computer Vision](https://www.kaggle.com/learn/computer-vision)
- [PyTorch transfer learning tutorial](https://docs.pytorch.org/tutorials/beginner/transfer_learning_tutorial)
- [ResNet paper](https://arxiv.org/abs/1512.03385)
- [Hugging Face image classification](https://huggingface.co/docs/transformers/tasks/image_classification)

**Exit gate:** explain the day's major choices from your own experiment evidence before starting the next day.

---

## Day 08 — Object detection, segmentation, audio and multimodal fundamentals

**Date:** 2026-11-02  
**Day exit goal:** Prove you know how labels, metrics and models differ across non-tabular modalities.

### D08.T01 — Detection and segmentation problem audit

- [ ] Explain image classification vs bounding boxes vs instance/semantic segmentation vs keypoints.
- [ ] Inspect COCO/YOLO box formats, mask formats, class IDs and empty annotations.
- [ ] Compute one example of IoU and interpret precision/recall/mAP or Dice with a hand-worked case.

**Artifact:** `vision_task_formats.md`

### D08.T02 — Small object detection experiment

- [ ] Prepare a small licensed annotated image subset and verify labels visually.
- [ ] Run a lightweight pretrained detector on the verified subset; fine-tune briefly only if annotations, rules and compute allow, then inspect predicted boxes and failure modes.
- [ ] Measure mAP where feasible and check whether object size and class frequency explain misses.

**Artifact:** `detection_mini_lab.ipynb`

### D08.T03 — Small segmentation experiment

- [ ] Build a mask loader and verify mask/image alignment and resize methods.
- [ ] Run a pretrained or tiny segmentation inference baseline on small permitted data; treat extra fine-tuning as a separate compute-dependent stretch experiment.
- [ ] Measure Dice/IoU and compare boundary vs region errors.

**Artifact:** `segmentation_mini_lab.ipynb`

### D08.T04 — Audio EDA and feature design

- [ ] Inspect waveform, duration, sample rate, background noise, spectrogram/Mel-spectrogram.
- [ ] Use speaker/session grouped validation to prevent same-speaker leakage.
- [ ] Build a simple log-Mel + classical classifier or small CNN baseline.

**Artifact:** `audio_mini_lab.ipynb`

### D08.T05 — Audio-model optimization

- [ ] Compare crop duration, sample rate, time/frequency masking and model capacity.
- [ ] Use a limited tuning budget and monitor class/recording-condition errors.
- [ ] Contrast pretrained audio embeddings with handcrafted spectral features conceptually or experimentally.

**Artifact:** `audio_experiment_matrix.md`

### D08.T06 — Multimodal and compute-aware comparison

- [ ] Design a small image+text or audio+metadata fusion thought experiment with modality-specific encoders.
- [ ] List how missing modalities and alignment errors affect validation and prediction.
- [ ] Summarize when to choose pretrained encoders vs training from scratch across CV/audio.

**Artifact:** `multimodal_architecture_note.md`

**Read / reference (skim with a specific experiment in mind):**
- [PyTorch domain tutorials](https://docs.pytorch.org/tutorials/domains.html)
- [U-Net paper](https://arxiv.org/abs/1505.04597)
- [Hugging Face audio classification](https://huggingface.co/docs/transformers/tasks/audio_classification)

**Exit gate:** explain the day's major choices from your own experiment evidence before starting the next day.

---

## Day 09 — Recommendation, ranking, retrieval, graphs, generative AI and competition strategy

**Date:** 2026-11-03  
**Day exit goal:** Understand specialized Kaggle task families and perform two compact ranking/retrieval experiments.

### D09.T01 — Recommendation data and metrics

- [ ] Sketch implicit/explicit feedback, user-item interactions, cold-start and temporal relevance.
- [ ] Calculate Recall@K, MAP@K and NDCG@K for a tiny worked example.
- [ ] Set up a user/time-aware train/validation/test split, excluding future interactions.

**Artifact:** `recommender_basics.ipynb`

### D09.T02 — Recommendation baseline

- [ ] Train popularity and item-neighbor/similarity baselines on a small public permitted dataset.
- [ ] Compare ranking metrics and coverage for known vs new users.
- [ ] Record leakage risks from test interactions and repeated users.

**Artifact:** `recommendation_comparison.md`

### D09.T03 — Search, retrieval and learning to rank

- [ ] Create a tiny corpus and compare TF-IDF/BM25-style sparse retrieval with dense embeddings.
- [ ] Build a pairwise feature table and optional small ranker for judged query-document examples.
- [ ] Explain candidate retrieval vs reranking, and evaluate per-query not per-row randomly.

**Artifact:** `retrieval_mini_lab.ipynb`

### D09.T04 — Graph and relational ML awareness

- [ ] Identify node/edge prediction, graph-level labels and graph split leakage.
- [ ] Implement simple degree/neighbor feature baseline for a toy graph.
- [ ] Explain when GNNs are appropriate and when feature-engineered tabular models are sufficient.

**Artifact:** `graph_task_primer.md`

### D09.T05 — LLM and multimodal competition awareness

- [ ] Survey prompt-based classification, embeddings, instruction fine-tuning, LoRA/PEFT and model evaluation.
- [ ] Compare retrieval augmentation vs full fine-tuning in a small written design, accounting for allowed data and compute.
- [ ] Audit competition constraints, provenance, subjective metrics and reproducibility before using pretrained models.

**Artifact:** `generative_ai_task_guide.md`

### D09.T06 — Read winning workflows and design a strategy

- [ ] Study at least two legitimate winning-solution writeups from different modalities.
- [ ] Extract the recurring loop: CV, simple baseline, error analysis, targeted HPO, ensembles, reproducible submission.
- [ ] Reassess the medal-eligible competition selected on Day 1 using its rules, deadline, participation requirements and hardware budget; decide whether to continue or document a justified switch.

**Artifact:** `competition_selection.md`

**Read / reference (skim with a specific experiment in mind):**
- [scikit-learn ranking-relevant metrics](https://scikit-learn.org/stable/modules/model_evaluation.html)
- [Hugging Face Transformers tasks](https://huggingface.co/docs/transformers/tasks/sequence_classification)
- [Kaggle competitions guide](https://www.kaggle.com/learn-guide/kaggle-competitions)
- [NVIDIA GenAI-assisted Kaggle competition](https://developer.nvidia.com/blog/winning-a-kaggle-competition-with-generative-ai-assisted-coding/)

**Exit gate:** explain the day's major choices from your own experiment evidence before starting the next day.

---

## Day 10 — Blind competition capstone, debugging mastery, portfolio and next-90-day medal plan

**Date:** 2026-11-04  
**Day exit goal:** Independently solve a new problem end-to-end and prove reproducible improvement.

### D10.T01 — Blind dataset triage

- [ ] Choose an unseen permitted dataset or competition and refuse to reuse a full ready-made solution.
- [ ] Within an initial fixed session, identify task, metric, labels, potential leaks, constraints and validation.
- [ ] Produce a one-page analysis plan with prioritized hypotheses.

**Artifact:** `capstone_problem_brief.md`

### D10.T02 — Baseline-to-strong-solution sprint

- [ ] Implement baseline, valid folds, one meaningful EDA insight and first end-to-end inference.
- [ ] Train at least two diverse models under the fixed metric and freeze the best stable baseline.
- [ ] Record runtime, reproducibility, configuration and error examples.

**Artifact:** `capstone_baselines.csv`

### D10.T03 — Evidence-driven improvements

- [ ] Run three deliberately chosen feature/model experiments with one variable changed at a time.
- [ ] Apply small Optuna HPO only after CV and baseline work; preserve untouched final test.
- [ ] Compare model blending/stacking only where OOF evidence supports it.

**Artifact:** `capstone_experiment_log.csv`

### D10.T04 — Debugging and generalization challenge

- [ ] Inject a synthetic leakage bug, feature-order mismatch or duplicated fold and make your tests catch it.
- [ ] Test extreme values, unseen categories, missing data and incorrect sample ordering.
- [ ] Create failure-case documentation and a reproducible rerun command.

**Artifact:** `capstone_tests + failure_report.md`

### D10.T05 — Submission and public explanation

- [ ] Validate final submission schema, rows, values and competition compliance.
- [ ] Publish a permissible, readable notebook with assumptions, EDA, CV, ablations, error analysis and limitations.
- [ ] Write a clear account of what AI assisted with versus what you verified yourself.

**Artifact:** `capstone_solution.md + submission.csv`

### D10.T06 — Skill audit and realistic Grandmaster trajectory

- [ ] Score your own ability in 10 dimensions: EDA, validation, tabular, HPO, TS, NLP, CV, audio, ranking, reproducibility.
- [ ] Review all 10 days' outputs; identify two weak modalities and make follow-up practice plans.
- [ ] Set a 90-day schedule for active medal-eligible competitions, responsible collaboration and reviewing post-competition winning solutions.

**Artifact:** `day10_skills_audit.md + 90_day_competition_plan.md`

**Read / reference (skim with a specific experiment in mind):**
- [Kaggle progression (current)](https://www.kaggle.com/progression/competitions)
- [Kaggle Competitions rankings](https://www.kaggle.com/rankings/competitions)
- [NVIDIA Grandmaster playbook](https://developer.nvidia.com/blog/the-kaggle-grandmasters-playbook-7-battle-tested-modeling-techniques-for-tabular-data)

**Exit gate:** explain the day's major choices from your own experiment evidence before starting the next day.

---

## Full topic coverage and where it appears

| Core competency | Days |
|---|---|
| EDA: univariate, bivariate, multivariate, distribution, shift, duplicates, quality | 1–2, 5–8 |
| ML task taxonomy, evaluation metrics, validation, leakage | 1, 3 |
| Feature engineering, target/frequency encoding, preprocessing | 2–4 |
| Optuna, manual/random/TPE searches, early stopping, pruning | 1, 3–8 |
| Tabular regression/classification, imbalanced data, tree boosting | 2–4 |
| Stacking, OOF, blending, pseudo-labeling, model error analysis | 4, 10 |
| Time series, spatial, walk-forward CV | 5 |
| NLP, embeddings, transformers, fine-tuning | 6 |
| Image classification, transfer learning, augmentation, TTA | 7 |
| Object detection, image segmentation, audio | 8 |
| Ranking/recommendation, retrieval, graph and LLM awareness | 9 |
| Competition simulation, reproducibility, healthy Kaggle practice | 10 |

## Mastery checks: you should answer these without copying from AI

1. What split strategy actually simulates the private test set? Which kind of leakage would violate it?
2. Which metric matches the real objective and how is it computed locally?
3. How do you separate OOF predictions from in-sample predictions?
4. How do you choose an Optuna search space and know when further tuning is wasteful?
5. What changed when a model improved: feature quality, CV noise, compute, data leakage or true generalization?
6. What types of augmentation are invalid for a particular image/audio/time-series task?
7. How do you decide between linear/trees/transformers/CNNs/pretrained embeddings?
8. How do you detect train-test domain shifts without relying on test labels?
9. How do you reproduce every result and prove your notebook generates a valid submission?
10. Can you write an honest postmortem with mistakes, unsuccessful experiments and limitations?

## Optional stretch modules for the 90 days after the sprint

Survival analysis; medical and scientific signals; geospatial/spatiotemporal prediction; large-scale recommender systems; reinforcement learning/game AI; graph neural networks; self-supervised and contrastive learning; semantic segmentation at scale; speech recognition; multi-output/multilabel prediction; code competitions with runtime constraints; retrieval/reranking and LLM evaluation; uncertainty estimation; GPU acceleration with RAPIDS; distributed training; model compression. Each needs a separate deeper project and domain-specific validation.

## Continuation protocol

At the start of a new chat send: **"Continue Kaggle masterclass Day XX Task YY using `plan.md` and `docs/KAGGLE_LEARNING_CONTEXT.md`. I have completed these checkboxes: ... . First test my understanding, then give me the next mini-exercise; review my attempt before offering full code."** 

If an experiment fails, log it and improve the scientific method, rather than marking the task complete based on running a cell.

## Attribution and responsible competition rules

Resources linked above are documentation/papers/case studies. Credit others' public code and respect dataset, external-data, notebook and model-usage rules. Never fabricate private-leaderboard performance, medal status, measurements or independent verification. Kaggle compute availability and quotas may change; adjust workload without compromising validation.
