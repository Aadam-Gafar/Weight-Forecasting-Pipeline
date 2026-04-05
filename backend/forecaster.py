"""
Weight forecasting engine using SARIMAX.
"""
import pandas as pd
import numpy as np
from datetime import date, timedelta
from typing import Optional, Callable
from statsmodels.tsa.statespace.sarimax import SARIMAX
from sklearn.preprocessing import StandardScaler

from .models import ForecastResult
from .safety import apply_safety_clipping, validate_forecast_safety, calculate_required_deficit


def train_and_forecast(
    df_clean: pd.DataFrame,
    training_start_date: pd.Timestamp,
    target_weight: float,
    deadline: date,
    progress_callback: Optional[Callable[[str], None]] = None,
    custom_start_date: Optional[pd.Timestamp] = None
) -> ForecastResult:
    """
    Train SARIMAX model and generate weight forecast.
    
    Args:
        df_clean: Cleaned DataFrame from validator.prepare_modeling_data()
        training_start_date: Start date for training window (from phase_detector)
        target_weight: User's target weight in kg
        deadline: Competition/goal deadline
        progress_callback: Optional callback for progress updates
        custom_start_date: Optional custom start date from user (overrides training_start_date)
        
    Returns:
        ForecastResult with predictions and recommendations
        
    Raises:
        ValueError: If custom_start_date results in less than 14 days of data
    """
    # Use custom start date if provided, otherwise use detected training start
    start_date = custom_start_date if custom_start_date is not None else training_start_date
    
    if progress_callback:
        progress_callback(f"Loading dataset ({len(df_clean)} days)...")
    
    # Filter to training window
    df_train = df_clean[df_clean.index >= start_date]
    
    # Validate minimum data requirement
    if len(df_train) < 14:
        raise ValueError(
            f"Insufficient data from selected start date: only {len(df_train)} days available. "
            f"Minimum 14 days required for training. Please select an earlier start date."
        )
    
    if progress_callback:
        progress_callback(f"Training on {len(df_train)} days from {start_date.strftime('%Y-%m-%d')}")
    
    # Prepare target and exogenous variables
    target = df_train['Weight Change (kg)'].copy()
    target.index = pd.DatetimeIndex(target.index)
    target = target.asfreq('D')
    target = target.dropna()
    
    exog_cols = ['Protein (g)', 'Carbs (g)', 'Fat (g)', 'Expenditure', 'Caloric Deficit (kcal)']
    exog = df_train[exog_cols].loc[target.index]
    
    # Scale exogenous variables
    if progress_callback:
        progress_callback("Preprocessing features...")
    
    scaler = StandardScaler()
    exog_scaled = scaler.fit_transform(exog)
    
    # Calculate days to deadline
    last_data_date = df_clean.index[-1].date()
    deadline_date = deadline if isinstance(deadline, date) else deadline.date()
    days_to_deadline = (deadline_date - last_data_date).days
    
    if days_to_deadline <= 0:
        raise ValueError("Deadline must be after the last data point")
    
    # Get current weight
    current_weight = df_clean['Trend Weight (kg)'].iloc[-1]
    
    if progress_callback:
        progress_callback("Training SARIMAX model...")
    
    # Train SARIMAX with simple parameters (no seasonality detected in notebook)
    # Using (0,0,0)×(0,0,0,7) as that's what auto_arima found optimal
    try:
        model = SARIMAX(
            target,
            exog=exog_scaled,
            order=(0, 0, 0),
            seasonal_order=(0, 0, 0, 7)
        )
        fitted_model = model.fit(disp=False)
        
        if progress_callback:
            progress_callback("Model fitted: (0,0,0)×(0,0,0,7)")
    
    except Exception as e:
        # Fallback to simpler model if SARIMAX fails
        if progress_callback:
            progress_callback(f"SARIMAX failed, using fallback model: {str(e)}")
        
        model = SARIMAX(
            target,
            exog=exog_scaled,
            order=(0, 0, 0),
            seasonal_order=(0, 0, 0, 0)
        )
        fitted_model = model.fit(disp=False)
    
    # Generate forecast
    if progress_callback:
        progress_callback(f"Generating {days_to_deadline}-day forecast...")
    
    # Use last known exogenous values extended into future
    # (Assumes user maintains current nutrition pattern)
    last_exog = exog_scaled[-1].reshape(1, -1)
    exog_forecast = np.tile(last_exog, (days_to_deadline, 1))
    
    # Forecast daily weight changes
    forecast_changes = fitted_model.forecast(steps=days_to_deadline, exog=exog_forecast)
    
    # Apply safety clipping
    if progress_callback:
        progress_callback("Applying safety constraints (±0.25% bodyweight/day)...")
    
    forecast_weights = apply_safety_clipping(forecast_changes, current_weight)
    
    # Get predicted weight at deadline
    predicted_weight = forecast_weights.iloc[-1]
    weight_gap = predicted_weight - target_weight
    
    # Validate safety
    is_safe, safety_warning = validate_forecast_safety(
        forecast_weights,
        current_weight,
        target_weight,
        days_to_deadline
    )
    
    if not is_safe:
        if progress_callback:
            progress_callback(f"⚠ Safety warning: {safety_warning}")
    
    # Determine status and recommendation
    status, recommendation, deficit_adjustment = _generate_recommendation(
        current_weight,
        target_weight,
        predicted_weight,
        weight_gap,
        days_to_deadline
    )
    
    if progress_callback:
        progress_callback("Forecast complete ✓")
    
    # Create forecast series with proper dates
    forecast_dates = pd.date_range(
        start=last_data_date + timedelta(days=1),
        periods=days_to_deadline,
        freq='D'
    )
    forecast_series = pd.Series(forecast_weights.values, index=forecast_dates)
    
    return ForecastResult(
        predicted_weight_at_deadline=round(predicted_weight, 1),
        forecast_series=forecast_series,
        current_weight=round(current_weight, 1),
        target_weight=target_weight,
        deadline=deadline_date,
        status=status,
        recommendation=recommendation,
        weight_gap=round(weight_gap, 1),
        required_deficit_adjustment=round(deficit_adjustment, 0)
    )


