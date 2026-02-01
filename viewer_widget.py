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
        
        # No placeholder - drop overlay handles empty state
        
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
            
            # Process events after QtInteractor creation
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
            import traceback
            traceback.print_exc()
            # Don't raise - allow the app to continue
    
    def load_stl(self, file_path):
        """
        Load and display an STL or STEP file.
        
        Args:
            file_path (str): Path to the STL or STEP file
            
        Returns:
            bool: True if successful, False otherwise
        """
        logger.info(f"load_stl: Starting to load file: {file_path}")
        
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
                    # Ensure renderer settings are preserved after removing actor
                    self._restore_renderer_settings()
                except Exception as e:
                    logger.warning(f"load_stl: Could not remove actor, using clear: {e}")
                    # Fallback to clear if remove_actor fails
                    self.plotter.clear()
                    self.plotter.add_axes()
                    # Restore renderer settings after clear
                    self._restore_renderer_settings()
            elif self.current_mesh is not None:
                # If we have a mesh but no actor reference, use clear
                logger.info("load_stl: Clearing previous mesh...")
                self.plotter.clear()
                self.plotter.add_axes()
                # Restore renderer settings after clear
                self._restore_renderer_settings()
            
            # Detect file format and load accordingly
            file_ext = file_path.lower()
            if file_ext.endswith('.step') or file_ext.endswith('.stp'):
                logger.info("load_stl: Detected STEP file, loading with StepLoader...")
                from core.step_loader import StepLoader
                try:
                    mesh = StepLoader.load_step(file_path)
                    logger.info(f"load_stl: STEP file loaded successfully. Mesh info: {mesh}")
                except Exception as e:
                    logger.error(f"load_stl: Failed to load STEP file: {e}", exc_info=True)
                    raise
            elif file_ext.endswith('.3dm'):
                logger.info("load_stl: Detected 3DM file, loading with Rhino3dmLoader...")
                from core.rhino3dm_loader import Rhino3dmLoader
                try:
                    mesh = Rhino3dmLoader.load_3dm(file_path)
                    logger.info(f"load_stl: 3DM file loaded successfully. Mesh info: {mesh}")
                except Exception as e:
                    logger.error(f"load_stl: Failed to load 3DM file: {e}", exc_info=True)
                    raise
            elif file_ext.endswith('.obj'):
                logger.info("load_stl: Detected OBJ file, attempting to load...")
                mesh = None
                load_error = None
                
                # Try PyVista first (fastest)
                try:
                    logger.info("load_stl: Trying PyVista OBJ reader...")
                    mesh = pv.read(file_path)
                    logger.info(f"load_stl: PyVista read completed. Mesh info: {mesh}")
                    
                    # Check if mesh is valid
                    if mesh is not None and mesh.n_points > 0:
                        logger.info("load_stl: PyVista successfully loaded OBJ file")
                    else:
                        logger.warning("load_stl: PyVista loaded empty mesh, trying meshio fallback...")
                        mesh = None  # Will trigger fallback
                except Exception as e:
                    logger.warning(f"load_stl: PyVista failed to load OBJ: {e}, trying meshio fallback...")
                    load_error = str(e)
                    mesh = None
                
                # Fallback to meshio if PyVista failed or produced empty mesh
                meshio_error = None
                if mesh is None or mesh.n_points == 0:
                    try:
                        logger.info("load_stl: Trying meshio OBJ reader...")
                        import meshio
                        meshio_mesh = meshio.read(file_path)
                        logger.info(f"load_stl: meshio read completed. Points: {len(meshio_mesh.points)}, Cells: {len(meshio_mesh.cells)}")
                        
                        # Convert meshio mesh to PyVista
                        if len(meshio_mesh.points) == 0:
                            raise ValueError("meshio loaded OBJ but found no points")
                        
                        points = meshio_mesh.points
                        
                        # Find triangle cells (most common for OBJ)
                        cells = None
                        cell_type = None
                        for cell_block in meshio_mesh.cells:
                            if cell_block.type == "triangle":
                                cells = cell_block.data
                                cell_type = "triangle"
                                break
                        
                        # If no triangles, try other cell types
                        if cells is None:
                            if len(meshio_mesh.cells) > 0:
                                cell_block = meshio_mesh.cells[0]
                                cells = cell_block.data
                                cell_type = cell_block.type
                                logger.warning(f"load_stl: Using cell type {cell_type} (not triangles)")
                            else:
                                raise ValueError("meshio loaded OBJ but found no cells")
                        
                        # Create PyVista mesh
                        if cell_type == "triangle":
                            mesh = pv.PolyData(points, cells)
                        else:
                            # For other cell types, create UnstructuredGrid and extract surface
                            unstructured = pv.UnstructuredGrid(cells, cell_type, points)
                            mesh = unstructured.extract_surface()
                        
                        logger.info(f"load_stl: Converted meshio mesh to PyVista. Points: {mesh.n_points}, Cells: {mesh.n_cells}")
                    except ImportError:
                        meshio_error = "meshio is not available"
                        logger.warning(f"load_stl: {meshio_error}, will try custom parser...")
                    except ValueError as e:
                        error_str = str(e)
                        # Check if this is a texture coordinate mismatch error
                        if "len(points)" in error_str and "point_data" in error_str:
                            meshio_error = f"meshio texture coordinate mismatch: {error_str}"
                            logger.warning(f"load_stl: {meshio_error}, will try custom parser...")
                        else:
                            # Other ValueError from meshio - re-raise
                            meshio_error = error_str
                            raise
                    except Exception as e:
                        meshio_error = str(e)
                        logger.warning(f"load_stl: meshio failed: {meshio_error}, will try custom parser...")
                
                # Third fallback: custom OBJ parser for files with texture coordinate mismatches
                if (mesh is None or mesh.n_points == 0) and meshio_error:
                    try:
                        logger.info("load_stl: Trying custom OBJ parser (handles texture coordinate mismatches)...")
                        from core.obj_loader import ObjLoader
                        mesh = ObjLoader.load_obj(file_path)
                        logger.info(f"load_stl: Custom OBJ parser successfully loaded file. Points: {mesh.n_points}, Cells: {mesh.n_cells}")
                    except ImportError:
                        error_msg = "OBJ file could not be loaded. All loaders failed (PyVista, meshio, and custom parser unavailable)."
                        if load_error:
                            error_msg += f" PyVista error: {load_error}."
                        if meshio_error:
                            error_msg += f" meshio error: {meshio_error}."
                        logger.error(f"load_stl: {error_msg}")
                        raise ValueError(error_msg)
                    except Exception as e:
                        error_msg = "OBJ file could not be loaded with any available method (PyVista, meshio, or custom parser)."
                        if load_error:
                            error_msg += f" PyVista error: {load_error}."
                        if meshio_error:
                            error_msg += f" meshio error: {meshio_error}."
                        error_msg += f" Custom parser error: {str(e)}"
                        logger.error(f"load_stl: {error_msg}")
                        raise ValueError(error_msg)
                
                # Final validation
                if mesh is None or mesh.n_points == 0:
                    error_msg = "OBJ file loaded but contains no geometry (zero points). The file may be corrupted or in an unsupported format."
                    if load_error:
                        error_msg += f" Reader error: {load_error}"
                    logger.error(f"load_stl: {error_msg}")
                    raise ValueError(error_msg)
            elif file_ext.endswith('.iges') or file_ext.endswith('.igs'):
                logger.info("load_stl: Detected IGES file, loading with IgesLoader...")
                from core.iges_loader import IgesLoader
                try:
                    mesh = IgesLoader.load_iges(file_path)
                    logger.info(f"load_stl: IGES file loaded successfully. Mesh info: {mesh}")
                except Exception as e:
                    logger.error(f"load_stl: Failed to load IGES file: {e}", exc_info=True)
                    raise
            else:
                logger.info("load_stl: Reading STL file with PyVista...")
                # Read STL file using PyVista
                mesh = pv.read(file_path)
                logger.info(f"load_stl: STL file read successfully. Mesh info: {mesh}")
            
            # Check if this is the first mesh load (before we update current_mesh)
            is_first_load = (self.current_mesh is None)
            
            # Validate mesh is not empty before proceeding
            if mesh is None:
                error_msg = "Failed to load mesh: file returned None. The file may be corrupted or in an unsupported format."
                logger.error(f"load_stl: {error_msg}")
                raise ValueError(error_msg)
            
            if mesh.n_points == 0:
                error_msg = f"Loaded mesh contains no geometry (zero points). The file may be corrupted, empty, or in an unsupported format."
                logger.error(f"load_stl: {error_msg}")
                raise ValueError(error_msg)
            
            logger.info(f"load_stl: Mesh validated - {mesh.n_points} points, {mesh.n_cells} cells")
            
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
            # Ensure renderer settings are active before adding mesh (preserves quality when uploading)
            self._restore_renderer_settings()
            
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
            
            # Ensure renderer settings are still active after adding mesh
            # This preserves visual quality when uploading files multiple times
            self._restore_renderer_settings()
            
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
        
        # Restore renderer settings after clearing
        self._restore_renderer_settings()
        
        self.current_mesh = None
        self.current_actor = None
        self._model_loaded = False
        # Show overlay again when cleared
        self._show_overlay(True)
        logger.info("clear_viewer: Viewer cleared")
    
    def _restore_renderer_settings(self):
        """Restore renderer settings after clearing to maintain visual quality."""
        if self.plotter is None:
            return
        
        try:
            # Re-enable anti-aliasing for sharpness
            self.plotter.enable_anti_aliasing()
            logger.info("_restore_renderer_settings: Anti-aliasing restored")
        except Exception as e:
            logger.warning(f"_restore_renderer_settings: Could not restore anti-aliasing: {e}")
        
        # Restore lighting settings for consistent visual quality
        try:
            # Remove existing lights and add fresh default lighting
            self.plotter.remove_all_lights()
            # Add a light kit for balanced illumination (like initial state)
            light = pv.Light(position=(1, 1, 1), light_type='scene light')
            light.intensity = 1.0
            self.plotter.add_light(light)
            
            # Add fill light from opposite side for softer shadows
            fill_light = pv.Light(position=(-1, -0.5, 0.5), light_type='scene light')
            fill_light.intensity = 0.4
            self.plotter.add_light(fill_light)
            
            logger.info("_restore_renderer_settings: Lighting restored")
        except Exception as e:
            logger.warning(f"_restore_renderer_settings: Could not restore lighting: {e}")
        
        # Preserve background color
        try:
            self.plotter.background_color = 'white'
            logger.debug("_restore_renderer_settings: Background color restored")
        except Exception as e:
            logger.debug(f"_restore_renderer_settings: Could not restore background color: {e}")
        
        # Force renderer update to ensure settings take effect
        try:
            self.plotter.render()
            logger.debug("_restore_renderer_settings: Renderer updated")
        except Exception as e:
            logger.debug(f"_restore_renderer_settings: Could not force render: {e}")
    
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
