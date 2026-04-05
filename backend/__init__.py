"""
WeightForecaster backend package.
"""
from .models import ValidationResult, ForecastResult, AppState
from .data_loader import load_macrofactor_data
from .validator import validate_data, prepare_modeling_data
from .phase_detector import detect_phases, select_optimal_training_phase, calculate_phase_statistics
from .forecaster import train_and_forecast
from .safety import apply_safety_clipping, validate_forecast_safety, calculate_required_deficit

__all__ = [
    'ValidationResult',
    'ForecastResult',
    'AppState',
    'load_macrofactor_data',
    'validate_data',
    'prepare_modeling_data',
    'detect_phases',
    'select_optimal_training_phase',
    'calculate_phase_statistics',
    'train_and_forecast',
    'apply_safety_clipping',
    'validate_forecast_safety',
    'calculate_required_deficit',
]
