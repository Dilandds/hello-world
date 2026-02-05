"""
Main ECTOFORM Window with minimalistic UI.
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
from ui.ruler_toolbar import RulerToolbar
from ui.styles import get_global_stylesheet, default_theme
from core.mesh_calculator import MeshCalculator

logger = logging.getLogger(__name__)


def safe_flush(stream):
    """Safely flush a stream, handling None (common in PyInstaller Windows builds)."""
    if stream is not None:
        try:
            stream.flush()
        except (AttributeError, OSError):
            pass  # Stream may not support flush or may be closed


# Print to stderr for immediate visibility
def debug_print(msg):
    print(f"[DEBUG] {msg}", file=sys.stderr)
    safe_flush(sys.stderr)


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
        self.setWindowTitle("ECTOFORM")
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
        
        # Create ruler toolbar (hidden by default)
        logger.info("init_ui: Creating ruler toolbar...")
        self.ruler_toolbar = RulerToolbar()
        self.ruler_toolbar.hide()  # Hidden until ruler mode is activated
        self._connect_ruler_toolbar_signals()
        right_layout.addWidget(self.ruler_toolbar)
        logger.info("init_ui: Ruler toolbar created")
        
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
            
            # Connect drag-and-drop signals
            self._connect_viewer_signals()
            
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
                self._connect_viewer_signals()
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
        self.toolbar.toggle_ruler.connect(self._toggle_ruler_mode)
        self.toolbar.load_file.connect(self.upload_stl_file)
        self.toolbar.clear_model.connect(self._clear_current_model)
    
    def _connect_ruler_toolbar_signals(self):
        """Connect ruler toolbar signals to handler methods."""
        self.ruler_toolbar.view_front.connect(self._ruler_view_front)
        self.ruler_toolbar.view_side.connect(self._ruler_view_side)
        self.ruler_toolbar.view_top.connect(self._ruler_view_top)
        self.ruler_toolbar.view_bottom.connect(self._ruler_view_bottom)
        self.ruler_toolbar.view_rear.connect(self._ruler_view_rear)
        self.ruler_toolbar.clear_measurements.connect(self._clear_measurements)
        self.ruler_toolbar.exit_ruler.connect(self._exit_ruler_mode)
    
    def _clear_current_model(self):
        """Clear the current model from the viewer."""
        logger.info("_clear_current_model: Clearing current model...")
        if hasattr(self.viewer_widget, 'clear_viewer'):
            self.viewer_widget.clear_viewer()
            # Update toolbar state
            self.toolbar.set_stl_loaded(False)
            # Reset window title
            self.setWindowTitle("ECTOFORM")
            # Reset toolbar load button tooltip
            self.toolbar.set_loaded_filename(None)
    
    def _connect_viewer_signals(self):
        """Connect viewer widget signals for drag-and-drop."""
        if hasattr(self.viewer_widget, 'file_dropped'):
            self.viewer_widget.file_dropped.connect(self._load_dropped_file)
        if hasattr(self.viewer_widget, 'click_to_upload'):
            self.viewer_widget.click_to_upload.connect(self.upload_stl_file)
        if hasattr(self.viewer_widget, 'drop_error'):
            self.viewer_widget.drop_error.connect(self._show_drop_error)
    
    def _load_dropped_file(self, file_path):
        """Load a file that was dropped on the viewer."""
        logger.info(f"_load_dropped_file: Loading dropped file: {file_path}")
        
        # Validate file extension
        file_ext = file_path.lower()
        if not (file_ext.endswith('.stl') or file_ext.endswith('.step') or file_ext.endswith('.stp') or file_ext.endswith('.3dm') or file_ext.endswith('.obj') or file_ext.endswith('.iges') or file_ext.endswith('.igs')):
            QMessageBox.warning(
                self,
                "Invalid File",
                "Please select a valid 3D file (.stl, .step, .stp, .3dm, .obj, .iges, or .igs extension)."
            )
            return
        
        # Load and display the STL file
        success = self.viewer_widget.load_stl(file_path)
        
        if not success:
            file_ext = file_path.lower()
            if file_ext.endswith('.step') or file_ext.endswith('.stp'):
                file_type = "STEP"
            elif file_ext.endswith('.3dm'):
                file_type = "3DM"
            elif file_ext.endswith('.obj'):
                file_type = "OBJ"
            elif file_ext.endswith('.iges') or file_ext.endswith('.igs'):
                file_type = "IGES"
            else:
                file_type = "STL"
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to load {file_type} file:\n{file_path}\n\nPlease ensure the file is a valid {file_type} format."
            )
        else:
            # Update window title with filename
            filename = Path(file_path).name
            self.setWindowTitle(f"ECTOFORM - {filename}")
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
    
    def _show_drop_error(self, error_msg):
        """Show an error message from drag-and-drop."""
        QMessageBox.warning(self, "Upload Error", error_msg)
    
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
    
    # ========== Ruler Mode Methods ==========
    
    def _toggle_ruler_mode(self):
        """Toggle ruler/measurement mode."""
        if self.toolbar.ruler_mode_enabled:
            # Enable ruler mode
            if hasattr(self.viewer_widget, 'enable_ruler_mode'):
                success = self.viewer_widget.enable_ruler_mode()
                if success:
                    self.ruler_toolbar.show()
                    self.ruler_toolbar.reset_to_front()
                    self._ruler_view_front()  # Auto-switch to front view
                    logger.info("_toggle_ruler_mode: Ruler mode enabled")
                else:
                    # Failed to enable, reset toolbar state
                    self.toolbar.ruler_mode_enabled = False
                    self.toolbar.ruler_btn.set_active(False)
                    logger.warning("_toggle_ruler_mode: Failed to enable ruler mode")
        else:
            # Disable ruler mode
            self._exit_ruler_mode()
    
    def _exit_ruler_mode(self):
        """Exit ruler mode and restore normal view."""
        if hasattr(self.viewer_widget, 'disable_ruler_mode'):
            self.viewer_widget.disable_ruler_mode()
        self.ruler_toolbar.hide()
        # Reset toolbar button state
        self.toolbar.ruler_mode_enabled = False
        self.toolbar.ruler_btn.set_active(False)
        self.toolbar.ruler_btn.set_icon("📏")
        logger.info("_exit_ruler_mode: Ruler mode disabled")
    
    def _ruler_view_front(self):
        """Set front orthographic view for measurement."""
        if hasattr(self.viewer_widget, 'view_front_ortho'):
            self.viewer_widget.view_front_ortho()
    
    def _ruler_view_side(self):
        """Set side orthographic view for measurement."""
        if hasattr(self.viewer_widget, 'view_side_ortho'):
            self.viewer_widget.view_side_ortho()
    
    def _ruler_view_top(self):
        """Set top orthographic view for measurement."""
        if hasattr(self.viewer_widget, 'view_top_ortho'):
            self.viewer_widget.view_top_ortho()
    
    def _ruler_view_bottom(self):
        """Set bottom orthographic view for measurement."""
        if hasattr(self.viewer_widget, 'view_bottom_ortho'):
            self.viewer_widget.view_bottom_ortho()
    
    def _ruler_view_rear(self):
        """Set rear orthographic view for measurement."""
        if hasattr(self.viewer_widget, 'view_rear_ortho'):
            self.viewer_widget.view_rear_ortho()
    
    def _clear_measurements(self):
        """Clear all measurements from the viewer."""
        if hasattr(self.viewer_widget, 'clear_measurements'):
            self.viewer_widget.clear_measurements()
    
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
        """Open file dialog and load selected STL or STEP file."""
        logger.info("upload_stl_file: Opening file dialog...")
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select 3D File",
            "",
            "3D Files (*.stl *.step *.stp *.3dm *.obj *.iges *.igs);;STL Files (*.stl);;STEP Files (*.step *.stp);;3DM Files (*.3dm);;OBJ Files (*.obj);;IGES Files (*.iges *.igs);;All Files (*)"
        )
        
        if file_path:
            logger.info(f"upload_stl_file: File selected: {file_path}")
            # Validate file extension
            file_ext = file_path.lower()
            if not (file_ext.endswith('.stl') or file_ext.endswith('.step') or file_ext.endswith('.stp') or file_ext.endswith('.3dm') or file_ext.endswith('.obj') or file_ext.endswith('.iges') or file_ext.endswith('.igs')):
                logger.warning(f"upload_stl_file: Invalid file extension: {file_path}")
                QMessageBox.warning(
                    self,
                    "Invalid File",
                    "Please select a valid 3D file (.stl, .step, .stp, .3dm, .obj, .iges, or .igs extension)."
                )
                return
            
            # Load and display the STL file
            logger.info("upload_stl_file: Loading STL file into viewer...")
            success = self.viewer_widget.load_stl(file_path)
            
            if not success:
                logger.error(f"upload_stl_file: Failed to load file: {file_path}")
                file_ext = file_path.lower()
                if file_ext.endswith('.step') or file_ext.endswith('.stp'):
                    file_type = "STEP"
                elif file_ext.endswith('.3dm'):
                    file_type = "3DM"
                elif file_ext.endswith('.obj'):
                    file_type = "OBJ"
                elif file_ext.endswith('.iges') or file_ext.endswith('.igs'):
                    file_type = "IGES"
                else:
                    file_type = "STL"
                QMessageBox.critical(
                    self,
                    "Error",
                    f"Failed to load {file_type} file:\n{file_path}\n\nPlease ensure the file is a valid {file_type} format."
                )
            else:
                logger.info(f"upload_stl_file: STL file loaded successfully: {file_path}")
                # Update window title with filename
                filename = Path(file_path).name
                self.setWindowTitle(f"ECTOFORM - {filename}")
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
