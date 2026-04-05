"""
Example integration: Setup Panel

Shows how to collect target weight and deadline from user.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit, 
    QPushButton, QDateEdit
)
from PyQt6.QtCore import QDate
from datetime import date
from ui.state_manager import AppStateManager


class SetupPanelExample(QWidget):
    """Example setup panel for target configuration."""
    
    def __init__(self, state_manager: AppStateManager):
        super().__init__()
        self.state = state_manager
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Current weight (inferred, read-only)
        layout.addWidget(QLabel("Current Weight (from your data):"))
        self.current_weight_label = QLabel("--")
        self.current_weight_label.setStyleSheet("font-size: 18pt; font-weight: bold;")
        layout.addWidget(self.current_weight_label)
        
        layout.addSpacing(20)
        
        # Target weight input
        layout.addWidget(QLabel("Target Weight (kg):"))
        self.target_input = QLineEdit()
        self.target_input.setPlaceholderText("70.0")
        layout.addWidget(self.target_input)
        
        layout.addSpacing(20)
        
        # Deadline input
        layout.addWidget(QLabel("Competition Date:"))
        self.deadline_input = QDateEdit()
        self.deadline_input.setCalendarPopup(True)
        self.deadline_input.setDate(QDate.currentDate().addDays(60))
        layout.addWidget(self.deadline_input)
        
        layout.addSpacing(20)
        
        # Summary (auto-calculated)
        self.summary_label = QLabel()
        layout.addWidget(self.summary_label)
        
        layout.addSpacing(20)
        
        # Continue button
        self.continue_btn = QPushButton("Continue to Forecast →")
        self.continue_btn.clicked.connect(self.on_continue)
        layout.addWidget(self.continue_btn)
        
        # Connect input changes to update summary
        self.target_input.textChanged.connect(self.update_summary)
        self.deadline_input.dateChanged.connect(self.update_summary)
        
        self.setLayout(layout)
    
    def showEvent(self, event):
        """Update UI when panel becomes visible."""
        super().showEvent(event)
        
        # Display current weight from state
        if self.state.current_weight:
            self.current_weight_label.setText(f"{self.state.current_weight} kg")
            
            # Pre-fill target if not set (5kg below current)
            if not self.target_input.text():
                suggested_target = self.state.current_weight - 5.0
                self.target_input.setText(f"{suggested_target:.1f}")
        
        self.update_summary()
    
    def update_summary(self):
        """Calculate and display summary stats."""
        try:
            current = self.state.current_weight
            target = float(self.target_input.text())
            deadline = self.deadline_input.date().toPyDate()
            
            # Calculate stats
            last_date = self.state.df_clean.index[-1].date()
            days_available = (deadline - last_date).days
            required_loss = current - target
            weekly_rate = (required_loss / days_available * 7) if days_available > 0 else 0
            
            # Display
            summary = f"""
            Required Loss: {required_loss:.1f} kg
            Days Available: {days_available} days
            Target Rate: {weekly_rate:.2f} kg/week
            """
            
            self.summary_label.setText(summary)
            
            # Enable/disable continue based on validity
            is_valid = (
                target > 0
                and days_available > 0
                and required_loss > 0
            )
            self.continue_btn.setEnabled(is_valid)
            
        except (ValueError, AttributeError):
            self.summary_label.setText("")
            self.continue_btn.setEnabled(False)
    
    def on_continue(self):
        """Save configuration and proceed to forecast."""
        try:
            target = float(self.target_input.text())
            deadline = self.deadline_input.date().toPyDate()
            
            # Save to state
            self.state.set_target_config(target, deadline)
            
            # Signal main window to switch to forecast panel
            # (In real implementation, emit custom signal here)
            
        except ValueError:
            pass  # Validation prevents this


# Usage in main window:
"""
setup_panel = SetupPanelExample(state)
"""
