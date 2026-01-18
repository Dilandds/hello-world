"""
Reusable UI components for the STL Viewer application.
"""
from PyQt5.QtWidgets import (
    QFrame, QLabel, QHBoxLayout, QVBoxLayout,
    QSpacerItem, QSizePolicy
)
from PyQt5.QtCore import Qt, QEvent
from PyQt5.QtGui import QFont
from ui.styles import default_theme


class DimensionRow(QFrame):
    """A reusable dimension row component with hover effect."""
    
    def __init__(self, label_text, value_text="--", parent=None):
        super().__init__(parent)
        self.setObjectName("dimensionRow")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setFixedHeight(44)
        self.setStyleSheet(f"""
            QFrame#dimensionRow {{
                background-color: {default_theme.row_bg_standard};
                border-radius: 8px;
                border: none;
            }}
        """)
        
        row_layout = QHBoxLayout(self)
        row_layout.setContentsMargins(14, 8, 14, 8)
        row_layout.setSpacing(0)
        
        # Label
        label = QLabel(label_text)
        label.setObjectName("dimensionLabel")
        label.setStyleSheet(f"background-color: transparent; color: {default_theme.text_secondary};")
        label_font = QFont()
        label_font.setPointSize(11)
        label.setFont(label_font)
        
        # Spacer
        spacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        
        # Value
        self.value_label = QLabel(value_text)
        self.value_label.setObjectName("dimensionValue")
        self.value_label.setStyleSheet(f"background-color: transparent; color: {default_theme.text_primary};")
        value_font = QFont()
        value_font.setPointSize(13)
        value_font.setBold(True)
        self.value_label.setFont(value_font)
        self.value_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        
        row_layout.addWidget(label)
        row_layout.addItem(spacer)
        row_layout.addWidget(self.value_label)
        
        # Install event filter for hover effect
        self.installEventFilter(self)
    
    def eventFilter(self, obj, event):
        """Handle hover events."""
        if obj == self:
            if event.type() == QEvent.Enter:
                self.setStyleSheet(f"""
                    QFrame#dimensionRow {{
                        background-color: {default_theme.row_bg_hover};
                        border-radius: 8px;
                    }}
                """)
            elif event.type() == QEvent.Leave:
                self.setStyleSheet(f"""
                    QFrame#dimensionRow {{
                        background-color: {default_theme.row_bg_standard};
                        border-radius: 8px;
                    }}
                """)
        return super().eventFilter(obj, event)
    
    def set_value(self, text):
        """Update the value label text."""
        self.value_label.setText(text)


