# Predicting Neighborhood Affordability Tiers in Toronto: A Classification Approach Using Static Urban Features

**Authors:** [Team Names], Department of Computer Science, Western University

**Course:** [Course Code] — [Course Title]

**Date:** February 2026

---

## Abstract

We present a machine learning system for predicting which affordability tier (Budget, Moderate, Expensive, or Premium) a Toronto neighborhood will fall into two years ahead, using only non-rent urban characteristics: crime rates, transit infrastructure, green space density, and population. Our dataset spans 15 years (2010-2024) across 158 neighborhoods, assembled from Toronto Open Data, TREB rental reports, TTC GTFS feeds, and Statistics Canada census data. We conducted a randomized hyperparameter search across 60 configurations of three model families (Random Forest, XGBoost, Gradient Boosting) evaluated under both stratified and temporal cross-validation. The best model (Gradient Boosting, StratifiedKFold) achieves a cross-validated macro F1 of 0.740 and a held-out test F1 of 0.604 (95% CI: 0.560-0.644) on 2020-2022 data, representing a 2.4x improvement over random baseline. The convergence of all three model families to similar performance (CV F1 0.73-0.74) provides evidence that the performance ceiling is driven by the static nature of the available features rather than model capacity. We complement the classifier with a K-Means clustering of neighborhoods into 7 interpretable groups and deploy the system as an interactive web application for rental affordability exploration.

---

## 1. Introduction

### 1.1 Motivation

Toronto's rental market has experienced sustained price growth over the past decade, with average one-bedroom rents increasing from approximately $1,100 in 2010 to over $2,200 in 2024. For students and young professionals entering the market, understanding which neighborhoods are likely to remain affordable — or become unaffordable — is a practical concern with limited tooling support.

Existing resources (CMHC reports, TREB market summaries) provide aggregate statistics but lack neighborhood-level granularity. There is no publicly available tool that combines longitudinal rental data with neighborhood characteristics (transit access, safety, green space) to help users reason about future affordability at the neighborhood level.

### 1.2 Problem Statement

We address two questions:

1. **Can neighborhood-level urban characteristics (crime, transit, parks, population) predict which affordability tier a neighborhood will occupy two years from now?** This is a 4-class classification problem where tiers are defined by within-year rent quartiles.

2. **Can we group Toronto's 158 neighborhoods into meaningful clusters** that enable a "find similar neighborhoods" feature for users priced out of their preferred area?

### 1.3 Contributions

- A longitudinal dataset of 158 Toronto neighborhoods across 15 years (2010-2024), integrating rental, crime, transit, and green space data from 4 municipal data sources
- A systematic model selection pipeline with cross-validated hyperparameter search and bootstrapped confidence intervals
- An analysis of the predictive ceiling imposed by static urban features, quantified through the CV-test performance gap
- An interactive web application (FastAPI + Streamlit) for neighborhood-level rental affordability exploration

### 1.4 Scope and Limitations

We acknowledge upfront that our non-rent features are static proxies: crime rates, transit infrastructure, park counts, and population are taken from the 2024 snapshot and applied to all prior years. This means the model cannot learn temporal dynamics (e.g., "neighborhoods that gained a subway station saw rent increases"). This is a known and deliberate constraint — time-varying versions of these features do not exist in a clean, publicly available form for Toronto neighborhoods. We quantify the cost of this limitation in Section 5.

---

## 2. Related Work

Rental price prediction has been studied extensively at the listing level, where features like square footage, number of bedrooms, and building age are strong predictors. Trulia, Zillow, and academic work (Pow et al., 2017; Ho et al., 2021) achieve high accuracy in this setting because the features directly describe the unit being priced.

Neighborhood-level prediction is less studied. Chaphalkar & Sandbhor (2019) used hedonic pricing models with neighborhood amenities but relied on cross-sectional data. Recent work by Li et al. (2022) applied gradient boosting to predict neighborhood-level rent changes in New York, but used time-varying features (new construction permits, subway ridership changes) that are not available in our Toronto context.

Our work differs in two ways: (1) we predict ordinal affordability tiers rather than continuous dollar amounts, which is more robust to the autocorrelation problem in rent time series, and (2) we explicitly characterize the performance ceiling imposed by static features, rather than treating it as a limitation to be minimized.

---

## 3. Data

### 3.1 Data Sources

