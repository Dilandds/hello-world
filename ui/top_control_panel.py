"""
Hover-activated top control panel for the STL 3D Viewer.
"""
from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QPushButton, 
    QFrame, QComboBox, QSizePolicy, QSpacerItem,
    QGraphicsDropShadowEffect
)
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve, pyqtSignal, QEvent
from PyQt5.QtGui import QFont, QColor
from ui.styles import default_theme


class PillButton(QPushButton):
    """Pill-shaped button with hover effect."""
    
    def __init__(self, text="", icon_text="", is_active=False, is_primary=False, parent=None):
        super().__init__(parent)
        self.is_active = is_active
        self.is_primary = is_primary
        
        if icon_text and text:
            self.setText(f"{icon_text}  {text}")
        elif icon_text:
            self.setText(icon_text)
        else:
            self.setText(text)
        
        self.setFixedHeight(32)
        self.setCursor(Qt.PointingHandCursor)
        self._update_style()
        self.installEventFilter(self)
    
    def _update_style(self):
        """Update button style based on state."""
        if self.is_primary:
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: #F97316;
                    color: white;
                    border: none;
                    border-radius: 16px;
                    padding: 6px 16px;
                    font-size: 12px;
                    font-weight: 600;
                }}
                QPushButton:hover {{
                    background-color: #EA580C;
                }}
                QPushButton:pressed {{
                    background-color: #C2410C;
                }}
            """)
        elif self.is_active:
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: #14B8A6;
                    color: white;
                    border: none;
                    border-radius: 16px;
                    padding: 6px 14px;
                    font-size: 12px;
                    font-weight: 500;
                }}
                QPushButton:hover {{
                    background-color: #0D9488;
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: #374151;
                    color: #E5E7EB;
                    border: none;
                    border-radius: 16px;
                    padding: 6px 14px;
                    font-size: 12px;
                    font-weight: 500;
                }}
                QPushButton:hover {{
                    background-color: #4B5563;
                }}
                QPushButton:pressed {{
                    background-color: #1F2937;
                }}
            """)
    
    def set_active(self, active):
        """Set button active state."""
        self.is_active = active
        self._update_style()
    
    def eventFilter(self, obj, event):
        """Handle events for visual feedback."""
        return super().eventFilter(obj, event)


