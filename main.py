"""
WeightForecaster - FULLY Unrestricted Calendar
"""
import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QDateEdit, QFileDialog
)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import Qt, QDate, pyqtSignal
from datetime import datetime, date
import plotly.graph_objects as go
import pandas as pd

from ui.state_manager import AppStateManager
from ui.forecast_worker import ForecastWorker


class Sidebar(QWidget):
    """Left sidebar with all controls and data display."""
    
    forecast_requested = pyqtSignal()
    
    def __init__(self, state_manager: AppStateManager):
        super().__init__()
        self.state = state_manager
        self.init_ui()
        
        self.state.data_loaded.connect(self.on_data_loaded)
        self.state.data_load_failed.connect(self.on_data_failed)
    
    def init_ui(self):
        self.setFixedWidth(280)
        self.setStyleSheet("""
            QWidget {
                background-color: #4A4A4A;
                color: white;
            }
            QPushButton {
                background-color: black;
                color: white;
                border: none;
                padding: 12px;
                font-size: 11pt;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #333;
            }
            QPushButton:disabled {
                background-color: #666;
                color: #999;
            }
            QLineEdit, QDateEdit {
                background-color: black;
                color: white;
                border: none;
                padding: 8px;
                font-size: 10pt;
            }
            QLabel {
                font-size: 9pt;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Import Data Section
        self.import_btn = QPushButton("Import data")
        self.import_btn.clicked.connect(self.on_import_clicked)
        layout.addWidget(self.import_btn)
        
        layout.addWidget(self.create_separator())
        
        # Data Stats
        self.data_loaded_label = QLabel("Data loaded: ---")
        layout.addWidget(self.data_loaded_label)
        
        self.date_range_label = QLabel("Date range: ---")
        self.total_days_label = QLabel("Total days: ---")
        self.nutrition_logs_label = QLabel("Nutrition logs: ---")
        self.current_weight_label = QLabel("Current weight: ---")
        
        layout.addWidget(self.date_range_label)
        layout.addWidget(self.total_days_label)
        layout.addWidget(self.nutrition_logs_label)
        layout.addWidget(self.current_weight_label)
        
        # Warnings
        self.warnings_label = QLabel("Warnings: ---")
        self.warnings_label.setWordWrap(True)
        layout.addWidget(self.warnings_label)
        
        # Errors
        self.errors_label = QLabel("")
        self.errors_label.setWordWrap(True)
        self.errors_label.setStyleSheet("color: #EE5A6F; font-size: 9pt;")
        self.errors_label.hide()
        layout.addWidget(self.errors_label)
        
        layout.addWidget(self.create_separator())
        
        # Start Date Picker - COMPLETELY UNRESTRICTED
        layout.addWidget(QLabel("Training start date:"))
        self.start_date_input = QDateEdit()
        self.start_date_input.setCalendarPopup(True)
        self.start_date_input.setEnabled(False)
        # DO NOT SET ANY DATE RANGE - let it be fully open
        self.start_date_input.dateChanged.connect(self.on_start_date_changed)
        layout.addWidget(self.start_date_input)
        
        self.training_days_label = QLabel("Training days: ---")
        layout.addWidget(self.training_days_label)
        
        layout.addWidget(self.create_separator())
        
        # Target Configuration
        layout.addWidget(QLabel("Target weight:"))
        target_container = QHBoxLayout()
        self.target_input = QLineEdit()
        self.target_input.setPlaceholderText("70.0")
        self.target_input.textChanged.connect(self.on_input_changed)
        target_container.addWidget(self.target_input)
        target_container.addWidget(QLabel("kg"))
        layout.addLayout(target_container)
        
        layout.addWidget(QLabel("Competition date:"))
        self.deadline_input = QDateEdit()
        self.deadline_input.setCalendarPopup(True)
        self.deadline_input.setDate(QDate.currentDate().addDays(60))
        self.deadline_input.dateChanged.connect(self.on_input_changed)
        layout.addWidget(self.deadline_input)
        
        # Summary Stats
        self.required_loss_label = QLabel("Required loss: ---")
        self.days_available_label = QLabel("Days available: ---")
        self.target_rate_label = QLabel("Target rate: ---")
        
        layout.addWidget(self.required_loss_label)
        layout.addWidget(self.days_available_label)
        layout.addWidget(self.target_rate_label)
        
        layout.addWidget(self.create_separator())
        
        # Forecast Button
        self.forecast_btn = QPushButton("Forecast")
        self.forecast_btn.setEnabled(False)
        self.forecast_btn.clicked.connect(self.on_forecast_clicked)
        layout.addWidget(self.forecast_btn)
        
        layout.addStretch()
        
        self.setLayout(layout)
    
    def create_separator(self):
        line = QWidget()
        line.setFixedHeight(1)
        line.setStyleSheet("background-color: #666;")
        return line
    
    def on_import_clicked(self):
        filepath, _ = QFileDialog.getOpenFileName(
            self,
            "Select MacroFactor Data",
            "",
            "Excel Files (*.xlsx)"
        )
        
        if filepath:
            self.errors_label.hide()
            self.errors_label.clear()
            
            self.data_loaded_label.setText("Data loaded: Loading...")
            self.state.load_data(filepath)
    
    def on_data_loaded(self, validation):
        """Update UI when data loads successfully."""
        self.data_loaded_label.setText("Data loaded: ✓")
        self.data_loaded_label.setStyleSheet("color: #26DE81; font-weight: bold;")
        
        stats = validation.stats
        
        self.date_range_label.setText(f"Date range: {stats['date_range_start']} - {stats['date_range_end']}")
        self.total_days_label.setText(f"Total days: {stats['total_days']}")
        self.nutrition_logs_label.setText(f"Nutrition logs: {stats['logged_days']}/{stats['total_days']}")
        self.current_weight_label.setText(f"Current weight: {stats['current_weight']} kg")
        
        # Warnings
        if validation.warnings:
            warning_text = "\n".join(f"⚠ {w}" for w in validation.warnings)
            self.warnings_label.setText(f"Warnings:\n{warning_text}")
            self.warnings_label.setStyleSheet("color: #FED330;")
        else:
            self.warnings_label.setText("Warnings: None")
            self.warnings_label.setStyleSheet("color: white;")
        
        # Setup start date picker
        # Use training_start from state - this is set by select_optimal_training_phase
        # which uses the LAST breakpoint (most recent phase) as per notebook logic
        if self.state.training_start:
            default_start = self.state.training_start
        else:
            # Fallback to first date if no breakpoints
            min_date, _ = self.state.get_available_date_range()
            default_start = min_date
        
        # Set the date without any restrictions
        self.start_date_input.setDate(QDate(default_start.year, default_start.month, default_start.day))
        self.start_date_input.setEnabled(True)
        
        # Store immediately
        self.state.set_custom_start_date(default_start)
        
        self.update_training_days()
        
        # Pre-fill target
        if not self.target_input.text():
            suggested = stats['current_weight'] - 5.0
            self.target_input.setText(f"{suggested:.1f}")
        
        self.update_summary()
    
    def on_data_failed(self, error_message):
        self.data_loaded_label.setText("Data loaded: ✗")
        self.data_loaded_label.setStyleSheet("color: #EE5A6F; font-weight: bold;")
        
        self.errors_label.setText(f"Errors:\n❌ {error_message}")
        self.errors_label.show()
        
        self.warnings_label.setText("Warnings: ---")
        self.warnings_label.setStyleSheet("color: white;")
    
    def on_start_date_changed(self, qdate):
        """Handle start date selection - validate but allow any date."""
        # Check if date is within data range
        min_date, max_date = self.state.get_available_date_range()
        
        if min_date and max_date:
            selected_date = pd.Timestamp(qdate.year(), qdate.month(), qdate.day())
            
            # Check if out of data range
            if selected_date < min_date or selected_date > max_date:
                self.errors_label.setText(
                    f"Errors:\n❌ Selected date is outside data range\n"
                    f"Available: {min_date.strftime('%Y-%m-%d')} to {max_date.strftime('%Y-%m-%d')}"
                )
                self.errors_label.show()
                self.forecast_btn.setEnabled(False)
                self.training_days_label.setText("Training days: ---")
                self.training_days_label.setStyleSheet("color: white;")
                return
            
            self.state.set_custom_start_date(selected_date)
            self.update_training_days()
            
            # Clear error if it was about date range
            if "outside data range" in self.errors_label.text():
                self.errors_label.clear()
                self.errors_label.hide()
            
            self.on_input_changed()
    
    def on_input_changed(self):
        """Re-validate when inputs change."""
        self.update_summary()
    
    def update_training_days(self):
        """Update training days and show error if insufficient."""
        if self.state.df_clean is not None:
            start_date = self.state.custom_start_date or self.state.training_start
            if start_date:
                df_subset = self.state.df_clean[self.state.df_clean.index >= start_date]
                days = len(df_subset)
                self.training_days_label.setText(f"Training days: {days}")
                
                if days < 14:
                    self.training_days_label.setStyleSheet("color: #EE5A6F;")
                    self.errors_label.setText(f"Errors:\n❌ Insufficient training data: {days} days (minimum 14 required)")
                    self.errors_label.show()
                else:
                    self.training_days_label.setStyleSheet("color: #26DE81;")
                    if "Insufficient training data" in self.errors_label.text():
                        self.errors_label.clear()
                        self.errors_label.hide()
    
    def update_summary(self):
        """Update summary and validate."""
        try:
            if not self.state.current_weight:
                return
            
            current = self.state.current_weight
            target = float(self.target_input.text())
            deadline = self.deadline_input.date().toPyDate()
            
            last_date = self.state.df_clean.index[-1].date()
            days_available = (deadline - last_date).days
            required_loss = current - target
            weekly_rate = (required_loss / days_available * 7) if days_available > 0 else 0
            
            self.required_loss_label.setText(f"Required loss: {required_loss:.1f} kg")
            self.days_available_label.setText(f"Days available: {days_available}")
            self.target_rate_label.setText(f"Target rate: {weekly_rate:.2f} kg/week")
            
            # Check training days
            start_date = self.state.custom_start_date or self.state.training_start
            if start_date:
                # Check if within data range
                min_date, max_date = self.state.get_available_date_range()
                if start_date < min_date or start_date > max_date:
                    # Out of range
                    self.forecast_btn.setEnabled(False)
                    return
                
                df_subset = self.state.df_clean[self.state.df_clean.index >= start_date]
                training_days = len(df_subset)
            else:
                training_days = 0
            
            # Validate
            is_valid = (
                target > 0 
                and days_available > 0 
                and required_loss > 0
                and training_days >= 14
            )
            self.forecast_btn.setEnabled(is_valid)
            
            if is_valid:
                self.state.set_target_config(target, deadline)
            
        except (ValueError, AttributeError):
            self.forecast_btn.setEnabled(False)
    
    def on_forecast_clicked(self):
        self.errors_label.clear()
        self.errors_label.hide()
        
        self.forecast_requested.emit()
    
    def show_error(self, error_message: str):
        self.errors_label.setText(f"Errors:\n❌ {error_message}")
        self.errors_label.show()


class MainWindow(QMainWindow):
    """Main application window."""
    
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("WeightForecaster")
        self.setMinimumSize(1100, 700)
        self.resize(1400, 900)
        
        self.state = AppStateManager()
        self.worker = None
        
        self.init_ui()
    
    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        self.sidebar = Sidebar(self.state)
        self.sidebar.forecast_requested.connect(self.start_forecast)
        main_layout.addWidget(self.sidebar)
        
        content = QWidget()
        content.setStyleSheet("background-color: #B8B8B8;")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        
        chart_container = QWidget()
        chart_container.setStyleSheet("background-color: #E8E8E8; margin: 30px;")
        chart_layout = QVBoxLayout(chart_container)
        
        self.chart_view = QWebEngineView()
        self.chart_view.setMinimumHeight(400)
        chart_layout.addWidget(self.chart_view)
        
        content_layout.addWidget(chart_container, stretch=1)
        
        status_section = self.create_status_section()
        content_layout.addWidget(status_section)
        
        main_layout.addWidget(content, stretch=1)
    
    def create_status_section(self):
        container = QWidget()
        container.setStyleSheet("background-color: #B8B8B8;")
        container.setFixedHeight(180)
        
        layout = QHBoxLayout(container)
        layout.setContentsMargins(30, 20, 30, 20)
        
        status_container = QWidget()
        status_layout = QVBoxLayout(status_container)
        status_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.status_indicator = QLabel("●")
        self.status_indicator.setStyleSheet("color: #666; font-size: 60pt;")
        self.status_indicator.setAlignment(Qt.AlignmentFlag.AlignCenter)
        status_layout.addWidget(self.status_indicator)
        
        self.status_text = QLabel("--")
        self.status_text.setStyleSheet("font-size: 18pt; font-weight: bold; color: #666;")
        self.status_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        status_layout.addWidget(self.status_text)
        
        layout.addWidget(status_container, stretch=1)
        
        pred_container = QWidget()
        pred_layout = QVBoxLayout(pred_container)
        pred_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.prediction_label = QLabel("Predicted weight at deadline: --\nDifference from Target: --")
        self.prediction_label.setStyleSheet("font-size: 12pt; color: #333;")
        self.prediction_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pred_layout.addWidget(self.prediction_label)
        
        layout.addWidget(pred_container, stretch=1)
        
        rec_container = QWidget()
        rec_container.setStyleSheet("background-color: #8A8A8A; padding: 15px;")
        rec_layout = QVBoxLayout(rec_container)
        
        rec_title = QLabel("Recommendation: --")
        rec_title.setStyleSheet("font-size: 10pt; font-weight: bold; color: white;")
        rec_layout.addWidget(rec_title)
        
        self.recommendation_text = QLabel("")
        self.recommendation_text.setWordWrap(True)
        self.recommendation_text.setStyleSheet("font-size: 9pt; color: white;")
        rec_layout.addWidget(self.recommendation_text)
        
        layout.addWidget(rec_container, stretch=2)
        
        return container
    
    def start_forecast(self):
        if not self.state.is_ready_to_forecast():
            return
        
        self.worker = ForecastWorker(
            df_clean=self.state.df_clean,
            training_start=self.state.training_start,
            target_weight=self.state.target_weight,
            deadline=self.state.deadline,
            custom_start_date=self.state.custom_start_date
        )
        
        self.worker.finished.connect(self.on_forecast_complete)
        self.worker.error.connect(self.on_forecast_error)
        
        self.sidebar.forecast_btn.setEnabled(False)
        self.sidebar.forecast_btn.setText("Forecasting...")
        
        self.worker.start()
    
    def on_forecast_complete(self, result):
        self.sidebar.forecast_btn.setEnabled(True)
        self.sidebar.forecast_btn.setText("Forecast")
        
        status_config = {
            'on_track': ('●', 'On Track', '#26DE81'),
            'minor_adjustment': ('●', 'Minor Adjustment', '#FED330'),
            'major_adjustment': ('●', 'Major Adjustment', '#EE5A6F')
        }
        
        _, text, color = status_config[result.status]
        self.status_indicator.setStyleSheet(f"color: {color}; font-size: 60pt;")
        self.status_text.setText(text)
        self.status_text.setStyleSheet(f"font-size: 18pt; font-weight: bold; color: {color};")
        
        self.prediction_label.setText(
            f"Predicted weight at deadline: {result.predicted_weight_at_deadline} kg\n"
            f"Difference from Target: {result.weight_gap:+.1f}kg"
        )
        
        self.recommendation_text.setText(result.recommendation)
        
        self.render_chart(result)
    
    def on_forecast_error(self, error_message):
        self.sidebar.show_error(error_message)
        self.sidebar.forecast_btn.setEnabled(True)
        self.sidebar.forecast_btn.setText("Forecast")
    
    def render_chart(self, result):
        fig = go.Figure()
        
        historical = self.state.df_clean
        start_date = self.state.custom_start_date or self.state.training_start
        if start_date:
            historical_display = historical[historical.index >= start_date]
        else:
            historical_display = historical
        
        fig.add_trace(go.Scatter(
            x=historical_display.index,
            y=historical_display['Trend Weight (kg)'],
            name='Actual Weight',
            line=dict(color='#2E86DE', width=3),
            mode='lines'
        ))
        
        fig.add_trace(go.Scatter(
            x=result.forecast_series.index,
            y=result.forecast_series.values,
            name='Forecast',
            line=dict(color='#EE5A6F', width=3, dash='dash'),
            mode='lines'
        ))
        
        fig.add_hline(
            y=result.target_weight,
            line=dict(color='#26DE81', width=2, dash='dot')
        )
        
        deadline_dt = datetime.combine(result.deadline, datetime.min.time())
        fig.add_shape(
            type='line',
            x0=deadline_dt, x1=deadline_dt,
            y0=0, y1=1,
            yref='paper',
            line=dict(color='#26DE81', width=2, dash='dot')
        )
        
        fig.update_layout(
            template='plotly_white',
            showlegend=False,
            margin=dict(l=40, r=40, t=20, b=40),
            xaxis_title='',
            yaxis_title='Weight (kg)',
            plot_bgcolor='#E8E8E8',
            paper_bgcolor='#E8E8E8',
            font=dict(size=11)
        )
        
        html = fig.to_html(include_plotlyjs='cdn')
        self.chart_view.setHtml(html)


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("WeightForecaster")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()