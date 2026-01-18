"""
Main STL Viewer Window with minimalistic UI.
"""
import sys
import logging
from pathlib import Path
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QFileDialog,
    QMessageBox, QSplitter, QFrame, QApplication
)
from PyQt5.QtCore import Qt
# Try QtInteractor first, fallback to offscreen if it fails
try:
    from viewer_widget import STLViewerWidget
    USE_OFFSCREEN = False
except Exception as e:
    print(f"Warning: Could not import QtInteractor viewer, using offscreen fallback: {e}", file=sys.stderr)
    from viewer_widget_offscreen import STLViewerWidgetOffscreen as STLViewerWidget
    USE_OFFSCREEN = True

from ui.sidebar_panel import SidebarPanel
from ui.toolbar import ViewControlsToolbar
from ui.styles import get_global_stylesheet, default_theme
from core.mesh_calculator import MeshCalculator

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
        screen = QApplication.primaryScreen().geometry()
        window_geometry = self.frameGeometry()
        window_geometry.moveCenter(screen.center())
        self.move(window_geometry.topLeft())
        
        logger.info("init_ui: Creating central widget...")
        central_widget = QWidget()
        central_widget.setStyleSheet(f"background-color: {default_theme.background};")
        self.setCentralWidget(central_widget)
        
        logger.info("init_ui: Creating main layout...")
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        logger.info("init_ui: Creating splitter...")
        splitter = QSplitter(Qt.Horizontal)
        splitter.setStyleSheet(f"background-color: {default_theme.background};")
        main_layout.addWidget(splitter)
        
        logger.info("init_ui: Creating sidebar panel...")
        self.sidebar_panel = SidebarPanel()
        self.sidebar_panel.upload_btn.clicked.connect(self.upload_stl_file)
        self.sidebar_panel.export_scaled_stl.connect(self.export_scaled_stl)
        splitter.addWidget(self.sidebar_panel)
        logger.info("init_ui: Sidebar panel created")
        
        # Create right panel container (toolbar + viewer)
        right_container = QWidget()
        right_layout = QVBoxLayout(right_container)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)
        
        # Create toolbar
        logger.info("init_ui: Creating toolbar...")
        self.toolbar = ViewControlsToolbar()
        self._connect_toolbar_signals()
        right_layout.addWidget(self.toolbar)
        logger.info("init_ui: Toolbar created")
        
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
            right_layout.addWidget(self.viewer_widget, 1)  # Add with stretch factor
        except Exception as e:
            debug_print(f"init_ui: ERROR creating viewer widget: {e}")
            logger.error(f"init_ui: Error creating viewer widget: {e}", exc_info=True)
            # Try offscreen as fallback
            try:
                debug_print("init_ui: Trying offscreen renderer as fallback...")
                logger.info("init_ui: Trying offscreen renderer as fallback...")
                from viewer_widget_offscreen import STLViewerWidgetOffscreen
                self.viewer_widget = STLViewerWidgetOffscreen()
                right_layout.addWidget(self.viewer_widget, 1)
                debug_print("init_ui: Offscreen renderer fallback successful")
                logger.info("init_ui: Offscreen renderer fallback successful")
            except Exception as e2:
                debug_print(f"init_ui: Offscreen fallback also failed: {e2}")
                logger.error(f"init_ui: Offscreen fallback also failed: {e2}", exc_info=True)
                raise
        
        # Add right container to splitter
        splitter.addWidget(right_container)
        
        logger.info("init_ui: Configuring splitter...")
        splitter.setSizes([200, 1000])
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        
        logger.info("init_ui: Applying styling...")
        self.apply_styling()
        logger.info("init_ui: UI initialization complete")
    
    def apply_styling(self):
        """Apply minimalistic styling with floating card design."""
        self.setStyleSheet(get_global_stylesheet())
    
    def _connect_toolbar_signals(self):
        """Connect toolbar signals to handler methods."""
        self.toolbar.toggle_grid.connect(self._toggle_grid)
        self.toolbar.toggle_theme.connect(self._toggle_theme)
        self.toolbar.toggle_wireframe.connect(self._toggle_wireframe)
        self.toolbar.reset_rotation.connect(self._reset_rotation)
        self.toolbar.view_front.connect(self._view_front)
        self.toolbar.view_side.connect(self._view_side)
        self.toolbar.view_top.connect(self._view_top)
        self.toolbar.toggle_fullscreen.connect(self._toggle_fullscreen)
        self.toolbar.load_file.connect(self.upload_stl_file)
    
    def _toggle_grid(self):
        """Toggle the background grid."""
        if hasattr(self.viewer_widget, 'plotter') and self.viewer_widget.plotter is not None:
            try:
                if self.toolbar.grid_enabled:
                    self.viewer_widget.plotter.show_grid()
                else:
                    self.viewer_widget.plotter.remove_bounds_axes()
            except Exception as e:
                logger.warning(f"Could not toggle grid: {e}")
    
    def _toggle_theme(self):
        """Toggle between light and dark viewer theme."""
        if hasattr(self.viewer_widget, 'plotter') and self.viewer_widget.plotter is not None:
            try:
                if self.toolbar.dark_theme:
                    self.viewer_widget.plotter.background_color = '#1a1a2e'
                else:
                    self.viewer_widget.plotter.background_color = 'white'
            except Exception as e:
                logger.warning(f"Could not toggle theme: {e}")
    
    def _toggle_wireframe(self):
        """Toggle wireframe display mode."""
        if hasattr(self.viewer_widget, 'current_actor') and self.viewer_widget.current_actor is not None:
            try:
                if self.toolbar.wireframe_enabled:
                    self.viewer_widget.current_actor.GetProperty().SetRepresentationToWireframe()
                else:
                    self.viewer_widget.current_actor.GetProperty().SetRepresentationToSurface()
                self.viewer_widget.plotter.render()
            except Exception as e:
                logger.warning(f"Could not toggle wireframe: {e}")
    
    def _reset_rotation(self):
        """Reset view to default isometric rotation."""
        if hasattr(self.viewer_widget, 'plotter') and self.viewer_widget.plotter is not None:
            try:
                self.viewer_widget.plotter.reset_camera()
                self.viewer_widget.plotter.view_isometric()
            except Exception as e:
                logger.warning(f"Could not reset rotation: {e}")
    
    def _view_front(self):
        """Set camera to front view."""
        if hasattr(self.viewer_widget, 'plotter') and self.viewer_widget.plotter is not None:
            try:
                self.viewer_widget.plotter.view_yz()
            except Exception as e:
                logger.warning(f"Could not set front view: {e}")
    
    def _view_side(self):
        """Set camera to side view."""
        if hasattr(self.viewer_widget, 'plotter') and self.viewer_widget.plotter is not None:
            try:
                self.viewer_widget.plotter.view_xz()
            except Exception as e:
                logger.warning(f"Could not set side view: {e}")
    
    def _view_top(self):
        """Set camera to top view."""
        if hasattr(self.viewer_widget, 'plotter') and self.viewer_widget.plotter is not None:
            try:
                self.viewer_widget.plotter.view_xy()
            except Exception as e:
                logger.warning(f"Could not set top view: {e}")
    
    def _toggle_fullscreen(self):
        """Toggle fullscreen mode."""
        if self.toolbar.is_fullscreen:
            self.showFullScreen()
        else:
            self.showNormal()
    
    def keyPressEvent(self, event):
        """Handle key press events."""
        if event.key() == Qt.Key_Escape and self.isFullScreen():
            self.showNormal()
            self.toolbar.reset_fullscreen_state()
        else:
            super().keyPressEvent(event)

    
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
                # Update toolbar load button to show filename
                self.toolbar.set_loaded_filename(filename)
                # Enable toolbar controls
                self.toolbar.set_stl_loaded(True)
                # Update dimensions display
                if hasattr(self.viewer_widget, 'current_mesh'):
                    mesh = self.viewer_widget.current_mesh
                    if mesh is not None:
                        mesh_data = MeshCalculator.get_mesh_data(mesh)
                        self.sidebar_panel.update_dimensions(mesh_data, file_path)
        else:
            logger.info("upload_stl_file: File selection cancelled")
    
    def export_scaled_stl(self, file_path, scale_factor):
        """Export the current mesh scaled by the given factor."""
        logger.info(f"export_scaled_stl: Exporting scaled STL to {file_path} with scale {scale_factor}")
        
        if not hasattr(self.viewer_widget, 'current_mesh') or self.viewer_widget.current_mesh is None:
            logger.error("export_scaled_stl: No mesh loaded")
            QMessageBox.warning(
                self,
                "No Mesh Loaded",
                "Please load an STL file first before exporting."
            )
            return
        
        try:
            # Scale and export the mesh
            scaled_mesh = MeshCalculator.scale_mesh(self.viewer_widget.current_mesh, scale_factor)
            
            if scaled_mesh is None:
                logger.error("export_scaled_stl: Failed to scale mesh")
                QMessageBox.critical(
                    self,
                    "Export Error",
                    "Failed to scale the mesh. Please try again."
                )
                return
            
            success = MeshCalculator.export_stl(scaled_mesh, file_path)
            
            if success:
                logger.info(f"export_scaled_stl: Successfully exported to {file_path}")
                QMessageBox.information(
                    self,
                    "Export Successful",
                    f"Scaled STL file exported successfully to:\n{file_path}"
                )
            else:
                logger.error(f"export_scaled_stl: Failed to export to {file_path}")
                QMessageBox.critical(
                    self,
                    "Export Error",
                    f"Failed to export STL file to:\n{file_path}"
                )
        except Exception as e:
            logger.error(f"export_scaled_stl: Error during export: {e}", exc_info=True)
            QMessageBox.critical(
                self,
                "Export Error",
                f"Error during export:\n{str(e)}"
            )


def main():
    """Main function to run the application."""
    from PyQt5.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    window = STLViewerWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
