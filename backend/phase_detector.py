"""
Training phase detection using changepoint analysis.
"""
import pandas as pd
import numpy as np
import ruptures as rpt
from typing import List, Optional, Callable


def detect_phases(
    df_clean: pd.DataFrame,
    n_breakpoints: int = 3,
    progress_callback: Optional[Callable[[str], None]] = None
) -> List[pd.Timestamp]:
    """
    Detect training phases using changepoint detection on weight trend.
    
    Args:
        df_clean: Cleaned DataFrame from validator.prepare_modeling_data()
        n_breakpoints: Number of breakpoints to detect (default: 3)
        progress_callback: Optional callback for progress updates
        
    Returns:
        List of breakpoint timestamps (excluding start/end boundaries)
    """
    if progress_callback:
        progress_callback("Detecting training phases...")
    
    # Extract weight trend signal
    signal = df_clean['Trend Weight (kg)'].dropna().values.reshape(-1, 1)
    index = df_clean['Trend Weight (kg)'].dropna().index
    
    if len(signal) < 10:
        if progress_callback:
            progress_callback("Insufficient data for phase detection")
        return []
    
    # Binary segmentation for changepoint detection
    algo = rpt.Binseg(model="l2").fit(signal)
    
    # Detect breakpoints
    breakpoints_idx = algo.predict(n_bkps=n_breakpoints)
    
    # Convert indices to timestamps (exclude last index which is end boundary)
    breakpoints = [index[bp] for bp in breakpoints_idx[:-1]]
    
    if progress_callback:
        progress_callback(f"Found {len(breakpoints)} breakpoint(s) ({len(breakpoints) + 1} phases identified)")
    
    return breakpoints


def select_optimal_training_phase(
    df_clean: pd.DataFrame,
    breakpoints: List[pd.Timestamp]
) -> pd.Timestamp:
    """
    Select the optimal training phase start date.
    
    For weight cut forecasting, prioritizes the most recent phase with
    consistent weight loss (cut phase).
    
    Args:
        df_clean: Cleaned DataFrame
        breakpoints: List of breakpoint timestamps
        
    Returns:
        Start date for training window (most recent breakpoint or start of data)
    """
    if not breakpoints:
        # No breakpoints detected - use all data
        return df_clean.index[0]
    
    # Use most recent phase (after last breakpoint)
    # This assumes user wants to forecast based on current training phase
    return breakpoints[-1]


def calculate_phase_statistics(
    df_clean: pd.DataFrame,
    breakpoints: List[pd.Timestamp]
) -> List[dict]:
    """
    Calculate statistics for each detected phase.
    
    Args:
        df_clean: Cleaned DataFrame
        breakpoints: List of breakpoint timestamps
        
    Returns:
        List of phase statistics dictionaries
    """
    phase_boundaries = [df_clean.index[0]] + breakpoints + [df_clean.index[-1]]
    phase_stats = []
    
    for i in range(len(phase_boundaries) - 1):
        phase_start = phase_boundaries[i]
        phase_end = phase_boundaries[i + 1]
        phase_data = df_clean.loc[phase_start:phase_end]
        
        weight_change = phase_data['Trend Weight (kg)'].iloc[-1] - phase_data['Trend Weight (kg)'].iloc[0]
        duration_days = len(phase_data)
        avg_deficit = phase_data['Caloric Deficit (kcal)'].mean()
        weekly_rate = (weight_change / duration_days * 7) if duration_days > 0 else 0
        
        # Classify phase
        if abs(weekly_rate) < 0.2:
            phase_type = "Maintenance"
        elif weight_change < 0:
            phase_type = "Cut"
        else:
            phase_type = "Bulk"
        
        phase_stats.append({
            'phase_number': i + 1,
            'start_date': phase_start.strftime('%Y-%m-%d'),
            'end_date': phase_end.strftime('%Y-%m-%d'),
            'duration_days': duration_days,
            'weight_change_kg': round(weight_change, 2),
            'avg_daily_deficit_kcal': round(avg_deficit, 0),
            'weekly_rate_kg': round(weekly_rate, 2),
            'classification': phase_type
        })
    
    return phase_stats
