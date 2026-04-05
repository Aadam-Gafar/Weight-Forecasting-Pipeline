"""
Fixed Results Panel Integration - Proper datetime handling for Plotly
"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QTextEdit
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import Qt
import plotly.graph_objects as go
from datetime import datetime

from ui.state_manager import AppStateManager
from ui.forecast_worker import ForecastWorker


class ResultsPanelExample(QWidget):
    """Example results panel with forecasting and chart display."""
    
    def __init__(self, state_manager: AppStateManager):
        super().__init__()
        self.state = state_manager
        self.worker = None
        
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Loading overlay (hidden initially)
        self.console = QTextEdit()
        self.console.setReadOnly(True)
        self.console.setMaximumHeight(150)
        self.console.setStyleSheet("""
            QTextEdit {
                background-color: #2C3E50;
                color: #ECF0F1;
                font-family: 'Courier New', monospace;
                padding: 10px;
            }
        """)
        self.console.hide()
        layout.addWidget(self.console)
        
        # Chart display (Plotly in WebEngine)
        self.chart_view = QWebEngineView()
        self.chart_view.setMinimumHeight(400)
        layout.addWidget(self.chart_view)
        
        # Status display
        self.status_label = QLabel()
        self.status_label.setStyleSheet("font-size: 24pt; font-weight: bold;")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)
        
        # Prediction display
        self.prediction_label = QLabel()
        self.prediction_label.setStyleSheet("font-size: 14pt;")
        self.prediction_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.prediction_label)
        
        # Recommendation display
        self.recommendation_label = QLabel()
        self.recommendation_label.setWordWrap(True)
        self.recommendation_label.setStyleSheet("padding: 20px;")
        layout.addWidget(self.recommendation_label)
        
        # Back button
        self.back_btn = QPushButton("← Adjust Inputs")
        layout.addWidget(self.back_btn)
        
        self.setLayout(layout)
    
    def showEvent(self, event):
        """Start forecasting when panel becomes visible."""
        super().showEvent(event)
        
        if self.state.is_ready_to_forecast() and not self.worker:
            self.start_forecasting()
    
    def start_forecasting(self):
        """Launch background worker to train model."""
        # Show console
        self.console.clear()
        self.console.append("═" * 60)
        self.console.append("Training Model...")
        self.console.append("═" * 60)
        self.console.show()
        
        # Hide results until complete
        self.chart_view.hide()
        self.status_label.hide()
        self.prediction_label.hide()
        self.recommendation_label.hide()
        
        # Create worker thread
        self.worker = ForecastWorker(
            df_clean=self.state.df_clean,
            training_start=self.state.training_start,
            target_weight=self.state.target_weight,
            deadline=self.state.deadline
        )
        
        # Connect signals
        self.worker.progress.connect(self.on_progress)
        self.worker.finished.connect(self.on_forecast_complete)
        self.worker.error.connect(self.on_forecast_error)
        
        # Start background processing
        self.worker.start()
    
    def on_progress(self, message: str):
        """Update console with progress message."""
        self.console.append(f"  > {message}")
        # Auto-scroll to bottom
        self.console.verticalScrollBar().setValue(
            self.console.verticalScrollBar().maximum()
        )
    
    def on_forecast_complete(self, result):
        """Display forecast results."""
        # Store result
        self.state.forecast_result = result
        
        # Hide console
        self.console.hide()
        
        # Display status
        status_config = {
            'on_track': ('🟢 On Track', '#26DE81'),
            'minor_adjustment': ('🟡 Minor Adjustment', '#FED330'),
            'major_adjustment': ('🔴 Major Adjustment', '#EE5A6F')
        }
        
        status_text, status_color = status_config[result.status]
        self.status_label.setText(status_text)
        self.status_label.setStyleSheet(
            f"font-size: 24pt; font-weight: bold; color: {status_color};"
        )
        self.status_label.show()
        
        # Display prediction
        pred_text = f"""
        Predicted Weight at Deadline: {result.predicted_weight_at_deadline} kg
        Difference from Target: {result.weight_gap:+.1f} kg
        """
        self.prediction_label.setText(pred_text)
        self.prediction_label.show()
        
        # Display recommendation
        self.recommendation_label.setText(f"Recommendation:\n{result.recommendation}")
        self.recommendation_label.show()
        
        # Render chart
        self.render_chart(result)
        self.chart_view.show()
    
    def on_forecast_error(self, error_message):
        """Display error message."""
        self.console.append(f"\n✗ Error: {error_message}")
        # Keep console visible to show error
    
    def render_chart(self, result):
        """Create Plotly chart and display in WebEngine."""
        fig = go.Figure()
        
        # Historical data
        historical = self.state.df_clean
        fig.add_trace(go.Scatter(
            x=historical.index,
            y=historical['Trend Weight (kg)'],
            name='Actual Weight',
            line=dict(color='#2E86DE', width=2),
            mode='lines',
            hovertemplate='%{x|%Y-%m-%d}<br>Weight: %{y:.1f} kg<extra></extra>'
        ))
        
        # Forecast
        fig.add_trace(go.Scatter(
            x=result.forecast_series.index,
            y=result.forecast_series.values,
            name='Forecast',
            line=dict(color='#EE5A6F', width=2, dash='dash'),
            mode='lines',
            hovertemplate='%{x|%Y-%m-%d}<br>Predicted: %{y:.1f} kg<extra></extra>'
        ))
        
        # Target line (horizontal)
        fig.add_hline(
            y=result.target_weight,
            line=dict(color='#26DE81', width=2, dash='dot'),
            annotation_text=f'Target: {result.target_weight} kg',
            annotation_position='right'
        )
        
        # Deadline marker (vertical) - Use datetime object
        # Convert date to datetime for Plotly compatibility
        if hasattr(result.deadline, 'year'):  # It's a date object
            deadline_dt = datetime.combine(result.deadline, datetime.min.time())
        else:  # Already datetime
            deadline_dt = result.deadline
        
        # Add deadline as a vertical shape instead of vline (more reliable)
        fig.add_shape(
            type='line',
            x0=deadline_dt,
            x1=deadline_dt,
            y0=0,
            y1=1,
            yref='paper',
            line=dict(color='#26DE81', width=2, dash='dot')
        )
        
        # Add deadline annotation manually
        fig.add_annotation(
            x=deadline_dt,
            y=1,
            yref='paper',
            text='Deadline',
            showarrow=False,
            yshift=10,
            font=dict(color='#26DE81')
        )
        
        # Styling
        fig.update_layout(
            template='plotly_white',
            hovermode='x unified',
            showlegend=True,
            margin=dict(l=60, r=40, t=40, b=60),
            xaxis_title='Date',
            yaxis_title='Weight (kg)',
            height=400
        )
        
        # Render to HTML and display
        html = fig.to_html(include_plotlyjs='cdn')
        self.chart_view.setHtml(html)