class SurfaceAreaRow(QFrame):
    """A reusable surface area row component with hover effect."""
    
    def __init__(self, label_text, value_text="--", row_type="standard", parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setFixedHeight(44)
        
        if row_type == "standard":
            self.setObjectName("surfaceRowStandard")
            self.setStyleSheet(f"""
                QFrame#surfaceRowStandard {{
                    background-color: {default_theme.row_bg_standard};
                    border-radius: 8px;
                    border: none;
                }}
            """)
        elif row_type == "highlight":
            self.setObjectName("surfaceRowHighlight")
            self.setStyleSheet(f"""
                QFrame#surfaceRowHighlight {{
                    background-color: {default_theme.row_bg_highlight};
                    border-left: 4px solid {default_theme.border_highlight};
                    border-top: none;
                    border-right: none;
                    border-bottom: none;
                    border-radius: 8px;
                }}
            """)
        else:
            self.setObjectName("surfaceRowStandard")
            self.setStyleSheet(f"""
                QFrame#surfaceRowStandard {{
                    background-color: {default_theme.row_bg_standard};
                    border-radius: 8px;
                    border: none;
                }}
            """)
        
        row_layout = QHBoxLayout(self)
        row_layout.setContentsMargins(14, 8, 14, 8)
        row_layout.setSpacing(0)
        
        # Label
        label = QLabel(label_text)
        label.setObjectName("surfaceLabel")
        label.setStyleSheet(f"background-color: transparent; color: {default_theme.text_secondary};")
        label_font = QFont()
        label_font.setPointSize(11)
        label.setFont(label_font)
        
        # Spacer
        spacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        
        # Value
        self.value_label = QLabel(value_text)
        self.value_label.setObjectName("surfaceValue")
        self.value_label.setStyleSheet(f"background-color: transparent; color: {default_theme.text_primary};")
        value_font = QFont()
        value_font.setPointSize(13)
        value_font.setBold(True)
        self.value_label.setFont(value_font)
        self.value_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        
        row_layout.addWidget(label)
        row_layout.addItem(spacer)
        row_layout.addWidget(self.value_label)
        
        # Install event filter for hover effect
        self.installEventFilter(self)
    
    def eventFilter(self, obj, event):
        """Handle hover events."""
        if obj == self:
            obj_name = self.objectName()
            if obj_name == "surfaceRowStandard":
                if event.type() == QEvent.Enter:
                    self.setStyleSheet(f"""
                        QFrame#surfaceRowStandard {{
                            background-color: {default_theme.row_bg_hover};
                            border-radius: 8px;
                        }}
                    """)
                elif event.type() == QEvent.Leave:
                    self.setStyleSheet(f"""
                        QFrame#surfaceRowStandard {{
                            background-color: {default_theme.row_bg_standard};
                            border-radius: 8px;
                        }}
                    """)
            elif obj_name == "surfaceRowHighlight":
                if event.type() == QEvent.Enter:
                    self.setStyleSheet(f"""
                        QFrame#surfaceRowHighlight {{
                            background-color: {default_theme.row_bg_highlight_hover};
                            border-left: 4px solid {default_theme.border_highlight};
                            border-top: none;
                            border-right: none;
                            border-bottom: none;
                            border-radius: 8px;
                        }}
                    """)
                elif event.type() == QEvent.Leave:
                    self.setStyleSheet(f"""
                        QFrame#surfaceRowHighlight {{
                            background-color: {default_theme.row_bg_highlight};
                            border-left: 4px solid {default_theme.border_highlight};
                            border-top: none;
                            border-right: none;
                            border-bottom: none;
                            border-radius: 8px;
                        }}
                    """)
        return super().eventFilter(obj, event)
    
    def set_value(self, text):
        """Update the value label text."""
        self.value_label.setText(text)


class WeightRow(QFrame):
    """A reusable weight row component with hover effect."""
    
    def __init__(self, label_text, value_text="--", row_type="standard", parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setFixedHeight(44)
        
        if row_type == "standard":
            self.setObjectName("weightRowStandard")
            self.setStyleSheet(f"""
                QFrame#weightRowStandard {{
                    background-color: {default_theme.row_bg_standard};
                    border-radius: 8px;
                    border: none;
                }}
            """)
        elif row_type == "highlight":
            self.setObjectName("weightRowHighlight")
            self.setStyleSheet(f"""
                QFrame#weightRowHighlight {{
                    background-color: {default_theme.row_bg_highlight};
                    border: 1px solid {default_theme.border_highlight};
                    border-radius: 8px;
                }}
            """)
        else:
            self.setObjectName("weightRowStandard")
            self.setStyleSheet(f"""
                QFrame#weightRowStandard {{
                    background-color: {default_theme.row_bg_standard};
                    border-radius: 8px;
                    border: none;
                }}
            """)
        
        row_layout = QHBoxLayout(self)
        row_layout.setContentsMargins(14, 8, 14, 8)
        row_layout.setSpacing(0)
        
        # Label
        label = QLabel(label_text)
        label.setObjectName("weightLabel")
        label.setStyleSheet(f"background-color: transparent; color: {default_theme.text_secondary};")
        label_font = QFont()
        label_font.setPointSize(11)
        label.setFont(label_font)
        
        # Spacer
        spacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        
        # Value
        self.value_label = QLabel(value_text)
        self.value_label.setObjectName("weightValue")
        self.value_label.setStyleSheet(f"background-color: transparent; color: {default_theme.text_primary};")
        value_font = QFont()
        value_font.setPointSize(13)
        value_font.setBold(True)
        self.value_label.setFont(value_font)
        self.value_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        
        row_layout.addWidget(label)
        row_layout.addItem(spacer)
        row_layout.addWidget(self.value_label)
        
        # Install event filter for hover effect
        self.installEventFilter(self)
    
    def eventFilter(self, obj, event):
        """Handle hover events."""
        if obj == self:
            obj_name = self.objectName()
            if obj_name == "weightRowStandard":
                if event.type() == QEvent.Enter:
                    self.setStyleSheet(f"""
                        QFrame#weightRowStandard {{
                            background-color: {default_theme.row_bg_hover};
                            border-radius: 8px;
                        }}
                    """)
                elif event.type() == QEvent.Leave:
                    self.setStyleSheet(f"""
                        QFrame#weightRowStandard {{
                            background-color: {default_theme.row_bg_standard};
                            border-radius: 8px;
                        }}
                    """)
            elif obj_name == "weightRowHighlight":
                if event.type() == QEvent.Enter:
                    self.setStyleSheet(f"""
                        QFrame#weightRowHighlight {{
                            background-color: {default_theme.row_bg_highlight_hover};
                            border: 1px solid {default_theme.border_highlight};
                            border-radius: 8px;
                        }}
                    """)
                elif event.type() == QEvent.Leave:
                    self.setStyleSheet(f"""
                        QFrame#weightRowHighlight {{
                            background-color: {default_theme.row_bg_highlight};
                            border: 1px solid {default_theme.border_highlight};
                            border-radius: 8px;
                        }}
                    """)
        return super().eventFilter(obj, event)
    
    def set_value(self, text):
        """Update the value label text."""
        self.value_label.setText(text)


class InfoCard(QFrame):
    """Base card component for info sections."""
    
    def __init__(self, title, object_name, parent=None):
        super().__init__(parent)
        self.setObjectName(object_name)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        
        self.card_layout = QVBoxLayout(self)
        self.card_layout.setContentsMargins(16, 16, 16, 16)
        self.card_layout.setSpacing(10)
        
        # Card title
        title_label = QLabel(title)
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet(f"color: {default_theme.text_title}; margin-bottom: 4px;")
        self.card_layout.addWidget(title_label)
    
    def add_separator(self):
        """Add a subtle separator line."""
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setStyleSheet(f"background-color: {default_theme.separator}; max-height: 1px; margin: 6px 0;")
        self.card_layout.addWidget(separator)


class Separator(QFrame):
    """Horizontal separator component."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.HLine)
        self.setStyleSheet(f"background-color: {default_theme.separator}; max-height: 1px; margin: 6px 0;")
