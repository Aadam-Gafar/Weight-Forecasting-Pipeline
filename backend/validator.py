"""
Data validation and quality checks module.
"""
import pandas as pd
import numpy as np
from .models import ValidationResult


def validate_data(df_raw: pd.DataFrame) -> ValidationResult:
    """
    Validate MacroFactor data quality and completeness.
    
    Args:
        df_raw: Raw merged DataFrame from data_loader
        
    Returns:
        ValidationResult with validation status, errors, warnings, and stats
    """
    warnings = []
    stats = {}
    
    # Check if DataFrame is empty
    if df_raw.empty:
        return ValidationResult(
            is_valid=False,
            error_message="Dataset is empty"
        )
    
    # Check minimum data requirement (30 days)
    total_days = len(df_raw)
    if total_days < 30:
        return ValidationResult(
            is_valid=False,
            error_message=f"Insufficient data: only {total_days} days found (minimum 30 required)"
        )
    
    # Required columns
    required_cols = [
        'Trend Weight (kg)',
        'Calories (kcal)',
        'Protein (g)',
        'Carbs (g)',
        'Fat (g)',
        'Expenditure'
    ]
    
    missing_cols = [col for col in required_cols if col not in df_raw.columns]
    if missing_cols:
        return ValidationResult(
            is_valid=False,
            error_message=f"Missing required columns: {', '.join(missing_cols)}"
        )
    
    # Check for weight trend data (should be complete)
    if df_raw['Trend Weight (kg)'].isnull().all():
        return ValidationResult(
            is_valid=False,
            error_message="No weight data found in 'Trend Weight (kg)' column"
        )
    
    # Calculate nutrition logging completeness
    nutrition_cols = ['Calories (kcal)', 'Protein (g)', 'Carbs (g)', 'Fat (g)']
    nutrition_complete = df_raw[nutrition_cols].notna().all(axis=1)
    logged_days = nutrition_complete.sum()
    completeness_pct = (logged_days / total_days) * 100
    
    if logged_days < 14:
        return ValidationResult(
            is_valid=False,
            error_message=f"Insufficient nutrition logs: only {logged_days} days logged (minimum 14 required)"
        )
    
    # Warning for low completeness
    if completeness_pct < 70:
        warnings.append(f"Low nutrition logging: {completeness_pct:.0f}% complete")
    
    # Check for extended gaps in logging (3+ consecutive days)
    missing_streaks = (~nutrition_complete).astype(int).groupby(nutrition_complete.cumsum()).sum()
    max_missing = missing_streaks.max() if len(missing_streaks) > 0 else 0
    
    if max_missing >= 3:
        warnings.append(f"Extended gap in logging: {max_missing} consecutive days without nutrition data")
    
    # Check for unusual weight swings (>2.5% bodyweight in one day)
    df_raw['Weight Change (kg)'] = df_raw['Trend Weight (kg)'].diff()
    weight_change_pct = (df_raw['Weight Change (kg)'].abs() / df_raw['Trend Weight (kg)'].shift(1)) * 100
    unusual_changes = weight_change_pct > 2.5
    unusual_count = unusual_changes.sum()
    
    if unusual_count > 0:
        warnings.append(f"{unusual_count} unusual weight swing(s) detected (>2.5% daily change)")
    
    # Infer current weight (most recent trend weight)
    current_weight = df_raw['Trend Weight (kg)'].dropna().iloc[-1]
    
    # Calculate stats
    stats = {
        'date_range_start': df_raw.index.min().strftime('%Y-%m-%d'),
        'date_range_end': df_raw.index.max().strftime('%Y-%m-%d'),
        'total_days': total_days,
        'logged_days': int(logged_days),
        'completeness_pct': round(completeness_pct, 1),
        'current_weight': round(current_weight, 1),
        'max_missing_streak': int(max_missing),
        'unusual_changes': int(unusual_count)
    }
    
    return ValidationResult(
        is_valid=True,
        warnings=warnings,
        stats=stats
    )


def prepare_modeling_data(df_raw: pd.DataFrame) -> pd.DataFrame:
    """
    Prepare cleaned DataFrame for modeling.
    
    Drops rows with missing nutrition data and selects modeling features.
    
    Args:
        df_raw: Raw merged DataFrame
        
    Returns:
        Cleaned DataFrame ready for modeling
    """
    # Drop rows with missing nutrition (only keep logged days)
    df_clean = df_raw.dropna(subset=['Calories (kcal)', 'Protein (g)', 'Carbs (g)', 'Fat (g)'])
    
    # Select modeling columns
    modeling_cols = [
        'Trend Weight (kg)',
        'Protein (g)',
        'Carbs (g)',
        'Fat (g)',
        'Expenditure'
    ]
    
    df_clean = df_clean[modeling_cols].copy()
    
    # Calculate derived features
    df_clean['Weight Change (kg)'] = df_clean['Trend Weight (kg)'].diff()
    df_clean['Caloric Deficit (kcal)'] = df_raw.loc[df_clean.index, 'Calories (kcal)'] - df_clean['Expenditure']
    
    # Drop Calories column (redundant with Caloric Deficit)
    # Keep Caloric Deficit as it's the fundamental driver
    
    return df_clean
