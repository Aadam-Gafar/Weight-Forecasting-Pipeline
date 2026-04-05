"""
Data models for WeightForecaster application.
"""
from dataclasses import dataclass, field
from datetime import date
from typing import Optional
import pandas as pd


@dataclass
class ValidationResult:
    """Result of data validation checks."""
    is_valid: bool
    error_message: Optional[str] = None
    warnings: list[str] = field(default_factory=list)
    stats: dict = field(default_factory=dict)


@dataclass
class ForecastResult:
    """Result of weight forecasting."""
    predicted_weight_at_deadline: float
    forecast_series: pd.Series
    current_weight: float
    target_weight: float
    deadline: date
    status: str  # 'on_track' | 'minor_adjustment' | 'major_adjustment'
    recommendation: str
    weight_gap: float  # Difference from target (positive = over, negative = under)
    required_deficit_adjustment: float  # kcal/day adjustment needed


@dataclass
class AppState:
    """Shared application state."""
    df_raw: Optional[pd.DataFrame] = None
    df_clean: Optional[pd.DataFrame] = None
    current_weight: Optional[float] = None
    target_weight: Optional[float] = None
    deadline: Optional[date] = None
    forecast_result: Optional[ForecastResult] = None
    breakpoints: list = field(default_factory=list)