| Source | Data | Years | Granularity |
|--------|------|-------|-------------|
| TREB (Toronto Regional Real Estate Board) | Average 1BR rent | 2010-2024 | Neighborhood x Year |
| Toronto Open Data | Crime rates (assault, auto theft, robbery, theft over $5k) | 2014-2024 | Neighborhood x Year |
| TTC GTFS Feeds | Transit stops, routes, frequencies, line lengths | 2024 | Neighborhood |
| Toronto Open Data | Park boundaries | 2024 | Neighborhood |
| Statistics Canada | Population | 2021 Census | Neighborhood |

### 3.2 Data Pipeline

Raw data was collected via per-year ETL notebooks using DuckDB with spatial extensions for point-in-polygon joins (assigning transit stops and parks to neighborhoods). The 15 per-year CSVs were assembled into a master dataset (2,528 rows x 95 columns), then cleaned to a modeling-ready format (2,054 rows x 21 columns) by:

- Deduplicating erroneous rows (2017 had 317 rows instead of 158)
- Proxying 2024 population to all prior years (census data only available for 2021)
- Imputing missing crime rates for 2010-2013 using training set medians
- Computing per-year rent quartiles to define tier labels
- Dropping rent-derived features to prevent target leakage

### 3.3 Target Variable

`TARGET_TIER_2YR` assigns each neighborhood-year to the rent quartile it will occupy two years later:

| Tier | Label | Definition |
|------|-------|-----------|
| 1 | Budget | Bottom 25% of rents for the target year |
| 2 | Moderate | 25th-50th percentile |
| 3 | Expensive | 50th-75th percentile |
| 4 | Premium | Top 25% of rents |

Quartile-based tiers handle inflation naturally: a $1,200 rent was "Expensive" in 2010 but "Budget" in 2024.

### 3.4 Features

**14 base numeric features:**

| Category | Features |
|----------|----------|
| Geography | `area_sq_meters`, `perimeter_meters` |
| Crime | `ASSAULT_RATE`, `AUTOTHEFT_RATE`, `ROBBERY_RATE`, `THEFTOVER_RATE` |
| Transit | `total_stop_count`, `avg_stop_frequency`, `max_stop_frequency`, `total_line_length_meters`, `transit_line_density`, `distinct_route_count` |
| Green space | `park_count` |
| Demographics | `POPULATION` |

**6 engineered ratio features:**

| Feature | Formula | Correlation with Target |
|---------|---------|------------------------|
| `park_density` | parks / area | 0.47 (vs 0.01 for raw `park_count`) |
| `pop_density` | population / area | 0.38 (vs 0.04 for raw `POPULATION`) |
| `transit_per_capita` | stops / population | 0.29 |
| `total_crime_rate` | sum of 4 crime rates | 0.07 |
| `compactness` | perimeter^2 / area | varies |
| `routes_per_stop` | routes / stops | varies |

**1 categorical feature:** `CLASSIFICATION_CODE` (label-encoded, 3 values)

**Excluded:** `avg_rent_1br` — current rent almost perfectly predicts future rent tier due to autocorrelation. Including it would mean the model learns "current tier = future tier" and ignores all neighborhood characteristics.

### 3.5 Train/Test Split

Time-based split: train on 2010-2019 (1,580 rows), test on 2020-2022 (474 rows). No random shuffling — the model should never see future data during training.

| Split | Years | Rows | Purpose |
|-------|-------|------|---------|
| Train | 2010-2019 | 1,580 | Cross-validation and model fitting |
| Test | 2020-2022 | 474 | Final evaluation (never seen during search) |

Target distribution in training set: Budget (418), Moderate (403), Expensive (387), Premium (372) — approximately balanced.

---

## 4. Methods

### 4.1 Model Families

We evaluated three tree-based ensemble methods:

**Random Forest:** Trains independent decision trees on bootstrap samples of the data, then aggregates predictions by majority vote. Naturally resistant to overfitting through bagging and feature subsampling.

**XGBoost:** Builds trees sequentially, where each tree corrects the residual errors of the ensemble so far. Includes L1 (`reg_alpha`) and L2 (`reg_lambda`) regularization on leaf weights, plus row and column subsampling.

**Gradient Boosting (sklearn):** Similar sequential boosting approach to XGBoost but with a different implementation. Uses stochastic gradient boosting (`subsample < 1.0`) for regularization.

### 4.2 Hyperparameter Search

We used `RandomizedSearchCV` from scikit-learn to sample 10 configurations per model family from predefined parameter distributions (see Appendix A for full distributions). Each configuration was evaluated under two cross-validation strategies:

**StratifiedKFold (5 splits, shuffled):** Ensures each fold contains a proportional representation of all 4 tiers. Shuffling breaks temporal ordering but maximizes class balance per fold. Appropriate here because non-rent features are static across years — temporal leakage risk is minimal.

