"""
Background worker for model training.
Prevents UI freezing during SARIMAX training.
"""
from PyQt6.QtCore import QThread, pyqtSignal
from datetime import date
from typing import Optional
import pandas as pd

from backend import train_and_forecast, ForecastResult


class ForecastWorker(QThread):
    """Background thread for model training and forecasting."""
    
    # Signals
    progress = pyqtSignal(str)  # Progress messages for console
    finished = pyqtSignal(object)  # ForecastResult on success
    error = pyqtSignal(str)  # Error message on failure
    
    def __init__(
        self,
        df_clean: pd.DataFrame,
        training_start: pd.Timestamp,
        target_weight: float,
        deadline: date,
        custom_start_date: Optional[pd.Timestamp] = None
    ):
        super().__init__()
        
        self.df_clean = df_clean
        self.training_start = training_start
        self.target_weight = target_weight
        self.deadline = deadline
        self.custom_start_date = custom_start_date
        self._is_running = True
    
    def run(self):
        """Execute forecasting in background thread."""
        try:
            # Train and forecast with progress callbacks
            result = train_and_forecast(
                df_clean=self.df_clean,
                training_start_date=self.training_start,
                target_weight=self.target_weight,
                deadline=self.deadline,
                progress_callback=self._emit_progress,
                custom_start_date=self.custom_start_date
            )
            
            # Emit result
            if self._is_running:
                self.finished.emit(result)
            
        except Exception as e:
            if self._is_running:
                self.error.emit(f"Forecasting failed: {str(e)}")
    
    def _emit_progress(self, message: str):
        """Progress callback for backend."""
        if self._is_running:
            self.progress.emit(message)
    
    def stop(self):
        """Stop the worker thread."""
        self._is_running = False
        self.quit()
        self.wait()