class IconButton(QPushButton):
    """Icon-only button for quick actions."""
    
    def __init__(self, icon_text, tooltip="", is_accent=False, parent=None):
        super().__init__(icon_text, parent)
        self.is_accent = is_accent
        self.setFixedSize(32, 32)
        self.setToolTip(tooltip)
        self.setCursor(Qt.PointingHandCursor)
        self._update_style()
    
    def _update_style(self):
        """Update button style."""
        if self.is_accent:
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: #7C3AED;
                    color: white;
                    border: none;
                    border-radius: 16px;
                    font-size: 14px;
                }}
                QPushButton:hover {{
                    background-color: #6D28D9;
                }}
                QPushButton:pressed {{
                    background-color: #5B21B6;
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: #374151;
                    color: #E5E7EB;
                    border: none;
                    border-radius: 16px;
                    font-size: 14px;
                }}
                QPushButton:hover {{
                    background-color: #4B5563;
                }}
                QPushButton:pressed {{
                    background-color: #1F2937;
                }}
            """)


class TopControlPanel(QWidget):
    """Hover-activated floating control panel."""
    
    # Signals for actions
    grid_toggled = pyqtSignal(bool)
    wireframe_toggled = pyqtSignal(bool)
    fullscreen_requested = pyqtSignal()
    new_file_requested = pyqtSignal()
    view_face_requested = pyqtSignal()
    view_side_requested = pyqtSignal()
    view_above_requested = pyqtSignal()
    rotation_toggled = pyqtSignal(bool)
    theme_changed = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_filename = ""
        self.is_visible = False
        self.grid_active = False
        self.wireframe_active = False
        self.rotation_active = False
        
        self.setFixedHeight(52)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMouseTracking(True)
        
        self._setup_ui()
        self._setup_animation()
        
        # Start hidden
        self.setWindowOpacity(0)
        self.hide()
    
    def _setup_ui(self):
        """Set up the control panel UI."""
        # Main container with frosted glass effect
        self.container = QFrame(self)
        self.container.setStyleSheet("""
            QFrame {
                background-color: rgba(31, 41, 55, 0.95);
                border-radius: 26px;
                border: 1px solid rgba(75, 85, 99, 0.5);
            }
        """)
        
        # Add drop shadow
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setXOffset(0)
        shadow.setYOffset(4)
        shadow.setColor(QColor(0, 0, 0, 60))
        self.container.setGraphicsEffect(shadow)
        
        container_layout = QHBoxLayout(self.container)
        container_layout.setContentsMargins(16, 8, 16, 8)
        container_layout.setSpacing(12)
        
        # File label
        self.file_label = QLabel("File: No file loaded")
        self.file_label.setStyleSheet("""
            QLabel {
                color: #9CA3AF;
                font-size: 12px;
                font-weight: 500;
                background: transparent;
            }
        """)
        container_layout.addWidget(self.file_label)
        
        # Separator
        sep1 = QFrame()
        sep1.setFixedSize(1, 24)
        sep1.setStyleSheet("background-color: rgba(75, 85, 99, 0.6);")
        container_layout.addWidget(sep1)
        
        # Grid toggle
        self.grid_btn = PillButton("Grid", "⊞", is_active=self.grid_active)
        self.grid_btn.clicked.connect(self._toggle_grid)
        container_layout.addWidget(self.grid_btn)
        
        # Theme dropdown
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Dark", "Light", "Blue"])
        self.theme_combo.setFixedHeight(32)
        self.theme_combo.setStyleSheet("""
            QComboBox {
                background-color: #374151;
                color: #E5E7EB;
                border: none;
                border-radius: 16px;
                padding: 6px 12px;
                padding-right: 24px;
                font-size: 12px;
                font-weight: 500;
                min-width: 70px;
            }
            QComboBox:hover {
                background-color: #4B5563;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 5px solid #9CA3AF;
                margin-right: 8px;
            }
            QComboBox QAbstractItemView {
                background-color: #374151;
                color: #E5E7EB;
                border: 1px solid #4B5563;
                border-radius: 8px;
                selection-background-color: #4B5563;
                padding: 4px;
            }
        """)
        self.theme_combo.currentTextChanged.connect(lambda t: self.theme_changed.emit(t))
        container_layout.addWidget(self.theme_combo)
        
        # Separator
        sep2 = QFrame()
        sep2.setFixedSize(1, 24)
        sep2.setStyleSheet("background-color: rgba(75, 85, 99, 0.6);")
        container_layout.addWidget(sep2)
        
        # Rotation button
        self.rotation_btn = IconButton("↻", "Toggle rotation")
        self.rotation_btn.clicked.connect(self._toggle_rotation)
        container_layout.addWidget(self.rotation_btn)
        
        # Wireframe button
        self.wireframe_btn = IconButton("◇", "Toggle wireframe")
        self.wireframe_btn.clicked.connect(self._toggle_wireframe)
        container_layout.addWidget(self.wireframe_btn)
        
        # Fullscreen button
        self.fullscreen_btn = IconButton("⛶", "Fullscreen", is_accent=True)
        self.fullscreen_btn.clicked.connect(lambda: self.fullscreen_requested.emit())
        container_layout.addWidget(self.fullscreen_btn)
        
        # Separator
        sep3 = QFrame()
        sep3.setFixedSize(1, 24)
        sep3.setStyleSheet("background-color: rgba(75, 85, 99, 0.6);")
        container_layout.addWidget(sep3)
        
        # View orientation buttons
        self.face_btn = IconButton("◉", "Front view")
        self.face_btn.clicked.connect(lambda: self.view_face_requested.emit())
        container_layout.addWidget(self.face_btn)
        
        self.side_btn = IconButton("◧", "Side view")
        self.side_btn.clicked.connect(lambda: self.view_side_requested.emit())
        container_layout.addWidget(self.side_btn)
        
        self.above_btn = IconButton("◎", "Top view")
        self.above_btn.clicked.connect(lambda: self.view_above_requested.emit())
        container_layout.addWidget(self.above_btn)
        
        # Spacer
        container_layout.addStretch()
        
        # New file button
        self.new_file_btn = PillButton("New file", "📁", is_primary=True)
        self.new_file_btn.clicked.connect(lambda: self.new_file_requested.emit())
        container_layout.addWidget(self.new_file_btn)
        
        # Main layout
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(20, 0, 20, 0)
        main_layout.addWidget(self.container)
    
    def _setup_animation(self):
        """Set up fade animation."""
        self.fade_animation = QPropertyAnimation(self, b"windowOpacity")
        self.fade_animation.setDuration(200)
        self.fade_animation.setEasingCurve(QEasingCurve.OutCubic)
    
    def show_panel(self):
        """Show the control panel with animation."""
        if not self.is_visible:
            self.is_visible = True
            self.show()
            self.fade_animation.stop()
            self.fade_animation.setStartValue(self.windowOpacity())
            self.fade_animation.setEndValue(1.0)
            self.fade_animation.start()
    
    def hide_panel(self):
        """Hide the control panel with animation."""
        if self.is_visible:
            self.is_visible = False
            self.fade_animation.stop()
            self.fade_animation.setStartValue(self.windowOpacity())
            self.fade_animation.setEndValue(0.0)
            self.fade_animation.finished.connect(self._on_hide_complete)
            self.fade_animation.start()
    
    def _on_hide_complete(self):
        """Handle hide animation completion."""
        if not self.is_visible:
            self.hide()
        try:
            self.fade_animation.finished.disconnect(self._on_hide_complete)
        except:
            pass
    
    def set_filename(self, filename):
        """Update the displayed filename."""
        self.current_filename = filename
        if filename:
            # Truncate long filenames
            display_name = filename if len(filename) <= 25 else f"...{filename[-22:]}"
            self.file_label.setText(f"File: {display_name}")
            self.file_label.setStyleSheet("""
                QLabel {
                    color: #E5E7EB;
                    font-size: 12px;
                    font-weight: 500;
                    background: transparent;
                }
            """)
        else:
            self.file_label.setText("File: No file loaded")
            self.file_label.setStyleSheet("""
                QLabel {
                    color: #9CA3AF;
                    font-size: 12px;
                    font-weight: 500;
                    background: transparent;
                }
            """)
    
    def _toggle_grid(self):
        """Toggle grid visibility."""
        self.grid_active = not self.grid_active
        self.grid_btn.set_active(self.grid_active)
        self.grid_toggled.emit(self.grid_active)
    
    def _toggle_wireframe(self):
        """Toggle wireframe mode."""
        self.wireframe_active = not self.wireframe_active
        if self.wireframe_active:
            self.wireframe_btn.setStyleSheet("""
                QPushButton {
                    background-color: #14B8A6;
                    color: white;
                    border: none;
                    border-radius: 16px;
                    font-size: 14px;
                }
                QPushButton:hover {
                    background-color: #0D9488;
                }
            """)
        else:
            self.wireframe_btn._update_style()
        self.wireframe_toggled.emit(self.wireframe_active)
    
    def _toggle_rotation(self):
        """Toggle auto-rotation."""
        self.rotation_active = not self.rotation_active
        if self.rotation_active:
            self.rotation_btn.setStyleSheet("""
                QPushButton {
                    background-color: #14B8A6;
                    color: white;
                    border: none;
                    border-radius: 16px;
                    font-size: 14px;
                }
                QPushButton:hover {
                    background-color: #0D9488;
                }
            """)
        else:
            self.rotation_btn._update_style()
        self.rotation_toggled.emit(self.rotation_active)


class HoverTriggerArea(QWidget):
    """Invisible hover trigger area at the top of the viewer."""
    
    hover_entered = pyqtSignal()
    hover_left = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(60)
        self.setMouseTracking(True)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet("background: transparent;")
    
    def enterEvent(self, event):
        """Handle mouse enter."""
        self.hover_entered.emit()
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """Handle mouse leave."""
        self.hover_left.emit()
        super().leaveEvent(event)