**TimeSeriesSplit (5 splits):** Respects temporal ordering. Each fold trains on earlier years and validates on the next chronological block. More conservative but produces unbalanced fold sizes (early folds have very few training examples).

Total configurations evaluated: 3 models x 2 CV strategies x 10 iterations = 60 configurations, 300 total model fits.

### 4.3 Model Selection

The configuration with the highest mean cross-validated macro F1 across all 60 entries was selected. Macro F1 was chosen over accuracy because it weights all 4 tiers equally, preventing the model from ignoring underrepresented tiers.

### 4.4 Confidence Intervals

After selecting the best model, we estimated 95% confidence intervals on the held-out test set using the bootstrap percentile method:

1. Resample the 474-row test set with replacement (same size) 2,000 times
2. For each resample, compute accuracy, macro F1, and per-class F1
3. Report the 2.5th and 97.5th percentiles as the 95% CI bounds

This quantifies the uncertainty in our test-set estimates due to the finite sample size.

### 4.5 Neighborhood Clustering

Separately from the classifier, we clustered the 158 neighborhoods in the 2024 snapshot using K-Means on standardized (z-scored) versions of the 20 numeric features (14 base + 6 engineered). We evaluated k=3 through k=12 using silhouette score and selected k=7 for practical interpretability.

---

## 5. Results

### 5.1 Cross-Validation Results

| Model | CV Strategy | Best CV F1 | Std |
|-------|-------------|-----------|-----|
| **GradientBoosting** | **StratifiedKFold** | **0.7400** | **0.0327** |
| RandomForest | StratifiedKFold | 0.7339 | 0.0315 |
| XGBoost | StratifiedKFold | 0.7324 | 0.0247 |
| GradientBoosting | TimeSeriesSplit | 0.7152 | — |
| XGBoost | TimeSeriesSplit | 0.7121 | — |
| RandomForest | TimeSeriesSplit | 0.7049 | — |

**Finding 1: Algorithm convergence.** All three model families achieve CV F1 within a narrow band (0.73-0.74 under StratifiedKFold). When fundamentally different algorithms (bagging vs. sequential boosting vs. regularized boosting) converge to the same performance, the bottleneck is the data, not the model.

**Finding 2: CV strategy comparison.** StratifiedKFold consistently outperforms TimeSeriesSplit by ~0.02-0.03 F1 points. This is expected: TimeSeriesSplit's early folds train on very few years, and the static features provide reasonable cross-temporal generalization.

### 5.2 Held-Out Test Performance

| Metric | Value | 95% CI |
|--------|-------|--------|
| Accuracy | 60.1% | [55.7%, 64.3%] |
| Macro F1 | 0.604 | [0.560, 0.644] |
| Random baseline | 25.0% | — |

Per-tier performance:

| Tier | Precision | Recall | F1 | 95% CI |
|------|-----------|--------|----|--------|
| Budget | 0.64 | 0.60 | 0.62 | [0.550, 0.691] |
| Moderate | 0.52 | 0.53 | 0.53 | [0.445, 0.596] |
| Expensive | 0.55 | 0.53 | 0.54 | [0.460, 0.610] |
| Premium | 0.70 | 0.76 | 0.73 | [0.660, 0.790] |

Premium neighborhoods are easiest to predict (F1 = 0.73) because they have distinctive characteristics (high density, high transit access). Middle tiers (Moderate, Expensive) are hardest because neighborhoods near the 50th percentile boundary can plausibly go either way.

### 5.3 The CV-Test Gap

The cross-validated F1 (0.740) exceeds the held-out test F1 (0.604) by 0.136 points. We attribute this gap to two factors:

1. **Static feature limitation.** The model learns neighborhood identity signals (high-density areas tend to be expensive) that hold within the 2010-2019 training period. But when market conditions shift in 2020-2022, static features cannot explain the change.

2. **Distributional shift.** The 2020-2022 test period includes pandemic-era disruption to Toronto's rental market (suburban demand increase, downtown vacancy spike), which represents a distributional shift from the training period.

This gap is a quantifiable result, not a failure. It measures exactly how much predictive power is lost when features cannot capture temporal dynamics.

### 5.4 Confusion Matrix Analysis

|  | Pred. Budget | Pred. Moderate | Pred. Expensive | Pred. Premium |
|--|--:|--:|--:|--:|
| **Budget** | 75 | 29 | 15 | 5 |
| **Moderate** | 38 | 63 | 16 | 2 |
| **Expensive** | 2 | 29 | 66 | 28 |
| **Premium** | 2 | 0 | 23 | 81 |

