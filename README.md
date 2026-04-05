# WeightForecaster Desktop App (Prototype)

> **⚠️ Early Development Branch**: This branch contains a rapid prototype of the desktop application. It is not production-ready and is shared here for development transparency and version control purposes.

## Overview

WeightForecaster is a desktop application that converts the SARIMAX-based weight forecasting model from my [Jupyter notebook analysis](link-to-notebook) into a standalone Windows GUI tool for combat sports athletes planning weight cuts.

This prototype was built to explore:
- PyQt6 desktop UI patterns for scientific computing applications
- Integration of statsmodels SARIMAX models into interactive tools
- Real-time validation and error handling for user inputs
- Data visualization with Plotly in native desktop applications

## Current Status: Prototype

**What this branch represents:**
- A functional proof-of-concept demonstrating the core forecasting workflow
- Rapid iteration on UI/UX patterns (not final design)
- Initial model integration (requires refinement for broader datasets)
- Development sandbox for testing architecture decisions

**Known limitations:**
- **UI Design**: Minimal styling, placeholder layouts — aesthetic polish deferred to post-validation phase
- **Model Generalization**: Current SARIMAX configuration optimized for the original training dataset; performs inconsistently on diverse input patterns (planned: hyperparameter tuning, ensemble methods, or alternative architectures)
- **Code Quality**: Contains exploratory code, minimal documentation, and vibecoded sections prioritizing speed over maintainability

## Why This Exists

I'm transitioning from support engineering to data science and wanted to demonstrate:
1. **End-to-end capability**: Taking research code (notebook) to a deployable artifact (desktop app)
2. **Product thinking**: Understanding user workflows beyond model accuracy
3. **Technical breadth**: Comfort across backend logic, UI integration, and data pipelines

This prototype validates the technical feasibility before investing in production-grade implementation.

## Repository Structure

```
WeightForecaster/
├── backend/              # Core forecasting engine
│   ├── models.py         # Data classes (ValidationResult, ForecastResult)
│   ├── data_loader.py    # MacroFactor XLSX import
│   ├── validator.py      # Data quality checks
│   ├── phase_detector.py # Changepoint detection (ruptures)
│   ├── forecaster.py     # SARIMAX training & prediction
│   └── safety.py         # Physiological constraints
├── ui/                   # PyQt6 interface
│   ├── state_manager.py  # Application state & signals
│   └── forecast_worker.py # Background thread for model training
└── main.py               # Entry point
```

## Technical Stack

- **Modeling**: statsmodels SARIMAX, ruptures (changepoint detection)
- **UI**: PyQt6, PyQt6-WebEngine (for Plotly charts)
- **Data**: pandas, numpy
- **Validation**: scikit-learn (preprocessing)

## Original Notebook Performance

The research notebook (trained on controlled personal dataset) achieved:
- **90.91% directional accuracy** under walk-forward validation
- **p-value: 0.006** for trend weight predictions
- Clean Phase 1 data (identified via changepoint detection)

Current prototype model performance degrades on datasets with:
- Multiple overlapping training phases
- High variance in caloric intake patterns  
- Limited logged nutrition days (<80% completeness)

## Next Steps (Post-Prototype)

**If validated for production:**

1. **Model Improvements**
   - Grid search for optimal SARIMAX orders per dataset characteristics
   - Feature engineering: rolling averages, lagged deficit terms
   - Fallback to simpler linear models for sparse data

2. **UI Refinement**
   - Professional design system (color scheme, typography, spacing)
   - Responsive layouts, accessibility features
   - Comprehensive error messaging and user guidance

3. **Code Quality**
   - Type hints throughout codebase
   - Unit tests for backend modules (target 80%+ coverage)
   - Documentation (docstrings, architecture diagrams)
   - Refactor for maintainability

4. **Distribution**
   - PyInstaller packaging for .exe
   - Installer with proper error handling
   - Crash reporting and logging

## Running the Prototype

**Requirements:**
- Python 3.10+
- Windows (PyQt6-WebEngine dependency)

**Setup:**
```bash
pip install -r requirements.txt
python main.py
```

**Expected workflow:**
1. Import MacroFactor XLSX export
2. Review auto-detected training phase
3. Set target weight and competition date
4. Generate forecast (model trains in background thread)

## Why I'm Sharing This

I believe in transparent development. This branch shows:
- **Iterative process**: Real projects evolve through messy prototypes
- **Prioritization**: Validating feasibility before premature optimization
- **Learning velocity**: Comfortable with rapid skill acquisition (PyQt6, desktop patterns)

Professional work would follow rigorous code review, testing standards, and design iteration. This prototype demonstrates the technical foundation upon which production-quality work is built.

## Contact

For questions about this project or my transition to data science, reach out via:
- **LinkedIn**: [Your LinkedIn]
- **Email**: [Your Email]

---

**Note to recruiters/hiring managers**: This is a development branch. For polished portfolio work, see the main branch's Jupyter notebook analysis demonstrating statistical rigor, validation methodology, and research documentation.