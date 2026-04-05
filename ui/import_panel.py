"""
Example integration: Import Panel

This shows how to wire up the file upload panel to the backend.
"""
from PyQt6.QtWidgets import QWidget, QPushButton, QVBoxLayout, QLabel, QFileDialog
from PyQt6.QtCore import Qt, QPropertyAnimation, QPoint
from ui.state_manager import AppStateManager


class ImportPanelExample(QWidget):
    """Example import panel with backend integration."""
    
    def __init__(self, state_manager: AppStateManager):
        super().__init__()
        self.state = state_manager
        
        # Connect signals
        self.state.data_loaded.connect(self.on_data_loaded)
        self.state.data_load_failed.connect(self.on_data_failed)
        
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Upload button
        self.upload_btn = QPushButton("Select data_weight.xlsx")
        self.upload_btn.clicked.connect(self.select_file)
        layout.addWidget(self.upload_btn)
        
        # Stats display (hidden initially)
        self.stats_label = QLabel()
        self.stats_label.hide()
        layout.addWidget(self.stats_label)
        
        # Error pill (hidden initially)
        self.error_pill = QLabel()
        self.error_pill.setStyleSheet("""
            background-color: #EE5A6F;
            color: white;
            padding: 10px;
            border-radius: 15px;
        """)
        self.error_pill.hide()
        layout.addWidget(self.error_pill)
        
        # Continue button (disabled initially)
        self.continue_btn = QPushButton("Continue to Setup →")
        self.continue_btn.setEnabled(False)
        layout.addWidget(self.continue_btn)
        
        self.setLayout(layout)
    
    def select_file(self):
        """Open file dialog and load data."""
        filepath, _ = QFileDialog.getOpenFileName(
            self,
            "Select MacroFactor Data",
            "",
            "Excel Files (*.xlsx)"
        )
        
        if filepath:
            # Hide previous error
            self.error_pill.hide()
            
            # Load data (async via state manager)
            self.state.load_data(filepath)
    
    def on_data_loaded(self, validation):
        """Handle successful data load."""
        # Display stats
        stats = validation.stats
        stats_text = f"""
        ✓ Data Loaded
        
        Date Range: {stats['date_range_start']} to {stats['date_range_end']}
        Total Days: {stats['total_days']}
        Nutrition Logs: {stats['logged_days']}/{stats['total_days']} ({stats['completeness_pct']}% complete)
        Current Weight: {stats['current_weight']} kg
        """
        
        # Add warnings if present
        if validation.warnings:
            stats_text += "\n\nWarnings:\n"
            for warning in validation.warnings:
                stats_text += f"⚠ {warning}\n"
        
        self.stats_label.setText(stats_text)
        self.stats_label.show()
        
        # Enable continue button
        self.continue_btn.setEnabled(True)
    
    def on_data_failed(self, error_message):
        """Handle data load failure."""
        # Shake animation
        self.shake_upload_button()
        
        # Show error pill
        self.error_pill.setText(f"❌ {error_message}")
        self.error_pill.show()
    
    def shake_upload_button(self):
        """Animate button shake on error."""
        animation = QPropertyAnimation(self.upload_btn, b"pos")
        animation.setDuration(500)
        animation.setLoopCount(1)
        
        start_pos = self.upload_btn.pos()
        
        # Shake left-right
        animation.setKeyValueAt(0, start_pos)
        animation.setKeyValueAt(0.1, start_pos + QPoint(-10, 0))
        animation.setKeyValueAt(0.2, start_pos + QPoint(10, 0))
        animation.setKeyValueAt(0.3, start_pos + QPoint(-10, 0))
        animation.setKeyValueAt(0.4, start_pos + QPoint(10, 0))
        animation.setKeyValueAt(0.5, start_pos)
        
        animation.start()


# Usage in main window:
"""
from ui.state_manager import AppStateManager

state = AppStateManager()
import_panel = ImportPanelExample(state)
"""
