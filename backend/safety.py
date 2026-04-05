"""
Safety constraints for weight forecasting.
"""
import numpy as np
import pandas as pd


def apply_safety_clipping(
    forecast_series: pd.Series,
    current_weight: float,
    max_daily_change_pct: float = 0.0025
) -> pd.Series:
    """
    Apply safety constraints to weight forecast.
    
    Clips daily weight changes to physiologically safe limits (default ±0.25% bodyweight/day).
    
    Args:
        forecast_series: Raw forecast of daily weight changes
        current_weight: Current bodyweight in kg
        max_daily_change_pct: Maximum daily change as fraction of bodyweight (default 0.0025 = 0.25%)
        
    Returns:
        Clipped forecast series with cumulative weights
    """
    # Calculate maximum safe daily change
    max_change_kg = current_weight * max_daily_change_pct
    
    # Clip daily changes
    clipped_changes = forecast_series.clip(lower=-max_change_kg, upper=max_change_kg)
    
    # Convert to cumulative weights
    cumulative_change = clipped_changes.cumsum()
    forecast_weights = current_weight + cumulative_change
    
    return forecast_weights


def validate_forecast_safety(
    forecast_weights: pd.Series,
    current_weight: float,
    target_weight: float,
    days_to_deadline: int
) -> tuple[bool, str]:
    """
    Validate that forecast meets safety criteria.
    
    Args:
        forecast_weights: Forecasted weights over time
        current_weight: Starting weight
        target_weight: Goal weight
        days_to_deadline: Number of days until deadline
        
    Returns:
        Tuple of (is_safe, warning_message)
    """
    total_loss = current_weight - target_weight
    
    # Check for extreme weight loss (>1.5 kg/week sustained)
    if days_to_deadline > 0:
        weekly_rate = (total_loss / days_to_deadline) * 7
        
        if weekly_rate > 1.5:
            return (
                False,
                f"Target requires {weekly_rate:.2f} kg/week loss - exceeds safe limit of 1.5 kg/week. "
                "Consider extending deadline or revising target weight."
            )
    
    # Check for extreme single-day drops in forecast
    daily_changes = forecast_weights.diff().abs()
    max_daily_drop = daily_changes.max()
    
    if max_daily_drop > current_weight * 0.03:  # >3% bodyweight in one day
        return (
            False,
            f"Forecast contains unsafe daily weight change ({max_daily_drop:.2f} kg). "
            "This may indicate data quality issues."
        )
    
    return (True, "")


def calculate_required_deficit(
    current_weight: float,
    target_weight: float,
    days_available: int,
    kcal_per_kg: float = 7700
) -> float:
    """
    Calculate required daily caloric deficit to hit target.
    
    Args:
        current_weight: Current weight in kg
        target_weight: Target weight in kg
        days_available: Days until deadline
        kcal_per_kg: Energy equivalent of weight (default 7700 kcal/kg)
        
    Returns:
        Required daily deficit in kcal
    """
    if days_available <= 0:
        return 0.0
    
    total_loss_needed = current_weight - target_weight
    total_deficit_needed = total_loss_needed * kcal_per_kg
    daily_deficit = total_deficit_needed / days_available
    
    return daily_deficit
