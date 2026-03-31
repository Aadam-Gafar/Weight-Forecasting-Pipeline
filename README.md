# Weight Forecasting for Athletes Using Nutrition Data

> A time-series forecasting pipeline for predicting weight change from daily nutrition tracking.

**Use Case:** Boxing weight cuts - forecast weight trajectory to make weight safely on schedule  
**Best Result:** 90.91% directional accuracy (p = 0.006) on test set | 74% average across walk-forward validation

---

## Overview

This project tests whether daily nutrition data (calories, macros, expenditure) carries statistically significant predictive power over weight change, and whether that signal can be operationalized for weight management.

The answer is yes. The pipeline is designed to be transferable: users import their MacroFactor export, and the methodology follows.

---

## Results

| Model | MAE (kg) | RMSE (kg) | Directional Accuracy |
|---|---|---|---|
| SARIMA (baseline) | 0.0255 | 0.0273 | 0.00% |
| **SARIMAX** | **0.0240** | **0.0259** | **90.91%** |
| XGBoost (single split) | 0.0004 | 0.0005 | 100.00% (overfitted) |
| XGBoost (walk-forward) | 0.0062 | 0.0132 | 74.00% ± 35.6% |

**Statistical Significance:** Binomial test p = 0.006 (99% confidence) - SARIMAX directional accuracy is not random chance.

SARIMAX outperforms both baseline and XGBoost. XGBoost's high variance across folds (35.6% std) indicates instability; SARIMAX provides more reliable predictions.

---

## Pipeline
```
[ MacroFactor Export ]
        |
        ▼
[ Phase Detection ]     -->  Changepoint analysis identifies training phases
        |
        ▼
[ Feature Selection ]   -->  Drop multicollinear features (Calories vs Deficit)
        |
        ▼
[ Model Testing ]       -->  SARIMA | SARIMAX | XGBoost
        |
        ▼
[ Validation ]          -->  Walk-forward CV (5 folds, 150 test obs)
```

---

## Key Methodological Decisions

**Phase-based training window** - Changepoint detection (via `ruptures`) identifies distinct training phases. Phase 1 (0.80x volatility ratio) selected for training due to clean deficit-response signal.

**Multicollinearity handling** - Calories dropped (r = 0.99 with Caloric Deficit) to prevent feature redundancy. Deficit retained as the fundamental thermodynamic driver.

**Feature engineering rejected** - Lagged target variables (TARGET_lag1, TARGET_lag2) caused severe overfitting in XGBoost. Removed to ensure model learns from nutrition, not weight momentum.

**Classical methods over ML** - SARIMAX (linear) outperformed XGBoost (non-linear) due to physiologically linear deficit-weight relationship. Added complexity introduced instability without benefit.

**Walk-forward validation** - 5-fold time-series CV revealed true performance (74% avg) vs. single-split optimism (90.91%). XGBoost variance across folds (35.6% std) confirmed instability.

---

## Adapting to Your Own Data

1. Export data from MacroFactor (`.xlsx` format with Calories & Macros, Weight Trend, Expenditure sheets)
2. Replace `macrofactor_data.xlsx` with your export
3. Set `USE_DRIVE = False` if running locally
4. Re-run changepoint detection to identify your training phases
5. Adjust `modeling_start_date` based on your phase analysis
6. Interpret results in context of your training regimen (cut/bulk/maintenance)

---

## Stack

| Category | Libraries |
|---|---|
| Data | `pandas`, `numpy`, `openpyxl` |
| EDA & Visualization | `plotly`, `ruptures` |
| Statistical Models | `statsmodels` (SARIMAX), `pmdarima` (auto_arima) |
| Machine Learning | `scikit-learn` (StandardScaler, GridSearchCV, TimeSeriesSplit), `xgboost` |
| Validation | `scipy.stats` (binomial test) |

---

## Project Structure
```
weight-forecasting-macrofactor/
├── notebook.ipynb              # Main notebook - full pipeline
├── macrofactor_data.xlsx       # User's MacroFactor export
└── README.md
```

---

## Limitations

- **Small dataset:** 190 logged days, 11-observation test set limits statistical power
- **Single individual:** Metabolic adaptation and physiology vary; results may not generalize
- **Phase-dependent:** Performance varies by training phase (74% average, 35.6% std across folds)

---

## Author

**Aadam Gafar**  
[linkedin.com/in/agafar](https://linkedin.com/in/agafar) · [github.com/Aadam-Gafar](https://github.com/Aadam-Gafar)

*BSc Physics, University of Glasgow · Career Accelerator in Data Science & ML, University of Cambridge ICE*