"""
3D Viewer Widget using PyVista for STL file visualization.
"""
import sys
import os
import logging
import pyvista as pv
from pyvistaqt import QtInteractor
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt5.QtCore import Qt, QTimer

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
    
    def __init__(self, parent=None):
        debug_print("STLViewerWidget: Initializing...")
        logger.info("STLViewerWidget: Initializing...")
        super().__init__(parent)
        debug_print("STLViewerWidget: Parent initialized")
        logger.info("STLViewerWidget: Parent initialized")
        
        # Set up layout first (empty for now)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        # Create placeholder label
        self.placeholder = QLabel("Initializing 3D viewer...")
        self.placeholder.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.placeholder)
        
        # Plotter will be initialized later
        self.plotter = None
        self.current_mesh = None
        self.current_actor = None  # Track the mesh actor to remove it specifically
        self._initialized = False
        
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
            self.plotter = QtInteractor(self)
            
            debug_print("STLViewerWidget: QtInteractor created successfully")
            logger.info("STLViewerWidget: QtInteractor created successfully")
            safe_flush(sys.stderr)
            
            # Process events after creation
            QApplication.processEvents()
            
            # Process events after QtInteractor creation
            QApplication.processEvents()
            
            # Remove placeholder
            self.layout.removeWidget(self.placeholder)
            self.placeholder.deleteLater()
            QApplication.processEvents()
            
            # Add plotter to layout
            self.layout.addWidget(self.plotter.interactor)
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
            
            try:
                self.plotter.enable_shadows()
                debug_print("STLViewerWidget: Shadows enabled")
                logger.info("STLViewerWidget: Shadows enabled")
            except Exception as e:
                debug_print(f"STLViewerWidget: Could not enable shadows: {e}")
                logger.warning(f"STLViewerWidget: Could not enable shadows: {e}")
            
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
                    try:
                        self.plotter.enable_shadows()
                    except:
                        pass
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
            
            # Store the original mesh BEFORE adding to plotter
            # This ensures volume calculations use the unmodified mesh
            # (plotter.add_mesh may modify the mesh for rendering)
            self.current_mesh = mesh.copy()
            
            logger.info("load_stl: Adding mesh to plotter...")
            # Add mesh to plotter with consistent rendering parameters
            # Store the actor reference so we can remove it later
            # Use the original mesh for rendering (okay to modify for display)
            self.current_actor = self.plotter.add_mesh(
                mesh,
                color='lightblue',
                show_edges=False,
                smooth_shading=True,
                ambient=0.3,
                diffuse=0.6,
                specular=0.3,
                specular_power=30
            )
            logger.info("load_stl: Mesh added to plotter")
            
            # Ensure axes are present (only add on first load)
            if is_first_load:
                self.plotter.add_axes()
            
            logger.info("load_stl: Resetting camera...")
            # Fit view to show entire model
            self.plotter.reset_camera()
            
            # Force renderer update to ensure consistent appearance
            from PyQt5.QtWidgets import QApplication
            QApplication.processEvents()
            logger.info("load_stl: STL file loaded successfully")
            
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
        logger.info("clear_viewer: Viewer cleared")
