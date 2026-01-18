"""
Sidebar panel widget for the STL Viewer application.
"""
import logging
import os
from datetime import datetime
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QScrollArea, QFrame, QComboBox, QSizePolicy, QGraphicsDropShadowEffect,
    QLineEdit, QFileDialog, QMessageBox
)
from PyQt5.QtCore import Qt, QEvent, pyqtSignal
from PyQt5.QtGui import QFont, QColor, QDoubleValidator
from ui.components import DimensionRow, SurfaceAreaRow, WeightRow, Separator, ScaleResultRow, ReportCheckbox
from ui.styles import get_button_style, default_theme

logger = logging.getLogger(__name__)


class SidebarPanel(QWidget):
    """Left sidebar panel with upload controls and information sections."""
    
    # Signal emitted when export is requested (file_path, scale_factor)
    export_scaled_stl = pyqtSignal(str, float)
    
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
        self.current_weight_grams = 0.0
        self.current_dimensions = {'width': 0.0, 'height': 0.0, 'depth': 0.0}
        self.calculated_scale_factor = 1.0
        self.current_surface_area_cm2 = 0.0
        self.current_stl_filename = ""
        self.has_stl_loaded = False
        self.has_scaled_data = False
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
        
        # Create Adjust to Target Weight section
        self.adjust_weight_group = self.create_adjust_weight_section()
        layout.addWidget(self.adjust_weight_group)
        
        # Create PDF Report section
        self.pdf_report_group = self.create_pdf_report_section()
        layout.addWidget(self.pdf_report_group)
        
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
    
    def create_adjust_weight_section(self):
        """Create the adjust to target weight section."""
        card = QFrame()
        card.setObjectName("adjustWeightCard")
        card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(16, 16, 16, 16)
        card_layout.setSpacing(10)
        
        # Header row with title and icon
        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)
        
        title_label = QLabel("Adjust to Target Weight")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet(f"color: {default_theme.text_title}; margin-bottom: 4px;")
        
        icon_label = QLabel("⚙")
        icon_label.setStyleSheet(f"color: {default_theme.icon_blue}; font-size: 16px;")
        icon_label.setAlignment(Qt.AlignCenter)
        
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(icon_label)
        card_layout.addLayout(header_layout)
        
        # Target weight input
        input_layout = QHBoxLayout()
        input_layout.setSpacing(8)
        
        self.target_weight_input = QLineEdit()
        self.target_weight_input.setObjectName("targetWeightInput")
        self.target_weight_input.setPlaceholderText("Enter target weight")
        self.target_weight_input.setMinimumHeight(40)
        
        # Set validator for numeric input
        validator = QDoubleValidator(0.0, 999999.0, 4)
        validator.setNotation(QDoubleValidator.StandardNotation)
        self.target_weight_input.setValidator(validator)
        self.target_weight_input.returnPressed.connect(self.calculate_scale)
        
        unit_label = QLabel("g")
        unit_label.setStyleSheet(f"color: {default_theme.text_secondary}; font-weight: bold;")
        unit_label.setFixedWidth(20)
        
        input_layout.addWidget(self.target_weight_input)
        input_layout.addWidget(unit_label)
        card_layout.addLayout(input_layout)
        
        # Calculate button
        self.calculate_scale_btn = QPushButton("Calculate Scale")
        self.calculate_scale_btn.setObjectName("calculateScaleBtn")
        self.calculate_scale_btn.setMinimumHeight(40)
        self.calculate_scale_btn.setEnabled(False)
        self.calculate_scale_btn.setStyleSheet(f"""
            QPushButton#calculateScaleBtn {{
                background-color: {default_theme.button_primary};
                color: {default_theme.text_white};
                border: none;
                border-radius: 8px;
                padding: 10px 16px;
                font-size: 13px;
                font-weight: bold;
            }}
            QPushButton#calculateScaleBtn:hover {{
                background-color: {default_theme.button_primary_hover};
            }}
            QPushButton#calculateScaleBtn:pressed {{
                background-color: {default_theme.button_primary_pressed};
            }}
            QPushButton#calculateScaleBtn:disabled {{
                background-color: {default_theme.button_default_bg};
                color: {default_theme.text_primary};
            }}
        """)
        self.calculate_scale_btn.clicked.connect(self.calculate_scale)
        card_layout.addWidget(self.calculate_scale_btn)
        
        # Separator
        separator = Separator(self)
        card_layout.addWidget(separator)
        
        # Results section title
        results_label = QLabel("Scaled Results")
        results_font = QFont()
        results_font.setPointSize(11)
        results_font.setBold(True)
        results_label.setFont(results_font)
        results_label.setStyleSheet(f"color: {default_theme.text_secondary}; margin-top: 4px;")
        card_layout.addWidget(results_label)
        
        # Scale factor row
        self.scale_factor_row = ScaleResultRow("Scale factor", "--", "highlight", self)
        card_layout.addWidget(self.scale_factor_row)
        
        # New dimensions rows
        self.new_x_row = ScaleResultRow("New X (Length)", "--", "standard", self)
        self.new_y_row = ScaleResultRow("New Y (Width)", "--", "standard", self)
        self.new_z_row = ScaleResultRow("New Z (Height)", "--", "standard", self)
        card_layout.addWidget(self.new_x_row)
        card_layout.addWidget(self.new_y_row)
        card_layout.addWidget(self.new_z_row)
        
        # New volume row (with subtle border to differentiate from dimensions)
        self.new_volume_row = ScaleResultRow("New Volume", "--", "volume", self)
        card_layout.addWidget(self.new_volume_row)
        
        # Weight comparison separator
        separator2 = Separator(self)
        card_layout.addWidget(separator2)
        
        # Weight comparison title
        comparison_label = QLabel("Weight Comparison")
        comparison_label.setFont(results_font)
        comparison_label.setStyleSheet(f"color: {default_theme.text_secondary}; margin-top: 4px;")
        card_layout.addWidget(comparison_label)
        
        # Weight comparison rows
        self.original_weight_row = ScaleResultRow("Original weight", "--", "comparison", self)
        self.target_weight_row = ScaleResultRow("Target weight", "--", "highlight", self)
        card_layout.addWidget(self.original_weight_row)
        card_layout.addWidget(self.target_weight_row)
        
        # Export button
        self.export_scaled_btn = QPushButton("Export Scaled STL")
        self.export_scaled_btn.setObjectName("exportScaledBtn")
        self.export_scaled_btn.setMinimumHeight(44)
        self.export_scaled_btn.setEnabled(False)
        self.export_scaled_btn.setStyleSheet(f"""
            QPushButton#exportScaledBtn {{
                background-color: #10B981;
                color: {default_theme.text_white};
                border: none;
                border-radius: 8px;
                padding: 10px 16px;
                font-size: 13px;
                font-weight: bold;
            }}
            QPushButton#exportScaledBtn:hover {{
                background-color: #059669;
            }}
            QPushButton#exportScaledBtn:pressed {{
                background-color: #047857;
            }}
            QPushButton#exportScaledBtn:disabled {{
                background-color: {default_theme.button_default_bg};
                color: {default_theme.text_primary};
            }}
        """)
        self.export_scaled_btn.clicked.connect(self.export_scaled_stl_file)
        card_layout.addWidget(self.export_scaled_btn)
        
        # Add shadow effect
        self._add_card_shadow(card)
        
        return card
    
    def create_pdf_report_section(self):
        """Create the PDF report export section."""
        card = QFrame()
        card.setObjectName("pdfReportCard")
        card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(16, 16, 16, 16)
        card_layout.setSpacing(10)
        
        # Header row with title and icon
        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)
        
        title_label = QLabel("Export PDF Report")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet(f"color: {default_theme.text_title}; margin-bottom: 4px;")
        
        icon_label = QLabel("📄")
        icon_label.setStyleSheet(f"color: {default_theme.icon_blue}; font-size: 16px;")
        icon_label.setAlignment(Qt.AlignCenter)
        
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(icon_label)
        card_layout.addLayout(header_layout)
        
        # Section selection label
        section_label = QLabel("Select report sections:")
        section_font = QFont()
        section_font.setPointSize(11)
        section_label.setFont(section_font)
        section_label.setStyleSheet(f"color: {default_theme.text_secondary};")
        card_layout.addWidget(section_label)
        
        # Checkbox rows
        self.report_dimensions_cb = ReportCheckbox(
            "Original dimensions", 
            checked=True, 
            enabled=True, 
            always_checked=True, 
            parent=self
        )
        self.report_dimensions_cb.set_status("Always included")
        card_layout.addWidget(self.report_dimensions_cb)
        
        self.report_surface_area_cb = ReportCheckbox(
            "Total surface area", 
            checked=True, 
            enabled=False, 
            parent=self
        )
        self.report_surface_area_cb.set_status("Load STL first")
        card_layout.addWidget(self.report_surface_area_cb)
        
        self.report_adjusted_dims_cb = ReportCheckbox(
            "Adjusted dimensions", 
            checked=True, 
            enabled=False, 
            parent=self
        )
        self.report_adjusted_dims_cb.set_status("Calculate scale first")
        card_layout.addWidget(self.report_adjusted_dims_cb)
        
        # Export button
        self.export_pdf_btn = QPushButton("Generate PDF Report")
        self.export_pdf_btn.setObjectName("exportPdfBtn")
        self.export_pdf_btn.setMinimumHeight(44)
        self.export_pdf_btn.setEnabled(False)
        self.export_pdf_btn.clicked.connect(self.export_pdf_report)
        card_layout.addWidget(self.export_pdf_btn)
        
        # Information footer
        footer_frame = QFrame()
        footer_frame.setObjectName("pdfReportFooter")
        footer_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        footer_frame.setMinimumHeight(36)
        footer_frame.setStyleSheet(f"""
            QFrame#pdfReportFooter {{
                background-color: {default_theme.background};
                border: 1px solid {default_theme.border_standard};
                border-radius: 6px;
            }}
        """)
        
        footer_layout = QHBoxLayout(footer_frame)
        footer_layout.setContentsMargins(10, 6, 10, 6)
        footer_layout.setSpacing(8)
        
        info_icon = QLabel("ℹ️")
        info_icon.setStyleSheet(f"color: {default_theme.icon_info_gray}; font-size: 11px;")
        info_icon.setFixedWidth(18)
        info_icon.setAlignment(Qt.AlignTop)
        
        disclaimer = QLabel("Report includes current calculated values only.")
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
        
        # Store current weight for scaling calculations
        self.current_weight_grams = result['grams']
        
        # Enable/disable calculate button based on whether we have valid data
        has_valid_weight = self.current_weight_grams > 0
        self.calculate_scale_btn.setEnabled(has_valid_weight)
        
        # Reset scale results if weight changed
        self.reset_scale_results()
    
    def calculate_scale(self):
        """Calculate the scale factor for target weight."""
        from core.mesh_calculator import MeshCalculator
        
        # Get target weight from input
        target_text = self.target_weight_input.text().strip()
        if not target_text:
            return
        
        try:
            target_weight = float(target_text)
        except ValueError:
            return
        
        if target_weight <= 0 or self.current_weight_grams <= 0:
            return
        
        # Calculate scale factor
        scale_result = MeshCalculator.calculate_scale_for_target_weight(
            self.current_weight_grams, target_weight
        )
        
        if not scale_result['valid']:
            return
        
        scale_factor = scale_result['scale_factor']
        self.calculated_scale_factor = scale_factor
        
        # Update scale factor display
        self.scale_factor_row.set_value(f"{scale_factor:.6f}")
        
        # Calculate new dimensions
        new_dims = MeshCalculator.apply_scale_to_dimensions(
            self.current_dimensions['width'],
            self.current_dimensions['height'],
            self.current_dimensions['depth'],
            scale_factor
        )
        
        self.new_x_row.set_value(f"{new_dims['width']:.2f} mm")
        self.new_y_row.set_value(f"{new_dims['height']:.2f} mm")
        self.new_z_row.set_value(f"{new_dims['depth']:.2f} mm")
        
        # Calculate new volume
        new_volume = MeshCalculator.apply_scale_to_volume(self.current_volume_mm3, scale_factor)
        self.new_volume_row.set_value(f"{new_volume['volume_cm3']:.4f} cm³")
        
        # Update weight comparison
        if self.current_weight_grams >= 1000:
            original_display = f"{self.current_weight_grams / 1000:.3f} kg"
        else:
            original_display = f"{self.current_weight_grams:.2f} g"
        
        if target_weight >= 1000:
            target_display = f"{target_weight / 1000:.3f} kg"
        else:
            target_display = f"{target_weight:.2f} g"
        
        self.original_weight_row.set_value(original_display)
        self.target_weight_row.set_value(target_display)
        
        # Enable export button
        self.export_scaled_btn.setEnabled(True)
        
        # Update PDF report state - scaled data now available
        self.has_scaled_data = True
        self.report_adjusted_dims_cb.set_enabled(True)
        self.report_adjusted_dims_cb.set_status("")
        self.update_pdf_button_state()
    
    def reset_scale_results(self):
        """Reset all scale result displays."""
        self.scale_factor_row.set_value("--")
        self.new_x_row.set_value("--")
        self.new_y_row.set_value("--")
        self.new_z_row.set_value("--")
        self.new_volume_row.set_value("--")
        self.original_weight_row.set_value("--")
        self.target_weight_row.set_value("--")
        self.export_scaled_btn.setEnabled(False)
        self.calculated_scale_factor = 1.0
        
        # Update PDF report state - scaled data no longer available
        self.has_scaled_data = False
        self.report_adjusted_dims_cb.set_enabled(False)
        self.report_adjusted_dims_cb.set_status("Calculate scale first")
        self.update_pdf_button_state()
    
    def export_scaled_stl_file(self):
        """Handle export of scaled STL file."""
        if self.calculated_scale_factor == 1.0:
            return
        
        # Open save dialog
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Scaled STL File",
            "",
            "STL Files (*.stl);;All Files (*)"
        )
        
        if file_path:
            # Ensure .stl extension
            if not file_path.lower().endswith('.stl'):
                file_path += '.stl'
            
            # Emit signal with file path and scale factor
            self.export_scaled_stl.emit(file_path, self.calculated_scale_factor)
    
    def update_dimensions(self, mesh_data, filename=None):
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
            self.current_dimensions = {'width': 0.0, 'height': 0.0, 'depth': 0.0}
            self.current_surface_area_cm2 = 0.0
            self.current_stl_filename = ""
            self.has_stl_loaded = False
            self.calculate_weight()
            self.reset_scale_results()
            self.calculate_scale_btn.setEnabled(False)
            
            # Update PDF report state
            self.report_surface_area_cb.set_enabled(False)
            self.report_surface_area_cb.set_status("Load STL first")
            self.update_pdf_button_state()
            return
        
        # Store filename
        if filename:
            self.current_stl_filename = os.path.basename(filename)
        
        # Update dimensions
        self.width_row.set_value(f"{mesh_data['width']:.2f} mm")
        self.height_row.set_value(f"{mesh_data['height']:.2f} mm")
        self.depth_row.set_value(f"{mesh_data['depth']:.2f} mm")
        self.volume_row.set_value(f"{mesh_data['volume_mm3']:.2f} mm³")
        
        # Store current dimensions
        self.current_dimensions = {
            'width': mesh_data['width'],
            'height': mesh_data['height'],
            'depth': mesh_data['depth']
        }
        
        # Update surface area
        self.surface_total_row.set_value(f"{mesh_data['surface_area_mm2']:.2f} mm²")
        self.surface_cm_row.set_value(f"{mesh_data['surface_area_cm2']:.2f} cm²")
        self.current_surface_area_cm2 = mesh_data['surface_area_cm2']
        self.has_stl_loaded = True
        
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
        
        # Update PDF report state - STL data now available
        self.report_surface_area_cb.set_enabled(True)
        self.report_surface_area_cb.set_status("")
        self.update_pdf_button_state()
    
    def update_pdf_button_state(self):
        """Update the PDF export button based on available data."""
        self.export_pdf_btn.setEnabled(self.has_stl_loaded)
    
    def export_pdf_report(self):
        """Generate and export PDF report."""
        if not self.has_stl_loaded:
            return
        
        # Open save dialog
        default_name = f"STL_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save PDF Report",
            default_name,
            "PDF Files (*.pdf);;All Files (*)"
        )
        
        if not file_path:
            return
        
        # Ensure .pdf extension
        if not file_path.lower().endswith('.pdf'):
            file_path += '.pdf'
        
        try:
            self._generate_pdf_report(file_path)
            QMessageBox.information(
                self,
                "Report Generated",
                f"PDF report saved successfully:\n{file_path}"
            )
        except Exception as e:
            logger.error(f"Error generating PDF report: {e}")
            QMessageBox.critical(
                self,
                "Export Error",
                f"Failed to generate PDF report:\n{str(e)}"
            )
    
    def _generate_pdf_report(self, file_path):
        """Generate the PDF report file."""
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import mm
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.enums import TA_CENTER, TA_LEFT
        
        # Create document
        doc = SimpleDocTemplate(
            file_path,
            pagesize=A4,
            rightMargin=20*mm,
            leftMargin=20*mm,
            topMargin=20*mm,
            bottomMargin=20*mm
        )
        
        # Styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=20,
            spaceAfter=12,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#1E293B')
        )
        subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=styles['Normal'],
            fontSize=10,
            spaceAfter=20,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#64748B')
        )
        section_style = ParagraphStyle(
            'SectionTitle',
            parent=styles['Heading2'],
            fontSize=14,
            spaceBefore=16,
            spaceAfter=8,
            textColor=colors.HexColor('#1E293B')
        )
        
        # Build content
        story = []
        
        # Title
        story.append(Paragraph("STL Analysis Report", title_style))
        
        # Subtitle with file info and date
        subtitle_text = f"File: {self.current_stl_filename or 'Unknown'} | Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        story.append(Paragraph(subtitle_text, subtitle_style))
        story.append(Spacer(1, 10))
        
        # Table styling
        table_style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F0F7FF')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#1E293B')),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('LEFTPADDING', (0, 0), (-1, -1), 12),
            ('RIGHTPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ])
        
        col_widths = [90*mm, 70*mm]
        
        # Original Dimensions (always included)
        story.append(Paragraph("Original Dimensions", section_style))
        dim_data = [
            ['Property', 'Value'],
            ['Length (X)', f"{self.current_dimensions['width']:.2f} mm"],
            ['Width (Y)', f"{self.current_dimensions['height']:.2f} mm"],
            ['Height (Z)', f"{self.current_dimensions['depth']:.2f} mm"],
            ['Volume', f"{self.current_volume_mm3:.2f} mm³"],
        ]
        dim_table = Table(dim_data, colWidths=col_widths)
        dim_table.setStyle(table_style)
        story.append(dim_table)
        
        # Surface Area (if checkbox selected and available)
        if self.report_surface_area_cb.is_checked() and self.current_surface_area_cm2 > 0:
            story.append(Spacer(1, 8))
            story.append(Paragraph("Surface Area (Galvanizing Data)", section_style))
            surface_data = [
                ['Property', 'Value'],
                ['Total Surface Area', f"{self.current_surface_area_cm2:.2f} cm²"],
            ]
            surface_table = Table(surface_data, colWidths=col_widths)
            surface_table.setStyle(table_style)
            story.append(surface_table)
        
        # Adjusted Dimensions (if checkbox selected and scaling applied)
        if self.report_adjusted_dims_cb.is_checked() and self.has_scaled_data:
            story.append(Spacer(1, 8))
            story.append(Paragraph("Adjusted Dimensions", section_style))
            
            # Get current adjusted values from display
            adjusted_data = [
                ['Property', 'Value'],
                ['Scale Factor', self.scale_factor_row.value_label.text()],
                ['New Length (X)', self.new_x_row.value_label.text()],
                ['New Width (Y)', self.new_y_row.value_label.text()],
                ['New Height (Z)', self.new_z_row.value_label.text()],
                ['New Volume', self.new_volume_row.value_label.text()],
            ]
            adjusted_table = Table(adjusted_data, colWidths=col_widths)
            adjusted_table.setStyle(table_style)
            story.append(adjusted_table)
            
            # Weight comparison
            story.append(Spacer(1, 8))
            story.append(Paragraph("Weight Comparison", section_style))
            
            # Get material name
            material_index = self.material_combo.currentIndex()
            material_name = self.MATERIALS[material_index][0] if 0 <= material_index < len(self.MATERIALS) else "Unknown"
            
            weight_data = [
                ['Property', 'Value'],
                ['Material', material_name],
                ['Original Weight', self.original_weight_row.value_label.text()],
                ['Target Weight', self.target_weight_row.value_label.text()],
            ]
            weight_table = Table(weight_data, colWidths=col_widths)
            weight_table.setStyle(table_style)
            story.append(weight_table)
        
        # Build PDF
        doc.build(story)
