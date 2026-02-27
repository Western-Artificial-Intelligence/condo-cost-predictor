============================================================
TIER CLASSIFIER + NEIGHBORHOOD CLUSTERING
  with cross-validated hyperparameter search
  and bootstrapped confidence intervals
============================================================

--- PART 1: TIER CLASSIFIER ---

Train: 1580 rows, Test: 474 rows
Target distribution (train):
TARGET_TIER_2YR
1    418
2    403
3    387
4    372
Name: count, dtype: int64

Features: 21 (14 base + 6 engineered + 1 categorical)

Search plan: 3 model families x 2 CV strategies x 10 iters = 60 total fits (6 search rounds)

--- CV Strategy: StratifiedKFold ---
  [22:40:59] [1/6] Starting RandomForest (10 configs x 5 folds)...
Fitting 5 folds for each of 10 candidates, totalling 50 fits
  [22:42:02] [1/6] RandomForest done — best CV F1=0.7339, took 63.3s
  [22:42:02] [2/6] Starting XGBoost (10 configs x 5 folds)...
Fitting 5 folds for each of 10 candidates, totalling 50 fits
  [22:43:42] [2/6] XGBoost done — best CV F1=0.7324, took 100.0s
  [22:43:42] [3/6] Starting GradientBoosting (10 configs x 5 folds)...
Fitting 5 folds for each of 10 candidates, totalling 50 fits
  [22:48:59] [3/6] GradientBoosting done — best CV F1=0.7400, took 316.9s

--- CV Strategy: TimeSeriesSplit ---
  [22:48:59] [4/6] Starting RandomForest (10 configs x 5 folds)...
Fitting 5 folds for each of 10 candidates, totalling 50 fits
  [22:49:44] [4/6] RandomForest done — best CV F1=0.7049, took 44.9s
  [22:49:44] [5/6] Starting XGBoost (10 configs x 5 folds)...
Fitting 5 folds for each of 10 candidates, totalling 50 fits
  [22:51:20] [5/6] XGBoost done — best CV F1=0.7121, took 95.8s
  [22:51:20] [6/6] Starting GradientBoosting (10 configs x 5 folds)...
Fitting 5 folds for each of 10 candidates, totalling 50 fits
  [22:54:43] [6/6] GradientBoosting done — best CV F1=0.7152, took 203.7s

================================================================================
HYPERPARAMETER SEARCH COMPLETE — 60 configs evaluated in 824.6s
================================================================================
  Rank                 Model        CV Strategy   Mean F1     Std   Train F1
     1      GradientBoosting    StratifiedKFold    0.7400  0.0327     0.9477
     2      GradientBoosting    StratifiedKFold    0.7351  0.0311     0.9476
     3          RandomForest    StratifiedKFold    0.7339  0.0315     0.8529
     4      GradientBoosting    StratifiedKFold    0.7329  0.0202     0.9477
     5               XGBoost    StratifiedKFold    0.7324  0.0247     0.8813
     6      GradientBoosting    StratifiedKFold    0.7315  0.0344     0.9477
     7      GradientBoosting    StratifiedKFold    0.7306  0.0333     0.9477
     8      GradientBoosting    StratifiedKFold    0.7301  0.0302     0.9477
     9      GradientBoosting    StratifiedKFold    0.7292  0.0324     0.9382
    10               XGBoost    StratifiedKFold    0.7289  0.0276     0.9433
    11          RandomForest    StratifiedKFold    0.7282  0.0278     0.8421
    12      GradientBoosting    StratifiedKFold    0.7279  0.0316     0.9251
    13               XGBoost    StratifiedKFold    0.7277  0.0244     0.9376
    14               XGBoost    StratifiedKFold    0.7237  0.0346     0.8643
    15      GradientBoosting    StratifiedKFold    0.7232  0.0313     0.8646
    16               XGBoost    StratifiedKFold    0.7222  0.0288     0.9415
    17               XGBoost    StratifiedKFold    0.7212  0.0247     0.9438
    18               XGBoost    StratifiedKFold    0.7192  0.0352     0.9376
    19          RandomForest    StratifiedKFold    0.7176  0.0254     0.8055
    20      GradientBoosting    StratifiedKFold    0.7176  0.0353     0.8365

Best overall: GradientBoosting (StratifiedKFold) — CV F1 = 0.7400 +/- 0.0327

============================================================
GradientBoosting — Held-Out Test Results (2020-2022)
============================================================
Accuracy:  0.6013 (60.1%)
Macro F1:  0.6040

Classification Report:
              precision    recall  f1-score   support

      Budget       0.64      0.60      0.62       124
    Moderate       0.52      0.53      0.53       119
   Expensive       0.55      0.53      0.54       125
     Premium       0.70      0.76      0.73       106

    accuracy                           0.60       474
   macro avg       0.60      0.61      0.60       474
weighted avg       0.60      0.60      0.60       474

Confusion Matrix (rows=actual, cols=predicted):
           Budget  Moderate  Expensive  Premium
     Budget      75      29      15       5
   Moderate      38      63      16       2
  Expensive       2      29      66      28
    Premium       2       0      23      81

