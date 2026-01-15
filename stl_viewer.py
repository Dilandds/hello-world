"""
Main STL Viewer Window with minimalistic UI.
"""
import sys
import logging
from pathlib import Path
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QFileDialog, QLabel, QMessageBox, QSplitter,
    QGroupBox, QGridLayout, QFrame
)
from PyQt5.QtCore import Qt, QSize, QTimer
from PyQt5.QtGui import QFont
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
        
        # Add stretch to push content to top
        layout.addStretch()
        
        return panel
    
    def create_dimensions_section(self):
        """Create the dimensions display section."""
        group = QGroupBox("Dimensions")
        group_layout = QGridLayout(group)
        group_layout.setSpacing(8)
        
        # Create dimension labels
        self.dim_width_label = QLabel("Width (X):")
        self.dim_width_value = QLabel("--")
        self.dim_width_value.setAlignment(Qt.AlignRight)
        
        self.dim_height_label = QLabel("Height (Y):")
        self.dim_height_value = QLabel("--")
        self.dim_height_value.setAlignment(Qt.AlignRight)
        
        self.dim_depth_label = QLabel("Depth (Z):")
        self.dim_depth_value = QLabel("--")
        self.dim_depth_value.setAlignment(Qt.AlignRight)
        
        # Add separator line
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        
        self.dim_volume_label = QLabel("Volume:")
        self.dim_volume_value = QLabel("--")
        self.dim_volume_value.setAlignment(Qt.AlignRight)
        
        self.dim_surface_label = QLabel("Surface:")
        self.dim_surface_value = QLabel("--")
        self.dim_surface_value.setAlignment(Qt.AlignRight)
        
        # Add to grid layout
        group_layout.addWidget(self.dim_width_label, 0, 0)
        group_layout.addWidget(self.dim_width_value, 0, 1)
        group_layout.addWidget(self.dim_height_label, 1, 0)
        group_layout.addWidget(self.dim_height_value, 1, 1)
        group_layout.addWidget(self.dim_depth_label, 2, 0)
        group_layout.addWidget(self.dim_depth_value, 2, 1)
        group_layout.addWidget(separator, 3, 0, 1, 2)
        group_layout.addWidget(self.dim_volume_label, 4, 0)
        group_layout.addWidget(self.dim_volume_value, 4, 1)
        group_layout.addWidget(self.dim_surface_label, 5, 0)
        group_layout.addWidget(self.dim_surface_value, 5, 1)
        
        return group
    
    def update_dimensions(self, mesh):
        """Update the dimensions display with mesh data."""
        if mesh is None:
            self.dim_width_value.setText("--")
            self.dim_height_value.setText("--")
            self.dim_depth_value.setText("--")
            self.dim_volume_value.setText("--")
            self.dim_surface_value.setText("--")
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
        
        # Update labels with formatted values
        self.dim_width_value.setText(f"{width:.2f} mm")
        self.dim_height_value.setText(f"{height:.2f} mm")
        self.dim_depth_value.setText(f"{depth:.2f} mm")
        self.dim_volume_value.setText(f"{volume:.2f} mm³")
        self.dim_surface_value.setText(f"{surface_area:.2f} mm²")
    
    def apply_styling(self):
        """Apply minimalistic styling to the application."""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            QPushButton {
                background-color: #4a90e2;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #357abd;
            }
            QPushButton:pressed {
                background-color: #2a5f8f;
            }
            QLabel {
                color: #333333;
            }
            QGroupBox {
                font-weight: bold;
                border: 1px solid #cccccc;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
                background-color: #ffffff;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: #333333;
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