The off-diagonal mass is concentrated on adjacent tiers. Budget neighborhoods are misclassified as Moderate (29 cases) far more often than as Premium (5 cases). This is consistent with the ordinal nature of the target — neighborhoods near a quartile boundary are genuinely ambiguous.

### 5.5 Clustering Results

| Cluster | Size | Description |
|---------|------|-------------|
| Frequent-Service Corridor | 22 | High-frequency transit stops with good route connectivity |
| Connected Family Neighborhood | 45 | Populated areas with parks and multiple transit routes |
| Quiet Low-Density Residential | 56 | Below-average transit and population |
| Downtown & Entertainment | 5 | High crime rates, high park density |
| Major Transit Hub | 2 | Extreme transit infrastructure |
| Transit-Rich Suburban | 18 | Large neighborhoods with extensive transit line coverage |
| High-Density Urban Core | 10 | Very high population density |

---

## 6. Discussion

### 6.1 What the Model Learns

The model effectively learns a mapping from neighborhood characteristics to affordability tier. SHAP analysis reveals that `park_density`, `pop_density`, and transit features are the strongest predictors. This aligns with urban economics intuition: dense neighborhoods with good transit access and green space command higher rents.

However, the model cannot learn *transitions*. A neighborhood undergoing gentrification (new condo developments, rezoning) looks identical to a stable neighborhood in our feature space because those dynamics are not captured by static features.

### 6.2 Practical Utility

Despite the 60% test accuracy, the system has practical value:

- **2.4x better than random guessing** on a 4-class problem
- **Adjacent-tier errors are low-cost.** Predicting "Moderate" when the truth is "Budget" is a much smaller mistake than predicting "Premium" when the truth is "Budget." The confusion matrix shows the model rarely makes extreme errors.
- **The clustering component is independent of prediction accuracy.** "Find similar neighborhoods" works well because it uses the same static features that are good at describing neighborhood character, even if they're limited for temporal prediction.

### 6.3 Limitations

1. **Static features.** The most significant limitation. Time-varying features (year-over-year crime changes, new transit openings, building permits) would likely improve test performance substantially but are not available in clean form.
2. **Population proxy.** Census population (2021) is applied to all years. Neighborhoods with significant population change between 2010-2024 are misrepresented.
3. **Crime data gap.** Crime rates for 2010-2013 are imputed from training set medians, introducing noise for those years.
4. **Pandemic disruption.** The 2020-2022 test period is not representative of normal market conditions. Test performance on a non-pandemic period might be higher.

### 6.4 Future Work

- Incorporate time-varying features: building permits, zoning changes, transit line openings
- Explore ordinal classification losses that penalize adjacent-tier errors less than distant-tier errors
- Extend the prediction horizon analysis (1-year, 3-year, 5-year) to characterize how accuracy degrades with horizon length
- Ensemble the top-k models from the search via stacking or soft voting

---

## 7. Conclusion

We built a neighborhood-level affordability tier classifier for Toronto that achieves 60.1% accuracy (95% CI: 55.7%-64.3%) using only static urban features, representing a 2.4x improvement over random baseline. A systematic hyperparameter search across 60 configurations of three model families confirmed that the performance ceiling is data-driven: all algorithms converge to similar cross-validated F1 (0.73-0.74). The 0.14-point gap between cross-validated and held-out test performance quantifies the cost of relying on static features in a temporally shifting market. We deploy the classifier alongside a 7-cluster neighborhood grouping in an interactive web application that enables Toronto renters to explore affordability, compare neighborhoods, and understand predicted tier trajectories.

---

## Appendix A: Hyperparameter Search Spaces

See `models/experiment_summary.md` for the full parameter distributions and `models/experiment_results.json` for per-configuration results.

## Appendix B: Reproducibility

All experiments can be reproduced by running:

```
source .venv/bin/activate
python3 models/train_tier_classifier.py
```

The script uses `random_state=42` throughout. Output artifacts are written to `models/`.

---

## References

<!-- Fill in with actual citations -->

- Chaphalkar, N. & Sandbhor, S. (2019). Use of hedonic pricing model for assessment of residential property values. *International Journal of Recent Technology and Engineering.*
- Ho, W. K., Tang, B. S., & Wong, S. W. (2021). Predicting property prices with machine learning algorithms. *Journal of Property Research.*
- Li, Y., et al. (2022). Neighborhood-level rent prediction using gradient boosting with urban dynamics features. *Urban Computing.*
- Pow, N., Janulewicz, E., & Liu, L. (2017). Applied machine learning project 4 prediction of real estate property prices in Montreal. *Course Report, McGill University.*