Bootstrapping 2000 resamples for 95% CI...
  bootstrap 200/2000 (10%) — 3.5s elapsed
  bootstrap 400/2000 (20%) — 7.0s elapsed
  bootstrap 600/2000 (30%) — 10.5s elapsed
  bootstrap 800/2000 (40%) — 14.0s elapsed
  bootstrap 1000/2000 (50%) — 17.6s elapsed
  bootstrap 1200/2000 (60%) — 21.1s elapsed
  bootstrap 1400/2000 (70%) — 24.6s elapsed
  bootstrap 1600/2000 (80%) — 28.3s elapsed
  bootstrap 1800/2000 (90%) — 31.8s elapsed
  bootstrap 2000/2000 (100%) — 35.4s elapsed
  Done in 35.4s

  Metric                   Mean                95% CI
  --------------------------------------------------
  accuracy               0.6013  [0.5570, 0.6435]
  macro_f1               0.6031  [0.5596, 0.6438]
  F1 (Budget)            0.6217  [0.5500, 0.6908]
  F1 (Moderate)          0.5235  [0.4454, 0.5957]
  F1 (Expensive)         0.5379  [0.4602, 0.6101]
  F1 (Premium)           0.7293  [0.6595, 0.7899]

Exported detailed results to /Users/juangomez/Documents/other SWE projecs/condo-cost-predictor/models/experiment_results.json
Exported summary leaderboard to /Users/juangomez/Documents/other SWE projecs/condo-cost-predictor/models/experiment_summary.csv

============================================================
BEST MODEL: GradientBoosting
  Test Accuracy: 0.6013 (60.1%)
  Test Macro F1: 0.6040
  Accuracy 95% CI: [0.5570, 0.6435]
  Macro F1 95% CI: [0.5596, 0.6438]
  CV Strategy: StratifiedKFold
  CV F1: 0.7400 +/- 0.0327
============================================================

Saved model bundle to /Users/juangomez/Documents/other SWE projecs/condo-cost-predictor/models/tier_classifier.pkl
Saved label encoder to /Users/juangomez/Documents/other SWE projecs/condo-cost-predictor/models/label_encoder.pkl

--- PART 2: NEIGHBORHOOD CLUSTERING ---


Loaded 158 neighborhoods for clustering

Cluster analysis (20 features):
    k     Inertia  Silhouette   MaxSize   MinSize
    3      2215.1      0.2118        96        26
    4      1988.7      0.1831        81         2
    5      1824.5      0.2027        86         3
    6      1670.8      0.1627        71         2
    7      1550.5      0.1350        56         2
    8      1432.8      0.1297        54         2
    9      1354.2      0.1519        53         1
   10      1294.4      0.1104        39         1
   11      1262.7      0.1224        49         1
   12      1207.2      0.1173        38         1

Selected k=7 (silhouette: 0.1350)

Cluster labels:
  Cluster 0: Frequent-Service Corridor (22 neighborhoods)
    e.g. Broadview North, Dufferin Grove, Eglinton East, Flemingdon Park
  Cluster 1: Connected Family Neighborhood (45 neighborhoods)
    e.g. Agincourt North, Bathurst Manor, Bayview Village, Bedford Park-Nortown
  Cluster 2: Quiet Low-Density Residential (56 neighborhoods)
    e.g. Alderwood, Bayview Woods-Steeles, Beechborough-Greenbrook, Bendale South
  Cluster 3: Downtown & Entertainment (5 neighborhoods)
    e.g. Downtown Yonge East, Kensington-Chinatown, Mimico-Queensway, Moss Park
  Cluster 4: Major Transit Hub (2 neighborhoods)
    e.g. West Humber-Clairville, York University Heights
  Cluster 5: Transit-Rich Suburban (18 neighborhoods)
    e.g. Agincourt South-Malvern West, Annex, Banbury-Don Mills, Bendale-Glen Andrew
  Cluster 6: High-Density Urban Core (10 neighborhoods)
    e.g. Avondale, Bay-Cloverhill, Church-Wellesley, Harbourfront-Cityplace

Exported cluster assignments to /Users/juangomez/Documents/other SWE projecs/condo-cost-predictor/data/processed_data/cluster_assignments.csv
Saved scaler to /Users/juangomez/Documents/other SWE projecs/condo-cost-predictor/models/scaler.pkl

============================================================
TRAINING COMPLETE
============================================================
  Classifier: GradientBoosting
    Test accuracy: 60.1% (95% CI: [55.7%, 64.3%])
    Test macro F1: 0.6040 (95% CI: [0.5596, 0.6438])
    CV F1: 0.7400 +/- 0.0327
    Configs evaluated: 60
  Clustering: 7 clusters assigned to 158 neighborhoods
  Artifacts:
    models/tier_classifier.pkl
    models/label_encoder.pkl
    models/scaler.pkl
    models/experiment_results.json
    models/experiment_summary.csv
    data/processed_data/cluster_assignments.csv