"""
Main STL Viewer Window with minimalistic UI.
"""
import sys
import logging
from pathlib import Path
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QFileDialog, QLabel, QMessageBox, QSplitter,
    QGroupBox, QGridLayout, QFrame, QSpacerItem, QSizePolicy
)
from PyQt5.QtCore import Qt, QSize, QTimer, QEvent
from PyQt5.QtGui import QFont, QColor
# Try QtInteractor first, fallback to offscreen if it fails
try:
    from viewer_widget import STLViewerWidget
    USE_OFFSCREEN = False
except Exception as e:
    print(f"Warning: Could not import QtInteractor viewer, using offscreen fallback: {e}", file=sys.stderr)
    from viewer_widget_offscreen import STLViewerWidgetOffscreen as STLViewerWidget
    USE_OFFSCREEN = True

logger = logging.getLogger(__name__)

# Print to stderr for immediate visibility
def debug_print(msg):
    print(f"[DEBUG] {msg}", file=sys.stderr)
    sys.stderr.flush()


class STLViewerWindow(QMainWindow):
    """Main window for STL file viewer application."""
    
    def __init__(self):
        debug_print("STLViewerWindow: Initializing...")
        logger.info("STLViewerWindow: Initializing...")
        super().__init__()
        debug_print("STLViewerWindow: Parent initialized")
        logger.info("STLViewerWindow: Parent initialized")
        self.init_ui()
        debug_print("STLViewerWindow: Initialization complete")
        logger.info("STLViewerWindow: Initialization complete")
    
    def init_ui(self):
        """Initialize the user interface."""
        logger.info("init_ui: Starting UI initialization...")
        
        logger.info("init_ui: Setting window title and size...")
        self.setWindowTitle("STL 3D Viewer")
        self.setMinimumSize(1200, 800)
        self.resize(1200, 800)
        
        # Center window on screen
        from PyQt5.QtWidgets import QApplication
        screen = QApplication.primaryScreen().geometry()
        window_geometry = self.frameGeometry()
        window_geometry.moveCenter(screen.center())
        self.move(window_geometry.topLeft())
        
        logger.info("init_ui: Creating central widget...")
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        logger.info("init_ui: Creating main layout...")
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        logger.info("init_ui: Creating splitter...")
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)
        
        logger.info("init_ui: Creating left panel...")
        left_panel = self.create_left_panel()
        splitter.addWidget(left_panel)
        logger.info("init_ui: Left panel created")
        
        debug_print("init_ui: Creating 3D viewer widget (this may take a moment)...")
        logger.info("init_ui: Creating 3D viewer widget (this may take a moment)...")
        try:
            # Try QtInteractor first
            if not USE_OFFSCREEN:
                self.viewer_widget = STLViewerWidget()
                debug_print("init_ui: 3D viewer widget (QtInteractor) created successfully")
                logger.info("init_ui: 3D viewer widget (QtInteractor) created successfully")
            else:
                # Use offscreen renderer
                from viewer_widget_offscreen import STLViewerWidgetOffscreen
                self.viewer_widget = STLViewerWidgetOffscreen()
                debug_print("init_ui: 3D viewer widget (Offscreen) created successfully")
                logger.info("init_ui: 3D viewer widget (Offscreen) created successfully")
            splitter.addWidget(self.viewer_widget)
        except Exception as e:
            debug_print(f"init_ui: ERROR creating viewer widget: {e}")
            logger.error(f"init_ui: Error creating viewer widget: {e}", exc_info=True)
            # Try offscreen as fallback
            try:
                debug_print("init_ui: Trying offscreen renderer as fallback...")
                logger.info("init_ui: Trying offscreen renderer as fallback...")
                from viewer_widget_offscreen import STLViewerWidgetOffscreen
                self.viewer_widget = STLViewerWidgetOffscreen()
                splitter.addWidget(self.viewer_widget)
                debug_print("init_ui: Offscreen renderer fallback successful")
                logger.info("init_ui: Offscreen renderer fallback successful")
            except Exception as e2:
                debug_print(f"init_ui: Offscreen fallback also failed: {e2}")
                logger.error(f"init_ui: Offscreen fallback also failed: {e2}", exc_info=True)
                raise
        
        logger.info("init_ui: Configuring splitter...")
        splitter.setSizes([200, 1000])
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        
        logger.info("init_ui: Applying styling...")
        self.apply_styling()
        logger.info("init_ui: UI initialization complete")
    
    def create_left_panel(self):
        """Create the left panel with upload controls."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setAlignment(Qt.AlignTop)
        layout.setSpacing(15)
        
        # Title label
        title_label = QLabel("STL Viewer")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # Upload button
        upload_btn = QPushButton("Upload STL File")
        upload_btn.setMinimumHeight(50)
        upload_btn.clicked.connect(self.upload_stl_file)
        layout.addWidget(upload_btn)
        
        # Info label
        info_label = QLabel(
            "Click the button above\nto load an STL file\nfor 3D visualization."
        )
        info_label.setAlignment(Qt.AlignCenter)
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # Dimensions section
        self.dimensions_group = self.create_dimensions_section()
        layout.addWidget(self.dimensions_group)
        
        # Surface Area section (sister widget)
        self.surface_area_group = self.create_surface_area_section()
        layout.addWidget(self.surface_area_group)
        
        # Add stretch to push content to top
        layout.addStretch()
        
        return panel
    
    def create_dimension_row(self, label_text, value_text="--"):
        """Create a styled dimension row with Alice Blue pill background and hover effect."""
        # Container frame for the row (pill style)
        row_frame = QFrame()
        row_frame.setObjectName("dimensionRow")
        row_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        row_frame.setFixedHeight(44)
        
        row_layout = QHBoxLayout(row_frame)
        row_layout.setContentsMargins(14, 8, 14, 8)
        row_layout.setSpacing(0)
        
        # Label (left-anchored, secondary text)
        label = QLabel(label_text)
        label.setObjectName("dimensionLabel")
        label_font = QFont()
        label_font.setPointSize(11)
        label.setFont(label_font)
        
        # Spacer to push value to the right
        spacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        
        # Value (right-anchored, primary focus)
        value = QLabel(value_text)
        value.setObjectName("dimensionValue")
        value_font = QFont()
        value_font.setPointSize(13)
        value_font.setBold(True)
        value.setFont(value_font)
        value.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        
        row_layout.addWidget(label)
        row_layout.addItem(spacer)
        row_layout.addWidget(value)
        
        # Install event filter for hover effect
        row_frame.installEventFilter(self)
        
        return row_frame, value
    
    def eventFilter(self, obj, event):
        """Handle hover events for dimension and surface area rows."""
        obj_name = obj.objectName()
        
        if obj_name == "dimensionRow":
            if event.type() == QEvent.Enter:
                obj.setStyleSheet("""
                    QFrame#dimensionRow {
                        background-color: #D6E8F5;
                        border-radius: 8px;
                    }
                """)
            elif event.type() == QEvent.Leave:
                obj.setStyleSheet("""
                    QFrame#dimensionRow {
                        background-color: #EBF4FA;
                        border-radius: 8px;
                    }
                """)
        elif obj_name == "surfaceRowStandard":
            if event.type() == QEvent.Enter:
                obj.setStyleSheet("""
                    QFrame#surfaceRowStandard {
                        background-color: #F0F0F0;
                        border: 1px solid #D0D5DD;
                        border-radius: 8px;
                    }
                """)
            elif event.type() == QEvent.Leave:
                obj.setStyleSheet("""
                    QFrame#surfaceRowStandard {
                        background-color: #FFFFFF;
                        border: 1px solid #E0E6ED;
                        border-radius: 8px;
                    }
                """)
        elif obj_name == "surfaceRowHighlight":
            if event.type() == QEvent.Enter:
                obj.setStyleSheet("""
                    QFrame#surfaceRowHighlight {
                        background-color: #B2EBF2;
                        border: 1px solid #00838F;
                        border-radius: 8px;
                    }
                """)
            elif event.type() == QEvent.Leave:
                obj.setStyleSheet("""
                    QFrame#surfaceRowHighlight {
                        background-color: #E0F7FA;
                        border: 1px solid #26A69A;
                        border-radius: 8px;
                    }
                """)
        return super().eventFilter(obj, event)
    
    def create_dimensions_section(self):
        """Create the floating info card dimensions display."""
        # Main card container
        card = QFrame()
        card.setObjectName("dimensionsCard")
        card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(16, 16, 16, 16)
        card_layout.setSpacing(10)
        
        # Card title
        title_label = QLabel("Dimensions")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #2C3E50; margin-bottom: 4px;")
        card_layout.addWidget(title_label)
        
        # Dimension rows
        width_row, self.dim_width_value = self.create_dimension_row("Length (X)")
        height_row, self.dim_height_value = self.create_dimension_row("Width (Y)")
        depth_row, self.dim_depth_value = self.create_dimension_row("Height (Z)")
        
        card_layout.addWidget(width_row)
        card_layout.addWidget(height_row)
        card_layout.addWidget(depth_row)
        
        # Subtle separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setStyleSheet("background-color: #E0E6ED; max-height: 1px; margin: 6px 0;")
        card_layout.addWidget(separator)
        
        # Volume row only
        volume_row, self.dim_volume_value = self.create_dimension_row("Volume")
        card_layout.addWidget(volume_row)
        
        return card
    
    def create_surface_area_row(self, label_text, value_text="--", row_type="standard"):
        """Create a styled surface area row with different styles based on row_type."""
        row_frame = QFrame()
        row_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        row_frame.setFixedHeight(44)
        
        if row_type == "standard":
            row_frame.setObjectName("surfaceRowStandard")
        elif row_type == "highlight":
            row_frame.setObjectName("surfaceRowHighlight")
        else:
            row_frame.setObjectName("surfaceRowStandard")
        
        row_layout = QHBoxLayout(row_frame)
        row_layout.setContentsMargins(14, 8, 14, 8)
        row_layout.setSpacing(0)
        
        # Label (left-anchored)
        label = QLabel(label_text)
        label.setObjectName("surfaceLabel")
        label_font = QFont()
        label_font.setPointSize(11)
        label.setFont(label_font)
        
        # Spacer
        spacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        
        # Value (right-anchored)
        value = QLabel(value_text)
        value.setObjectName("surfaceValue")
        value_font = QFont()
        value_font.setPointSize(13)
        value_font.setBold(True)
        value.setFont(value_font)
        value.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        
        row_layout.addWidget(label)
        row_layout.addItem(spacer)
        row_layout.addWidget(value)
        
        # Install event filter for hover effect
        row_frame.installEventFilter(self)
        
        return row_frame, value
    
    def create_surface_area_section(self):
        """Create the Surface Area floating info card."""
        # Main card container
        card = QFrame()
        card.setObjectName("surfaceAreaCard")
        card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(16, 16, 16, 16)
        card_layout.setSpacing(10)
        
        # Header row with title and icon
        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)
        
        # Card title
        title_label = QLabel("Total Surface Area")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #2C3E50; margin-bottom: 4px;")
        
        # Tray/download icon (using unicode for simplicity)
        icon_label = QLabel("⬇")
        icon_label.setStyleSheet("color: #4A90E2; font-size: 16px;")
        icon_label.setAlignment(Qt.AlignCenter)
        
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(icon_label)
        card_layout.addLayout(header_layout)
        
        # Total area row (standard - white background with border)
        total_row, self.surface_total_value = self.create_surface_area_row("Total area", "--", "standard")
        card_layout.addWidget(total_row)
        
        # Area in cm² row (highlight - cyan background with teal border)
        area_cm_row, self.surface_cm_value = self.create_surface_area_row("Area (cm²)", "--", "highlight")
        card_layout.addWidget(area_cm_row)
        
        # Information footer
        footer_frame = QFrame()
        footer_frame.setObjectName("surfaceFooter")
        footer_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        footer_frame.setFixedHeight(32)
        
        footer_layout = QHBoxLayout(footer_frame)
        footer_layout.setContentsMargins(10, 6, 10, 6)
        footer_layout.setSpacing(8)
        
        # Info icon
        info_icon = QLabel("ℹ")
        info_icon.setStyleSheet("color: #718096; font-size: 12px;")
        info_icon.setFixedWidth(16)
        
        # Disclaimer text
        disclaimer = QLabel("Calculated surface area")
        disclaimer_font = QFont()
        disclaimer_font.setPointSize(9)
        disclaimer.setFont(disclaimer_font)
        disclaimer.setStyleSheet("color: #718096;")
        
        footer_layout.addWidget(info_icon)
        footer_layout.addWidget(disclaimer)
        footer_layout.addStretch()
        
        card_layout.addWidget(footer_frame)
        
        return card
    
    def update_dimensions(self, mesh):
        """Update the dimensions display with mesh data."""
        if mesh is None:
            self.dim_width_value.setText("--")
            self.dim_height_value.setText("--")
            self.dim_depth_value.setText("--")
            self.dim_volume_value.setText("--")
            self.surface_total_value.setText("--")
            self.surface_cm_value.setText("--")
            return
        
        # Get bounding box dimensions
        bounds = mesh.bounds  # (xmin, xmax, ymin, ymax, zmin, zmax)
        width = bounds[1] - bounds[0]   # X dimension
        height = bounds[3] - bounds[2]  # Y dimension
        depth = bounds[5] - bounds[4]   # Z dimension
        
        # Get volume and surface area
        try:
            volume = mesh.volume
        except:
            volume = 0.0
        
        try:
            surface_area = mesh.area
        except:
            surface_area = 0.0
        
        # Convert surface area from mm² to cm²
        surface_area_cm = surface_area / 100.0
        
        # Update labels with formatted values
        self.dim_width_value.setText(f"{width:.2f} mm")
        self.dim_height_value.setText(f"{height:.2f} mm")
        self.dim_depth_value.setText(f"{depth:.2f} mm")
        self.dim_volume_value.setText(f"{volume:.2f} mm³")
        
        # Update surface area card
        self.surface_total_value.setText(f"{surface_area:.2f} mm²")
        self.surface_cm_value.setText(f"{surface_area_cm:.2f} cm²")
    
    def apply_styling(self):
        """Apply minimalistic styling with floating card design."""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #F0F3F6;
            }
            QPushButton {
                background-color: #4A90E2;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 20px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #357ABD;
            }
            QPushButton:pressed {
                background-color: #2A5F8F;
            }
            QLabel {
                color: #4A5568;
            }
            QLabel#dimensionLabel {
                color: #718096;
            }
            QLabel#dimensionValue {
                color: #1A202C;
            }
            QFrame#dimensionsCard {
                background-color: #FFFFFF;
                border-radius: 12px;
                border: none;
            }
            QFrame#dimensionRow {
                background-color: #EBF4FA;
                border-radius: 8px;
            }
            QFrame#surfaceAreaCard {
                background-color: #FFFFFF;
                border-radius: 12px;
                border: none;
            }
            QFrame#surfaceRowStandard {
                background-color: #FFFFFF;
                border: 1px solid #E0E6ED;
                border-radius: 8px;
            }
            QFrame#surfaceRowHighlight {
                background-color: #E0F7FA;
                border: 1px solid #26A69A;
                border-radius: 8px;
            }
            QFrame#surfaceFooter {
                background-color: #F8FAFC;
                border: 1px solid #E2E8F0;
                border-radius: 6px;
            }
            QLabel#surfaceLabel {
                color: #718096;
            }
            QLabel#surfaceValue {
                color: #1A202C;
            }
        """)
    
    def upload_stl_file(self):
        """Open file dialog and load selected STL file."""
        logger.info("upload_stl_file: Opening file dialog...")
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select STL File",
            "",
            "STL Files (*.stl);;All Files (*)"
        )
        
        if file_path:
            logger.info(f"upload_stl_file: File selected: {file_path}")
            # Validate file extension
            if not file_path.lower().endswith('.stl'):
                logger.warning(f"upload_stl_file: Invalid file extension: {file_path}")
                QMessageBox.warning(
                    self,
                    "Invalid File",
                    "Please select a valid STL file (.stl extension)."
                )
                return
            
            # Load and display the STL file
            logger.info("upload_stl_file: Loading STL file into viewer...")
            success = self.viewer_widget.load_stl(file_path)
            
            if not success:
                logger.error(f"upload_stl_file: Failed to load STL file: {file_path}")
                QMessageBox.critical(
                    self,
                    "Error",
                    f"Failed to load STL file:\n{file_path}\n\nPlease ensure the file is a valid STL format."
                )
            else:
                logger.info(f"upload_stl_file: STL file loaded successfully: {file_path}")
                # Update window title with filename
                filename = Path(file_path).name
                self.setWindowTitle(f"STL 3D Viewer - {filename}")
                # Update dimensions display
                if hasattr(self.viewer_widget, 'current_mesh'):
                    self.update_dimensions(self.viewer_widget.current_mesh)
        else:
            logger.info("upload_stl_file: File selection cancelled")


def main():
    """Main function to run the application."""
    from PyQt6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    window = STLViewerWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
