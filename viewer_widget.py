"""
3D Viewer Widget using PyVista for STL file visualization.
"""
import sys
import os
import logging
import pyvista as pv
from pyvistaqt import QtInteractor
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QStackedLayout
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from ui.drop_zone_overlay import DropZoneOverlay

# Set PyVista environment variables for macOS compatibility
os.environ.setdefault('PYVISTA_OFF_SCREEN', 'false')
os.environ.setdefault('PYVISTA_USE_PANEL', 'false')

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


class STLViewerWidget(QWidget):
    """PyVista-based 3D viewer widget for displaying STL files."""
    
    # Signals for drag-and-drop functionality
    file_dropped = pyqtSignal(str)
    click_to_upload = pyqtSignal()
    drop_error = pyqtSignal(str)
    
    def __init__(self, parent=None):
        debug_print("STLViewerWidget: Initializing...")
        logger.info("STLViewerWidget: Initializing...")
        super().__init__(parent)
        debug_print("STLViewerWidget: Parent initialized")
        logger.info("STLViewerWidget: Parent initialized")
        
        # Set up stacked layout for overlay
        self.layout = QStackedLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setStackingMode(QStackedLayout.StackAll)
        
        # Container for the 3D viewer
        self.viewer_container = QWidget()
        self.viewer_layout = QVBoxLayout(self.viewer_container)
        self.viewer_layout.setContentsMargins(0, 0, 0, 0)
        
        # Create placeholder label
        self.placeholder = QLabel("Initializing 3D viewer...")
        self.placeholder.setAlignment(Qt.AlignCenter)
        self.viewer_layout.addWidget(self.placeholder)
        
        self.layout.addWidget(self.viewer_container)
        
        # Create drop zone overlay (shown when no model loaded)
        self.drop_overlay = DropZoneOverlay()
        self.drop_overlay.file_dropped.connect(self._on_file_dropped)
        self.drop_overlay.click_to_upload.connect(self._on_click_upload)
        self.drop_overlay.error_occurred.connect(self._on_drop_error)
        self.layout.addWidget(self.drop_overlay)
        
        # Show overlay on top initially
        self.layout.setCurrentWidget(self.drop_overlay)
        
        # Plotter will be initialized later
        self.plotter = None
        self.current_mesh = None
        self.current_actor = None  # Track the mesh actor to remove it specifically
        self._initialized = False
        self._model_loaded = False
        
        debug_print("STLViewerWidget: Basic initialization complete, QtInteractor will be created after window is shown")
        logger.info("STLViewerWidget: Basic initialization complete, QtInteractor will be created after window is shown")
    
    def showEvent(self, event):
        """Initialize QtInteractor when widget is first shown."""
        super().showEvent(event)
        
        if not self._initialized:
            debug_print("STLViewerWidget: showEvent triggered, scheduling QtInteractor initialization...")
            logger.info("STLViewerWidget: showEvent triggered, scheduling QtInteractor initialization...")
            # Use QTimer with longer delay to ensure window is fully rendered
            # Process events multiple times to ensure everything is ready
            QTimer.singleShot(500, self._initialize_plotter)
    
    def _initialize_plotter(self):
        """Initialize the PyVista plotter (called after window is shown)."""
        if self._initialized:
            return
        
        # Process events before starting initialization
        from PyQt5.QtWidgets import QApplication
        QApplication.processEvents()
        
        # Ensure widget is visible and has a window
        if not self.isVisible():
            debug_print("STLViewerWidget: Widget not visible yet, retrying in 200ms...")
            logger.warning("STLViewerWidget: Widget not visible yet, retrying...")
            QTimer.singleShot(200, self._initialize_plotter)
            return
        
        # Check if widget has a valid window handle
        if not self.window().isVisible():
            debug_print("STLViewerWidget: Parent window not visible yet, retrying in 200ms...")
            logger.warning("STLViewerWidget: Parent window not visible yet, retrying...")
            QTimer.singleShot(200, self._initialize_plotter)
            return
            
        try:
            debug_print("STLViewerWidget: Starting plotter initialization...")
            logger.info("STLViewerWidget: Starting plotter initialization...")
            logger.info(f"STLViewerWidget: PyVista version: {pv.__version__}")
            debug_print(f"STLViewerWidget: PyVista version: {pv.__version__}")
            debug_print(f"STLViewerWidget: Widget visible: {self.isVisible()}, Window visible: {self.window().isVisible()}")
            logger.info(f"STLViewerWidget: Widget visible: {self.isVisible()}, Window visible: {self.window().isVisible()}")
            safe_flush(sys.stderr)
            
            debug_print("STLViewerWidget: Creating QtInteractor (this may take a moment)...")
            logger.info("STLViewerWidget: Creating QtInteractor (this may take a moment)...")
            safe_flush(sys.stderr)
            
            # Process events multiple times before creating QtInteractor
            for _ in range(3):
                QApplication.processEvents()
            
            # Initialize PyVista plotter with Qt backend
            # This might block, but we've processed events first
            self.plotter = QtInteractor(self.viewer_container)
            
            debug_print("STLViewerWidget: QtInteractor created successfully")
            logger.info("STLViewerWidget: QtInteractor created successfully")
            safe_flush(sys.stderr)
            
            # Process events after creation
            QApplication.processEvents()
            
            # Process events after QtInteractor creation
            QApplication.processEvents()
            
            # Remove placeholder
            self.viewer_layout.removeWidget(self.placeholder)
            self.placeholder.deleteLater()
            QApplication.processEvents()
            
            # Add plotter to viewer container layout
            self.viewer_layout.addWidget(self.plotter.interactor)
            QApplication.processEvents()
            
            debug_print("STLViewerWidget: Configuring plotter settings...")
            logger.info("STLViewerWidget: Configuring plotter settings...")
            safe_flush(sys.stderr)
            
            # Configure plotter for smooth interaction with large models
            try:
                self.plotter.enable_anti_aliasing()
                debug_print("STLViewerWidget: Anti-aliasing enabled")
                logger.info("STLViewerWidget: Anti-aliasing enabled")
            except Exception as e:
                debug_print(f"STLViewerWidget: Could not enable anti-aliasing: {e}")
                logger.warning(f"STLViewerWidget: Could not enable anti-aliasing: {e}")
            
            # Shadows disabled to reduce excessive shadowing while preserving 3D look
            # try:
            #     self.plotter.enable_shadows()
            #     debug_print("STLViewerWidget: Shadows enabled")
            #     logger.info("STLViewerWidget: Shadows enabled")
            # except Exception as e:
            #     debug_print(f"STLViewerWidget: Could not enable shadows: {e}")
            #     logger.warning(f"STLViewerWidget: Could not enable shadows: {e}")
            
            debug_print("STLViewerWidget: Initializing empty scene...")
            logger.info("STLViewerWidget: Initializing empty scene...")
            safe_flush(sys.stderr)
            
            # Initialize with empty scene - do this carefully to avoid hangs
            try:
                self.plotter.background_color = 'white'
                QApplication.processEvents()
                debug_print("STLViewerWidget: Background color set")
                logger.info("STLViewerWidget: Background color set")
            except Exception as e:
                debug_print(f"STLViewerWidget: Could not set background color: {e}")
                logger.warning(f"STLViewerWidget: Could not set background color: {e}")
            
            QApplication.processEvents()
            
            # Add axes - this can sometimes hang, so do it carefully
            try:
                debug_print("STLViewerWidget: Adding axes...")
                logger.info("STLViewerWidget: Adding axes...")
                safe_flush(sys.stderr)
                self.plotter.add_axes()
                QApplication.processEvents()
                debug_print("STLViewerWidget: Axes added")
                logger.info("STLViewerWidget: Axes added")
            except Exception as e:
                debug_print(f"STLViewerWidget: Could not add axes: {e}")
                logger.warning(f"STLViewerWidget: Could not add axes: {e}")
                # Continue anyway - axes are optional
            
            QApplication.processEvents()
            
            # Don't force render immediately - let it render naturally
            # The render() call can block on macOS
            debug_print("STLViewerWidget: Scene configured, will render on next event loop")
            logger.info("STLViewerWidget: Scene configured, will render on next event loop")
            
            debug_print("STLViewerWidget: Empty scene initialized")
            logger.info("STLViewerWidget: Empty scene initialized")
            
            self._initialized = True
            debug_print("STLViewerWidget: QtInteractor initialization complete")
            logger.info("STLViewerWidget: QtInteractor initialization complete")
            safe_flush(sys.stderr)
            
            # Final event processing - multiple times to ensure UI updates
            for _ in range(5):
                QApplication.processEvents()
            
            # Update the widget to ensure it's visible
            self.update()
            self.repaint()
            QApplication.processEvents()
            
            debug_print("STLViewerWidget: All initialization complete, widget should be functional")
            logger.info("STLViewerWidget: All initialization complete, widget should be functional")
            safe_flush(sys.stderr)
            
        except Exception as e:
            debug_print(f"STLViewerWidget: ERROR during plotter initialization: {e}")
            logger.error(f"STLViewerWidget: Error during plotter initialization: {e}", exc_info=True)
            # Update placeholder to show error
            if self.placeholder:
                self.placeholder.setText(f"Error initializing 3D viewer: {str(e)}")
            import traceback
            traceback.print_exc()
            # Don't raise - allow the app to continue
    
    def load_stl(self, file_path):
        """
        Load and display an STL file.
        
        Args:
            file_path (str): Path to the STL file
            
        Returns:
            bool: True if successful, False otherwise
        """
        logger.info(f"load_stl: Starting to load STL file: {file_path}")
        
        # Wait for plotter to be initialized if not ready
        if not self._initialized or self.plotter is None:
            logger.warning("load_stl: Plotter not initialized yet, waiting...")
            # Wait a bit for initialization
            from PyQt5.QtWidgets import QApplication
            for _ in range(50):  # Wait up to 5 seconds
                QApplication.processEvents()
                if self._initialized and self.plotter is not None:
                    break
                import time
                time.sleep(0.1)
            
            if not self._initialized or self.plotter is None:
                logger.error("load_stl: Plotter failed to initialize")
                return False
        
        try:
            # Remove previous mesh actor if it exists (instead of clearing everything)
            if self.current_actor is not None:
                logger.info("load_stl: Removing previous mesh actor...")
                try:
                    self.plotter.remove_actor(self.current_actor)
                    logger.info("load_stl: Previous mesh actor removed")
                except Exception as e:
                    logger.warning(f"load_stl: Could not remove actor, using clear: {e}")
                    # Fallback to clear if remove_actor fails
                    self.plotter.clear()
                    self.plotter.add_axes()
                    # Re-enable settings after clear
                    try:
                        self.plotter.enable_anti_aliasing()
                    except:
                        pass
                    # Shadows disabled to reduce excessive shadowing
                    # try:
                    #     self.plotter.enable_shadows()
                    # except:
                    #     pass
            elif self.current_mesh is not None:
                # If we have a mesh but no actor reference, use clear
                logger.info("load_stl: Clearing previous mesh...")
                self.plotter.clear()
                self.plotter.add_axes()
            
            logger.info("load_stl: Reading STL file with PyVista...")
            # Read STL file using PyVista
            mesh = pv.read(file_path)
            logger.info(f"load_stl: STL file read successfully. Mesh info: {mesh}")
            
            # Check if this is the first mesh load (before we update current_mesh)
            is_first_load = (self.current_mesh is None)
            
            # Store the original mesh BEFORE processing for rendering
            # This ensures volume calculations use the unmodified mesh
            self.current_mesh = mesh.copy()
            
            # Prepare mesh for high-quality rendering (optional enhancements)
            # These steps are optional - if they fail, we'll use the original mesh
            logger.info("load_stl: Preparing mesh for rendering...")
            render_mesh = mesh  # Start with original mesh
            
            # Try to triangulate if needed (optional enhancement)
            try:
                if not render_mesh.is_all_triangles():
                    logger.info("load_stl: Triangulating mesh...")
                    render_mesh = render_mesh.triangulate()
                    logger.info("load_stl: Mesh triangulated successfully")
            except Exception as e:
                logger.warning(f"load_stl: Could not triangulate mesh: {e}, using original mesh")
                render_mesh = mesh  # Fallback to original mesh
            
            # Try to compute normals for proper smooth shading (optional enhancement)
            # This is critical for Windows rendering to show detail correctly
            logger.info("load_stl: Computing mesh normals...")
            try:
                render_mesh.compute_normals(inplace=True, point_normals=True, cell_normals=False)
                logger.info("load_stl: Mesh normals computed successfully")
            except Exception as e:
                logger.warning(f"load_stl: Could not compute normals: {e}, continuing anyway")
            
            logger.info("load_stl: Adding mesh to plotter...")
            # Add mesh to plotter with consistent rendering parameters
            # Store the actor reference so we can remove it later
            # Use the processed mesh for rendering (with normals and triangulation if successful)
            self.current_actor = self.plotter.add_mesh(
                render_mesh,
                color='lightblue',
                show_edges=False,
                smooth_shading=False,
                ambient=0.7,  # Increased for less shadowing
                diffuse=0.4,  # Reduced to balance with higher ambient
                specular=0.2,  # Reduced for less harsh highlights
                specular_power=20  # Reduced for softer specular
            )
            logger.info("load_stl: Mesh added to plotter")
            
            # Ensure axes are present (only add on first load)
            if is_first_load:
                self.plotter.add_axes()
            
            logger.info("load_stl: Resetting camera...")
            # Fit view to show entire model
            self.plotter.reset_camera()
            
            # Force renderer update to ensure consistent appearance
            # Explicitly render on Windows to ensure detail is visible
            from PyQt5.QtWidgets import QApplication
            import sys
            try:
                # Force render update, especially important on Windows
                self.plotter.render()
                logger.info("load_stl: Renderer updated explicitly")
            except Exception as e:
                logger.warning(f"load_stl: Could not force render: {e}, continuing anyway")
            
            QApplication.processEvents()
            logger.info("load_stl: STL file loaded successfully")
            
            # Hide overlay when model is loaded
            self._model_loaded = True
            self._show_overlay(False)

            return True
            
        except Exception as e:
            logger.error(f"load_stl: Error loading STL file: {e}", exc_info=True)
            return False
    
    def clear_viewer(self):
        """Clear the 3D viewer."""
        if self.plotter is None:
            return
        logger.info("clear_viewer: Clearing viewer...")
        # Remove mesh actor if it exists
        if self.current_actor is not None:
            try:
                self.plotter.remove_actor(self.current_actor)
            except:
                pass
        self.plotter.clear()
        self.plotter.add_axes()
        self.current_mesh = None
        self.current_actor = None
        self._model_loaded = False
        # Show overlay again when cleared
        self._show_overlay(True)
        logger.info("clear_viewer: Viewer cleared")
    
    def _on_file_dropped(self, file_path: str):
        """Handle file dropped on overlay."""
        self.file_dropped.emit(file_path)
    
    def _on_click_upload(self):
        """Handle click on overlay to upload."""
        self.click_to_upload.emit()
    
    def _on_drop_error(self, error_msg: str):
        """Handle drop error."""
        self.drop_error.emit(error_msg)
    
    def _show_overlay(self, show: bool):
        """Show or hide the drop zone overlay."""
        if show:
            self.drop_overlay.show()
            self.drop_overlay.raise_()
        else:
            self.drop_overlay.hide()
