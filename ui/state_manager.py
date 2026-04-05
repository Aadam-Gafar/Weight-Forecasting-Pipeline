"""
Application state manager for WeightForecaster.
Coordinates data flow between UI panels and backend.
"""
from PyQt6.QtCore import QObject, pyqtSignal
from datetime import date
from typing import Optional
import pandas as pd

from backend import (
    load_macrofactor_data,
    validate_data,
    prepare_modeling_data,
    detect_phases,
    select_optimal_training_phase,
    calculate_phase_statistics,
    ValidationResult,
    ForecastResult
)


class AppStateManager(QObject):
    """Manages application state and coordinates backend operations."""
    
    # Signals for UI updates
    data_loaded = pyqtSignal(object)  # ValidationResult
    data_load_failed = pyqtSignal(str)  # Error message
    
    forecast_started = pyqtSignal()
    forecast_progress = pyqtSignal(str)  # Progress message
    forecast_completed = pyqtSignal(object)  # ForecastResult
    forecast_failed = pyqtSignal(str)  # Error message
    
    def __init__(self):
        super().__init__()
        
        # Data storage
        self.df_raw: Optional[pd.DataFrame] = None
        self.df_clean: Optional[pd.DataFrame] = None
        self.validation: Optional[ValidationResult] = None
        self.breakpoints: list = []
        self.training_start: Optional[pd.Timestamp] = None
        
        # User inputs
        self.current_weight: Optional[float] = None
        self.target_weight: Optional[float] = None
        self.deadline: Optional[date] = None
        self.custom_start_date: Optional[pd.Timestamp] = None  # User-selected start date
        
        # Results
        self.forecast_result: Optional[ForecastResult] = None
    
    def load_data(self, filepath: str):
        """
        Load MacroFactor data from file.
        
        Emits:
            data_loaded(ValidationResult) on success
            data_load_failed(str) on error
        """
        try:
            # Load raw data
            self.df_raw = load_macrofactor_data(filepath)
            
            # Validate
            self.validation = validate_data(self.df_raw)
            
            if not self.validation.is_valid:
                self.data_load_failed.emit(self.validation.error_message)
                return
            
            # Prepare modeling data
            self.df_clean = prepare_modeling_data(self.df_raw)
            
            # Infer current weight
            self.current_weight = self.validation.stats['current_weight']
            
            # Detect phases (for future phase analysis display)
            self.breakpoints = detect_phases(self.df_clean, n_breakpoints=3)
            self.training_start = select_optimal_training_phase(self.df_clean, self.breakpoints)
            
            # Success
            self.data_loaded.emit(self.validation)
            
        except Exception as e:
            self.data_load_failed.emit(str(e))
    
    def set_target_config(self, target_weight: float, deadline: date):
        """Store user's target configuration."""
        self.target_weight = target_weight
        self.deadline = deadline
    
    def set_custom_start_date(self, start_date: pd.Timestamp):
        """Store user's custom training start date."""
        self.custom_start_date = start_date
    
    def get_available_date_range(self) -> tuple[pd.Timestamp, pd.Timestamp]:
        """Get the available date range for training data."""
        if self.df_clean is None or len(self.df_clean) == 0:
            return None, None
        return self.df_clean.index.min(), self.df_clean.index.max()
    
    def get_phase_statistics(self) -> list[dict]:
        """Get statistics for detected training phases."""
        if not self.df_clean or not self.breakpoints:
            return []
        return calculate_phase_statistics(self.df_clean, self.breakpoints)
    
    def get_historical_data(self) -> pd.DataFrame:
        """Get cleaned historical data for charting."""
        return self.df_clean if self.df_clean is not None else pd.DataFrame()
    
    def is_ready_to_forecast(self) -> bool:
        """Check if all required data is available for forecasting."""
        return (
            self.df_clean is not None
            and self.training_start is not None
            and self.target_weight is not None
            and self.deadline is not None
            and self.current_weight is not None
        )
