# Experiment Report: Tier Classifier Hyperparameter Search

## Overview

We conducted a randomized hyperparameter search across three model families and two cross-validation strategies to select the best classifier for predicting Toronto neighborhood affordability tiers 2 years ahead. All experiments were scored by macro F1 to treat all four tiers equally.

## Experimental Setup

| Parameter | Value |
|-----------|-------|
| Training set | 1,580 rows (158 neighborhoods x 10 years, 2010-2019) |
| Test set | 474 rows (158 neighborhoods x 3 years, 2020-2022) |
| Features | 21 (14 base numeric + 6 engineered ratios + 1 categorical) |
| Target | `TARGET_TIER_2YR` — 4-class ordinal (Budget / Moderate / Expensive / Premium) |
| Split strategy | Time-based (train on past, test on future) |
| Scoring metric | Macro F1 (unweighted average across all 4 classes) |
| Configs per model | 10 random samples from each param distribution |
| CV folds | 5 per strategy |
| Total fits | 300 (10 configs x 5 folds x 3 models x 2 CV strategies) |
| Bootstrap resamples | 2,000 (for 95% confidence intervals on test set) |
| Random seed | 42 |

## Model Families and Hyperparameter Distributions

**RandomForest**

| Hyperparameter | Search Space | Role |
|----------------|-------------|------|
| `n_estimators` | [200, 300, 500, 700] | Number of trees |
| `max_depth` | [6, 8, 10, 12, 15, None] | Tree depth limit (regularization) |
| `min_samples_leaf` | [3, 5, 8, 12] | Minimum leaf size (regularization) |
| `min_samples_split` | [2, 5, 10] | Minimum split size |
| `max_features` | [sqrt, log2, 0.5, 0.7] | Feature subsample per tree |
| `class_weight` | [balanced, balanced_subsample] | Class imbalance handling |

**XGBoost**

| Hyperparameter | Search Space | Role |
|----------------|-------------|------|
| `max_depth` | [3, 4, 5, 6, 8] | Tree depth limit |
| `n_estimators` | [200, 300, 500, 700] | Boosting rounds |
| `learning_rate` | [0.01, 0.03, 0.05, 0.1] | Step size shrinkage |
| `subsample` | [0.7, 0.8, 0.9, 1.0] | Row subsampling |
| `colsample_bytree` | [0.6, 0.7, 0.8, 0.9] | Feature subsampling |
| `min_child_weight` | [1, 3, 5, 7] | Minimum leaf weight |
| `reg_alpha` | [0.0, 0.01, 0.1, 0.5] | L1 regularization |
| `reg_lambda` | [0.5, 1.0, 2.0, 5.0] | L2 regularization |

**GradientBoosting (sklearn)**

| Hyperparameter | Search Space | Role |
|----------------|-------------|------|
| `n_estimators` | [200, 300, 500, 700] | Boosting rounds |
| `max_depth` | [3, 4, 5, 6, 8] | Tree depth limit |
| `learning_rate` | [0.01, 0.03, 0.05, 0.1] | Step size shrinkage |
| `min_samples_leaf` | [3, 5, 8, 12] | Minimum leaf size |
| `subsample` | [0.7, 0.8, 0.9, 1.0] | Stochastic gradient boosting |

## Cross-Validation Strategies

**StratifiedKFold (5 splits, shuffled):** Each fold contains a proportional representation of all 4 tiers. Shuffling breaks temporal ordering but ensures balanced class representation. Appropriate here because non-rent features are static proxies (same values across all years for a given neighborhood), so temporal leakage risk is low.

**TimeSeriesSplit (5 splits):** Training data sorted by YEAR. Each fold trains on earlier years and validates on the next. More conservative — simulates real-world deployment where only past data is available. Produces smaller early folds and larger later folds.

## Results: Cross-Validated Search

### Best model per family per CV strategy

| Model | CV Strategy | Best CV F1 | Std | Search Time |
|-------|-------------|-----------|-----|-------------|
| **GradientBoosting** | **StratifiedKFold** | **0.7400** | **0.0327** | **316.9s** |
| RandomForest | StratifiedKFold | 0.7339 | 0.0315 | 63.3s |
| XGBoost | StratifiedKFold | 0.7324 | 0.0247 | 100.0s |
| GradientBoosting | TimeSeriesSplit | 0.7152 | — | 203.7s |
| XGBoost | TimeSeriesSplit | 0.7121 | — | 95.8s |
| RandomForest | TimeSeriesSplit | 0.7049 | — | 44.9s |

