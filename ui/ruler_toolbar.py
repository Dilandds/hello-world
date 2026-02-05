"""
Secondary toolbar for ruler/measurement mode with orthographic view presets.
"""
import logging
from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QPushButton, QFrame
)
from PyQt5.QtCore import Qt, pyqtSignal, QEvent
from PyQt5.QtGui import QFont
from ui.styles import default_theme

logger = logging.getLogger(__name__)


class RulerViewButton(QPushButton):
    """Styled button for ruler view selection."""
    
    def __init__(self, text, tooltip="", parent=None):
        super().__init__(text, parent)
        self._is_active = False
        self.setToolTip(tooltip)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(26)
        self.setMinimumWidth(60)
        self._apply_default_style()
        self.installEventFilter(self)
    
    def _apply_default_style(self):
        """Apply default button style."""
        if self._is_active:
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: {default_theme.button_primary};
                    color: {default_theme.text_white};
                    border: none;
                    border-radius: 6px;
                    padding: 4px 12px;
                    font-size: 11px;
                    font-weight: 500;
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: {default_theme.row_bg_standard};
                    color: {default_theme.text_primary};
                    border: 1px solid transparent;
                    border-radius: 6px;
                    padding: 4px 12px;
                    font-size: 11px;
                }}
            """)
    
    def _apply_hover_style(self):
        """Apply hover style."""
        if not self._is_active:
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: {default_theme.row_bg_hover};
                    color: {default_theme.text_primary};
                    border: 1px solid {default_theme.border_light};
                    border-radius: 6px;
                    padding: 4px 12px;
                    font-size: 11px;
                }}
            """)
    
    def set_active(self, active):
        """Set the active state of the button."""
        self._is_active = active
        self._apply_default_style()
    
    def eventFilter(self, obj, event):
        """Handle hover events."""
        if obj == self:
            if event.type() == QEvent.Enter:
                self._apply_hover_style()
            elif event.type() == QEvent.Leave:
                self._apply_default_style()
        return super().eventFilter(obj, event)


class RulerToolbar(QWidget):
    """
    Secondary toolbar displayed when ruler/measurement mode is active.
    Provides orthographic view presets for accurate measurement.
    """
    
    # Signals for view selection
    view_front = pyqtSignal()
    view_side = pyqtSignal()
    view_top = pyqtSignal()
    view_bottom = pyqtSignal()
    view_rear = pyqtSignal()
    clear_measurements = pyqtSignal()
    exit_ruler = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_view = "front"
        self.init_ui()
    
    def init_ui(self):
        """Initialize the ruler toolbar UI."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 6, 10, 6)
        layout.setSpacing(8)
        
        # Container frame for styling
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {default_theme.row_bg_highlight};
                border-bottom: 1px solid {default_theme.border_highlight};
            }}
        """)
        
        # Mode indicator
        mode_label = QLabel("📐 Measure Mode")
        mode_label.setStyleSheet(f"""
            color: {default_theme.text_primary};
            font-size: 11px;
            font-weight: bold;
            background: transparent;
        """)
        layout.addWidget(mode_label)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.VLine)
        separator.setFrameShadow(QFrame.Plain)
        separator.setStyleSheet(f"color: {default_theme.border_highlight};")
        separator.setFixedWidth(1)
        layout.addWidget(separator)
        
        # Instruction label
        instruction_label = QLabel("Click two points to measure")
        instruction_label.setStyleSheet(f"""
            color: {default_theme.text_secondary};
            font-size: 10px;
            background: transparent;
        """)
        layout.addWidget(instruction_label)
        
        # Spacer
        layout.addStretch()
        
        # View buttons
        view_label = QLabel("View:")
        view_label.setStyleSheet(f"""
            color: {default_theme.text_secondary};
            font-size: 10px;
            background: transparent;
        """)
        layout.addWidget(view_label)
        
        self.front_btn = RulerViewButton("Front")
        self.front_btn.set_active(True)  # Default view
        self.front_btn.clicked.connect(self._on_front_clicked)
        layout.addWidget(self.front_btn)
        
        self.side_btn = RulerViewButton("Side")
        self.side_btn.clicked.connect(self._on_side_clicked)
        layout.addWidget(self.side_btn)
        
        self.top_btn = RulerViewButton("Top")
        self.top_btn.clicked.connect(self._on_top_clicked)
        layout.addWidget(self.top_btn)
        
        self.bottom_btn = RulerViewButton("Bottom")
        self.bottom_btn.clicked.connect(self._on_bottom_clicked)
        layout.addWidget(self.bottom_btn)
        
        self.rear_btn = RulerViewButton("Rear")
        self.rear_btn.clicked.connect(self._on_rear_clicked)
        layout.addWidget(self.rear_btn)
        
        # Separator
        separator2 = QFrame()
        separator2.setFrameShape(QFrame.VLine)
        separator2.setFrameShadow(QFrame.Plain)
        separator2.setStyleSheet(f"color: {default_theme.border_light};")
        separator2.setFixedWidth(1)
        layout.addWidget(separator2)
        
        # Clear button
        self.clear_btn = RulerViewButton("Clear")
        self.clear_btn.clicked.connect(self._on_clear_clicked)
        layout.addWidget(self.clear_btn)
        
        # Exit button
        self.exit_btn = QPushButton("✕ Exit")
        self.exit_btn.setCursor(Qt.PointingHandCursor)
        self.exit_btn.setFixedHeight(26)
        self.exit_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {default_theme.button_default_bg};
                color: {default_theme.text_primary};
                border: 1px solid {default_theme.border_light};
                border-radius: 6px;
                padding: 4px 12px;
                font-size: 11px;
            }}
            QPushButton:hover {{
                background-color: {default_theme.row_bg_hover};
                border: 1px solid {default_theme.border_medium};
            }}
        """)
        self.exit_btn.clicked.connect(self._on_exit_clicked)
        layout.addWidget(self.exit_btn)
        
        self.setFixedHeight(38)
    
    def _update_view_buttons(self, active_view):
        """Update view button active states."""
        self._current_view = active_view
        self.front_btn.set_active(active_view == "front")
        self.side_btn.set_active(active_view == "side")
        self.top_btn.set_active(active_view == "top")
        self.bottom_btn.set_active(active_view == "bottom")
        self.rear_btn.set_active(active_view == "rear")
    
    def _on_front_clicked(self):
        """Handle front view button click."""
        self._update_view_buttons("front")
        self.view_front.emit()
    
    def _on_side_clicked(self):
        """Handle side view button click."""
        self._update_view_buttons("side")
        self.view_side.emit()
    
    def _on_top_clicked(self):
        """Handle top view button click."""
        self._update_view_buttons("top")
        self.view_top.emit()
    
    def _on_bottom_clicked(self):
        """Handle bottom view button click."""
        self._update_view_buttons("bottom")
        self.view_bottom.emit()
    
    def _on_rear_clicked(self):
        """Handle rear view button click."""
        self._update_view_buttons("rear")
        self.view_rear.emit()
    
    def _on_clear_clicked(self):
        """Handle clear measurements button click."""
        self.clear_measurements.emit()
    
    def _on_exit_clicked(self):
        """Handle exit ruler mode button click."""
        self.exit_ruler.emit()
    
    def reset_to_front(self):
        """Reset view selection to front (called when entering ruler mode)."""
        self._update_view_buttons("front")