def _generate_recommendation(
    current_weight: float,
    target_weight: float,
    predicted_weight: float,
    weight_gap: float,
    days_to_deadline: int
) -> tuple[str, str, float]:
    """
    Generate status and recommendation based on forecast.
    
    Returns:
        Tuple of (status, recommendation_text, deficit_adjustment_kcal)
    """
    # Calculate required adjustment
    if abs(weight_gap) <= 0.5:
        # On track - no adjustment needed
        status = 'on_track'
        recommendation = (
            "Your current nutrition plan is on track. Maintain your current "
            "caloric deficit. No adjustment needed."
        )
        deficit_adjustment = 0.0
        
    elif abs(weight_gap) <= 1.5:
        # Minor adjustment needed
        status = 'minor_adjustment'
        
        # Calculate kcal adjustment needed
        deficit_adjustment = calculate_required_deficit(
            predicted_weight,
            target_weight,
            days_to_deadline,
            kcal_per_kg=7700
        )
        
        if weight_gap > 0:
            # Predicted weight over target - need more deficit
            recommendation = (
                f"You're predicted to be {abs(weight_gap):.1f} kg over target. "
                f"Increase your daily caloric deficit by {abs(deficit_adjustment):.0f} kcal "
                f"to hit your target weight safely."
            )
        else:
            # Predicted weight under target - can reduce deficit
            recommendation = (
                f"You're predicted to be {abs(weight_gap):.1f} kg under target. "
                f"You can reduce your daily caloric deficit by {abs(deficit_adjustment):.0f} kcal "
                f"while still hitting your target."
            )
    
    else:
        # Major adjustment needed
        status = 'major_adjustment'
        
        deficit_adjustment = calculate_required_deficit(
            predicted_weight,
            target_weight,
            days_to_deadline,
            kcal_per_kg=7700
        )
        
        if weight_gap > 0:
            recommendation = (
                f"You're predicted to be {abs(weight_gap):.1f} kg over target. "
                f"This requires a {abs(deficit_adjustment):.0f} kcal/day adjustment, which may be aggressive. "
                f"Consider extending your deadline or revising your target weight."
            )
        else:
            recommendation = (
                f"You're predicted to be {abs(weight_gap):.1f} kg under target. "
                f"Your current deficit is too aggressive. Reduce by {abs(deficit_adjustment):.0f} kcal/day "
                f"or consider a more ambitious target weight."
            )
    
    return status, recommendation, deficit_adjustment
