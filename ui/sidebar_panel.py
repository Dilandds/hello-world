"""
Sidebar panel widget for the STL Viewer application.
"""
import logging
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QScrollArea, QFrame, QComboBox, QSizePolicy, QGraphicsDropShadowEffect
)
from PyQt5.QtCore import Qt, QEvent
from PyQt5.QtGui import QFont, QColor
from ui.components import DimensionRow, SurfaceAreaRow, WeightRow, Separator
from ui.styles import get_button_style, default_theme

logger = logging.getLogger(__name__)


class SidebarPanel(QWidget):
    """Left sidebar panel with upload controls and information sections."""
    
    # Material density data (g/cm³)
    MATERIALS = [
        ("24 carat gold (999)", 19.32),
        ("22 carat gold (916)", 17.7),
        ("18K yellow gold 3N", 15.5),
        ("18K rose gold", 15.0),
        ("18K white gold (Pd)", 15.0),
        ("18K white gold (Ag)", 14.7),
        ("14K yellow gold N2", 13.58),
        ("14K rose gold", 13.2),
        ("14K white gold", 13.0),
        ("10K gold", 11.6),
        ("9K gold", 10.8),
        ("Pure platinum (999)", 21.45),
        ("Platinum 950", 20.64),
        ("Platinum 900", 20.0),
        ("Pure palladium (999)", 12.02),
        ("Palladium 950", 11.5),
        ("Pure silver (999)", 10.49),
        ("Sterling Silver 925", 10.36),
        ("Copper Cu", 8.96),
        ("Brass UZ36", 8.5),
        ("Bronze", 8.8),
        ("316L Stainless Steel", 8.0),
        ("Grade 2 Titanium", 4.51),
        ("Aluminium", 2.7),
        ("Standard Resin", 1.2),
        ("Diamond", 3.52),
        ("Sapphire / Ruby", 4.0),
        ("Emerald", 2.75),
        ("Quartz", 2.65),
    ]
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_volume_mm3 = 0.0
        self.init_ui()
    
    def _add_card_shadow(self, card):
        """Add a subtle shadow effect to a card."""
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(12)
        shadow.setXOffset(0)
        shadow.setYOffset(2)
        shadow.setColor(QColor(0, 0, 0, 30))  # Semi-transparent black
        card.setGraphicsEffect(shadow)
    
    def init_ui(self):
        """Initialize the sidebar UI."""
        # Create scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setObjectName("sidebarScrollArea")
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_area.setMinimumWidth(350)
        
        # Style scroll area
        scroll_area.setStyleSheet(f"""
            QScrollArea#sidebarScrollArea {{
                background-color: {default_theme.background};
                border: none;
            }}
            QScrollArea#sidebarScrollArea > QWidget > QWidget {{
                background-color: {default_theme.background};
            }}
        """)
        scroll_area.viewport().setStyleSheet(f"background-color: {default_theme.background};")
        
        # Create content widget
        content_widget = QWidget()
        content_widget.setObjectName("sidebarContent")
        content_widget.setStyleSheet(f"background-color: {default_theme.background};")
        content_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        
        layout = QVBoxLayout(content_widget)
        layout.setAlignment(Qt.AlignTop)
        layout.setSpacing(15)
        layout.setContentsMargins(10, 10, 20, 10)
        
        # Title label
        title_label = QLabel("STL Viewer")
        title_label.setObjectName("titleLabel")
        title_font = QFont("Inter", 16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # Upload button
        self.upload_btn = QPushButton("Upload STL File")
        self.upload_btn.setMinimumHeight(50)
        self.upload_btn.setObjectName("uploadBtn")
        self.upload_btn.setStyleSheet(get_button_style("uploadBtn"))
        layout.addWidget(self.upload_btn)
        
        # Info label
        info_label = QLabel(
            "Click the button above\nto load an STL file\nfor 3D visualization."
        )
        info_label.setObjectName("infoLabel")
        info_label.setAlignment(Qt.AlignCenter)
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # Create sections
        self.dimensions_group = self.create_dimensions_section()
        layout.addWidget(self.dimensions_group)
        
        self.surface_area_group = self.create_surface_area_section()
        layout.addWidget(self.surface_area_group)
        
        self.weight_group = self.create_weight_section()
        layout.addWidget(self.weight_group)
        
        # Add stretch
        layout.addStretch()
        
        # Set content widget to scroll area
        scroll_area.setWidget(content_widget)
        
        # Store scroll area as main widget
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll_area)
    
    def create_dimensions_section(self):
        """Create the dimensions display section."""
        card = QFrame()
        card.setObjectName("dimensionsCard")
        card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(16, 16, 16, 16)
        card_layout.setSpacing(10)
        
        # Card title
        title_label = QLabel("Dimensions")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet(f"color: {default_theme.text_title}; margin-bottom: 4px;")
        card_layout.addWidget(title_label)
        
        # Dimension rows using components
        self.width_row = DimensionRow("Length (X)", "--", self)
        self.height_row = DimensionRow("Width (Y)", "--", self)
        self.depth_row = DimensionRow("Height (Z)", "--", self)
        
        card_layout.addWidget(self.width_row)
        card_layout.addWidget(self.height_row)
        card_layout.addWidget(self.depth_row)
        
        # Separator
        separator = Separator(self)
        card_layout.addWidget(separator)
        
        # Volume row
        self.volume_row = DimensionRow("Volume", "--", self)
        card_layout.addWidget(self.volume_row)
        
        # Add shadow effect
        self._add_card_shadow(card)
        
        return card
    
    def create_surface_area_section(self):
        """Create the surface area section."""
        card = QFrame()
        card.setObjectName("surfaceAreaCard")
        card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(16, 16, 16, 16)
        card_layout.setSpacing(10)
        
        # Header row with title and icon
        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)
        
        title_label = QLabel("Total Surface Area")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet(f"color: {default_theme.text_title}; margin-bottom: 4px;")
        
        icon_label = QLabel("⬇")
        icon_label.setStyleSheet(f"color: {default_theme.icon_blue}; font-size: 16px;")
        icon_label.setAlignment(Qt.AlignCenter)
        
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(icon_label)
        card_layout.addLayout(header_layout)
        
        # Surface area rows using components
        self.surface_total_row = SurfaceAreaRow("Total area", "--", "standard", self)
        self.surface_cm_row = SurfaceAreaRow("Area (cm²)", "--", "highlight", self)
        
        card_layout.addWidget(self.surface_total_row)
        card_layout.addWidget(self.surface_cm_row)
        
        # Information footer
        footer_frame = QFrame()
        footer_frame.setObjectName("surfaceFooter")
        footer_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        footer_frame.setMinimumHeight(40)
        
        footer_layout = QHBoxLayout(footer_frame)
        footer_layout.setContentsMargins(10, 8, 10, 8)
        footer_layout.setSpacing(8)
        
        info_icon = QLabel("ℹ️")
        info_icon.setStyleSheet(f"color: {default_theme.icon_info_gray}; font-size: 12px;")
        info_icon.setFixedWidth(20)
        info_icon.setAlignment(Qt.AlignTop)
        
        disclaimer = QLabel("Calculated surface area: Sum of the areas of all triangles in the 3D mesh. Useful for estimating galvanizing or surface treatment costs.")
        disclaimer_font = QFont()
        disclaimer_font.setPointSize(9)
        disclaimer.setFont(disclaimer_font)
        disclaimer.setStyleSheet(f"color: {default_theme.icon_info_gray};")
        disclaimer.setWordWrap(True)
        
        footer_layout.addWidget(info_icon)
        footer_layout.addWidget(disclaimer)
        footer_layout.addStretch()
        
        card_layout.addWidget(footer_frame)
        
        # Add shadow effect
        self._add_card_shadow(card)
        
        return card
    
    def create_weight_section(self):
        """Create the estimated weight calculator section."""
        card = QFrame()
        card.setObjectName("weightCard")
        card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(16, 16, 16, 16)
        card_layout.setSpacing(10)
        
        # Header row with title and icon
        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)
        
        title_label = QLabel("Estimated Weight")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet(f"color: {default_theme.text_title}; margin-bottom: 4px;")
        
        icon_label = QLabel("⚖")
        icon_label.setStyleSheet(f"color: {default_theme.icon_blue}; font-size: 16px;")
        icon_label.setAlignment(Qt.AlignCenter)
        
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(icon_label)
        card_layout.addLayout(header_layout)
        
        # Material selector dropdown
        self.material_combo = QComboBox()
        self.material_combo.setObjectName("materialCombo")
        self.material_combo.setMinimumHeight(40)
        for material_name, density in self.MATERIALS:
            self.material_combo.addItem(f"{material_name} ({density} g/cm³)", density)
        self.material_combo.currentIndexChanged.connect(self.on_material_changed)
        card_layout.addWidget(self.material_combo)
        
        # Weight rows using components
        self.weight_volume_row = WeightRow("Volume", "--", "standard", self)
        self.weight_density_row = WeightRow("Density", "--", "standard", self)
        self.weight_result_row = WeightRow("Estimated weight", "--", "highlight", self)
        
        card_layout.addWidget(self.weight_volume_row)
        card_layout.addWidget(self.weight_density_row)
        card_layout.addWidget(self.weight_result_row)
        
        # Information footer
        footer_frame = QFrame()
        footer_frame.setObjectName("weightFooter")
        footer_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        footer_frame.setMinimumHeight(40)
        
        footer_layout = QHBoxLayout(footer_frame)
        footer_layout.setContentsMargins(10, 8, 10, 8)
        footer_layout.setSpacing(8)
        
        info_icon = QLabel("ℹ️")
        info_icon.setStyleSheet(f"color: {default_theme.icon_warning}; font-size: 12px;")
        info_icon.setFixedWidth(20)
        info_icon.setAlignment(Qt.AlignTop)
        
        disclaimer = QLabel("Actual Volume Calculated: Weight is estimated by multiplying volume (mm³ → cm³) by material density. Results may vary based on mesh accuracy and material purity.")
        disclaimer_font = QFont()
        disclaimer_font.setPointSize(9)
        disclaimer.setFont(disclaimer_font)
        disclaimer.setStyleSheet(f"color: {default_theme.icon_warning};")
        disclaimer.setWordWrap(True)
        
        footer_layout.addWidget(info_icon)
        footer_layout.addWidget(disclaimer)
        
        card_layout.addWidget(footer_frame)
        
        # Add shadow effect
        self._add_card_shadow(card)
        
        return card
    
    def eventFilter(self, obj, event):
        """Handle hover events for rows."""
        # Rows handle their own events, but we need to ensure they're installed
        # The event filter is already installed on each row in create_*_section methods
        return super().eventFilter(obj, event)
    
    def on_material_changed(self, index):
        """Handle material selection change."""
        if index < 0 or index >= len(self.MATERIALS):
            return
        
        material_name, density = self.MATERIALS[index]
        self.weight_density_row.set_value(f"{density} g/cm³")
        self.calculate_weight()
    
    def calculate_weight(self, volume_mm3=None, density_g_per_cm3=None):
        """Calculate and update the estimated weight."""
        from core.mesh_calculator import MeshCalculator
        
        if volume_mm3 is None:
            volume_mm3 = self.current_volume_mm3
        
        if density_g_per_cm3 is None:
            index = self.material_combo.currentIndex()
            if index < 0 or index >= len(self.MATERIALS):
                return
            _, density_g_per_cm3 = self.MATERIALS[index]
        
        result = MeshCalculator.estimate_weight(volume_mm3, density_g_per_cm3)
        self.weight_result_row.set_value(result['display'])
    
    def update_dimensions(self, mesh_data):
        """Update all dimension displays with mesh data."""
        from core.mesh_calculator import MeshCalculator
        
        if mesh_data is None:
            self.width_row.set_value("--")
            self.height_row.set_value("--")
            self.depth_row.set_value("--")
            self.volume_row.set_value("--")
            self.surface_total_row.set_value("--")
            self.surface_cm_row.set_value("--")
            self.weight_volume_row.set_value("--")
            self.current_volume_mm3 = 0.0
            self.calculate_weight()
            return
        
        # Update dimensions
        self.width_row.set_value(f"{mesh_data['width']:.2f} mm")
        self.height_row.set_value(f"{mesh_data['height']:.2f} mm")
        self.depth_row.set_value(f"{mesh_data['depth']:.2f} mm")
        self.volume_row.set_value(f"{mesh_data['volume_mm3']:.2f} mm³")
        
        # Update surface area
        self.surface_total_row.set_value(f"{mesh_data['surface_area_mm2']:.2f} mm²")
        self.surface_cm_row.set_value(f"{mesh_data['surface_area_cm2']:.2f} cm²")
        
        # Update weight calculator
        self.current_volume_mm3 = mesh_data['volume_mm3']
        self.weight_volume_row.set_value(f"{mesh_data['volume_cm3']:.4f} cm³")
        
        # Update density display
        index = self.material_combo.currentIndex()
        if index >= 0 and index < len(self.MATERIALS):
            _, density = self.MATERIALS[index]
            self.weight_density_row.set_value(f"{density} g/cm³")
        
        # Calculate weight
        self.calculate_weight()
