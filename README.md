# Equity Return Forecasting Framework

> A modular, stock-agnostic pipeline for forecasting target equity returns using sector-wide signals.

**Demonstrated on:** Nvidia (NVDA) within the semiconductor ecosystem  
**Best result:** 75.86% directional accuracy (p < 0.001) | 72.81% under walk-forward validation across 114 weekly steps

---

## Overview

This project investigates whether wider stock market behaviour of a sector basket carries statistically significant predictive power over a target equity's weekly returns and whether that signal can be operationalised into a useful forecasting framework.

The answer is yes. The pipeline is designed to be transferable: the target equity and sector basket are user-defined parameters. Swap out Nvidia and semiconductors for any target equity and relevant sector, and the methodology follows.

---

## Results

| Model | MAE | RMSE | Directional Accuracy |
|---|---|---|---|
| SARIMA (baseline) | - | - | N/A (null model) |
| SARIMAX (daily) | 0.011255 | 0.017895 | 53.03% |
| SARIMAX (weekly) | 0.036743 | 0.047096 | 72.41% |
| XGBoost (weekly) | 0.046385 | 0.060773 | 62.07% |
| Ensemble - Simple Average | 0.035354 | 0.045747 | 67.24% |
| Ensemble - Weighted Average | 0.034674 | 0.045180 | 70.69% |
| Ensemble - Stacking | 0.035375 | 0.045743 | 70.69% |
| **Confidence Switching Ensemble** | **0.034863** | **0.043652** | **75.86%** |
| Walk-Forward Validation | 0.037588 | 0.047422 | **72.81%** |

The confidence switching ensemble outperforms all standard ensemble approaches by dynamically selecting between SARIMAX and XGBoost based on forecast confidence - derived from out-of-fold predictions with no look-ahead.

---

## Pipeline

```
[ Raw Sector Data ]
        |
        ▼
[ Regime Analysis ]  -->  Identifies training windows
        |
        ▼
[ PCA Reduction ]    -->  35 Features to 11 (80% Variance)
        |
        ▼
[  Model Testing  ]  -->  SARIMA | SARIMAX | XGBoost
        |
        ▼
[ Final Ensemble  ]  -->  Confidence Switching Logic
        |
        ▼
[   Validation    ]  -->  114-step Walk-Forward (p < 0.001)
```

---

## Key Methodological Decisions

**Regime-based training window** - Binary Segmentation (via `ruptures`) identifies structural breakpoints in log-transformed cumulative returns, statistically grounding our chosen training boundary.

**PCA with leakage prevention** - StandardScaler and PCA are fit exclusively on training data and applied to test data via transform only. Refitted at weekly frequency to reflect the different statistical structure of weekly returns.

**Controlled experimental design** - ARIMA parameters are held constant between SARIMA and SARIMAX, ensuring any performance difference is attributable purely to the addition of sector features rather than different parameter selection.

**Confidence switching ensemble** - Motivated by error decorrelation analysis. When SARIMAX's forecast magnitude exceeds an OOF-derived threshold, SARIMAX is used. Otherwise XGBoost is used. Threshold derived entirely from training data with no look-ahead.

**Walk-forward validation** - Expanding window retraining at every weekly step across 114 steps, simulating production use and confirming the static result is not overfitted to our test window.

---

## Adapting to Your Own Target Equity

1. Replace `data_stocks.csv` with your sector basket (closing prices)
2. Replace Nvidia with your own target equity throughout the notebook
3. Set `USE_DRIVE = False` if running locally
4. Re-run the elbow plot to select an appropriate number of breakpoints for your data
5. Interpret era labels through the lens of your sector's history
6. Adjust `m` in `auto_arima` if using a different resampling frequency (`m=5` daily, `m=4` weekly)

---

## Stack

| Category | Libraries |
|---|---|
| Data | `pandas`, `numpy` |
| EDA & Visualisation | `plotly`, `ruptures` |
| Statistical Models | `statsmodels` (SARIMAX), `pmdarima` (auto_arima) |
| Machine Learning | `scikit-learn` (PCA, GridSearchCV, TimeSeriesSplit), `xgboost` |
| Validation | `scipy.stats` (binomial test, Shapiro-Wilk), `statsmodels` (Ljung-Box) |
| Notebook | `itables`, Google Colab |

---

## Project Structure

```
equity-return-forecasting-framework/
├── notebook.ipynb          # Main notebook - full pipeline
├── data_stocks.csv         # Sector basket closing prices
└── README.md
```

---

## Author

**Aadam Gafar**  
[linkedin.com/in/agafar](https://linkedin.com/in/agafar) · [github.com/Aadam-Gafar](https://github.com/Aadam-Gafar)

*BSc Physics, University of Glasgow · Career Accelerator in Data Science & ML, University of Cambridge ICE*