### Key observations

1. **All three model families converge to similar CV F1 (0.73-0.74 under StratifiedKFold).** This convergence across fundamentally different algorithms (bagging, boosting, sequential boosting) is strong evidence that the performance ceiling is data-driven, not algorithm-driven.

2. **StratifiedKFold consistently outperforms TimeSeriesSplit** (~0.73 vs ~0.71). This is expected: StratifiedKFold sees data from all years in each fold, while TimeSeriesSplit's early folds train on very few years. The gap is moderate, suggesting the static features provide reasonable cross-temporal generalization.

3. **GradientBoosting shows high train F1 (0.95) vs CV F1 (0.74).** This train-validation gap indicates some overfitting, but the CV score is still the highest overall. The regularization from `subsample < 1.0` and `min_samples_leaf > 1` helps control it.

### Selected model: GradientBoosting

Winning hyperparameters (from `experiment_results.json`):

| Parameter | Value |
|-----------|-------|
| `n_estimators` | 500 |
| `max_depth` | 5 |
| `learning_rate` | 0.05 |
| `min_samples_leaf` | 3 |
| `subsample` | 0.8 |

## Results: Held-Out Test Set (2020-2022)

The selected model was evaluated on 474 rows it never saw during training or cross-validation.

| Metric | Value |
|--------|-------|
| Accuracy | 60.1% |
| Macro F1 | 0.604 |
| Baseline (random) | 25.0% |
| Improvement over baseline | 2.4x |

### Per-tier performance

| Tier | Precision | Recall | F1 | Support |
|------|-----------|--------|----|---------|
| Budget | 0.64 | 0.60 | 0.62 | 124 |
| Moderate | 0.52 | 0.53 | 0.53 | 119 |
| Expensive | 0.55 | 0.53 | 0.54 | 125 |
| Premium | 0.70 | 0.76 | 0.73 | 106 |

### Confusion matrix

|  | Predicted Budget | Predicted Moderate | Predicted Expensive | Predicted Premium |
|--|--:|--:|--:|--:|
| **Actual Budget** | 75 | 29 | 15 | 5 |
| **Actual Moderate** | 38 | 63 | 16 | 2 |
| **Actual Expensive** | 2 | 29 | 66 | 28 |
| **Actual Premium** | 2 | 0 | 23 | 81 |

Most misclassifications occur between adjacent tiers (Budget-Moderate, Expensive-Premium), which is expected for neighborhoods near quartile boundaries.

## Results: Bootstrapped 95% Confidence Intervals

2,000 bootstrap resamples of the 474-row test set, using percentile method.

| Metric | Mean | 95% CI Lower | 95% CI Upper |
|--------|------|-------------|-------------|
| Accuracy | 0.6013 | 0.5570 | 0.6435 |
| Macro F1 | 0.6031 | 0.5596 | 0.6438 |
| F1 (Budget) | 0.6217 | 0.5500 | 0.6908 |
| F1 (Moderate) | 0.5235 | 0.4454 | 0.5957 |
| F1 (Expensive) | 0.5379 | 0.4602 | 0.6101 |
| F1 (Premium) | 0.7293 | 0.6595 | 0.7899 |

### CV-Test gap analysis

The CV F1 (0.74) exceeds the test F1 (0.60) by 0.14 points. This gap quantifies the cost of the static-feature limitation: the model generalizes well within the 2010-2019 training distribution, but the 2020-2022 test period (which includes pandemic-era market disruption) introduces distributional shift that static neighborhood features cannot explain.

## Artifacts

| File | Description |
|------|-------------|
| `models/tier_classifier.pkl` | GradientBoosting model bundle (model + metadata + CIs) |
| `models/label_encoder.pkl` | LabelEncoder for CLASSIFICATION_CODE |
| `models/experiment_results.json` | Full search results: all 60 configs, per-fold scores, bootstrap CIs |
| `models/experiment_summary.csv` | Ranked leaderboard (one row per config) |
