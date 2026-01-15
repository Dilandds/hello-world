"""
Alternative 3D Viewer Widget using PyVista offscreen rendering.
This is a fallback for when QtInteractor doesn't work on macOS.
"""
import sys
import os
import logging
import numpy as np
import pyvista as pv
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QPixmap, QImage
import io

logger = logging.getLogger(__name__)

# Print to stderr for immediate visibility
def debug_print(msg):
    print(f"[DEBUG] {msg}", file=sys.stderr)
    sys.stderr.flush()


class STLViewerWidgetOffscreen(QWidget):
    """PyVista-based 3D viewer widget using offscreen rendering."""
    
    def __init__(self, parent=None):
        debug_print("STLViewerWidgetOffscreen: Initializing...")
        logger.info("STLViewerWidgetOffscreen: Initializing...")
        super().__init__(parent)
        
        # Set PyVista to offscreen mode
        try:
            pv.OFF_SCREEN = True
            # Try to start xvfb if available (Linux), but don't fail if not available (macOS)
            try:
                pv.start_xvfb()
            except:
                pass  # xvfb not available (e.g., on macOS), that's okay
        except Exception as e:
            debug_print(f"STLViewerWidgetOffscreen: Could not set offscreen mode: {e}")
            logger.warning(f"STLViewerWidgetOffscreen: Could not set offscreen mode: {e}")
        
        # Set up layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        # Create image label for displaying rendered scene
        self.image_label = QLabel("Initializing 3D viewer...")
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setMinimumSize(400, 400)
        self.image_label.setStyleSheet("background-color: white; border: 1px solid #ccc;")
        self.layout.addWidget(self.image_label)
        
        # Create control buttons
        controls_layout = QHBoxLayout()
        self.rotate_left_btn = QPushButton("← Rotate")
        self.rotate_right_btn = QPushButton("Rotate →")
        self.zoom_in_btn = QPushButton("Zoom +")
        self.zoom_out_btn = QPushButton("Zoom -")
        self.reset_btn = QPushButton("Reset View")
        
        controls_layout.addWidget(self.rotate_left_btn)
        controls_layout.addWidget(self.rotate_right_btn)
        controls_layout.addWidget(self.zoom_in_btn)
        controls_layout.addWidget(self.zoom_out_btn)
        controls_layout.addWidget(self.reset_btn)
        controls_layout.addStretch()
        
        self.layout.addLayout(controls_layout)
        
        # Connect buttons
        self.rotate_left_btn.clicked.connect(lambda: self.rotate_view(-15))
        self.rotate_right_btn.clicked.connect(lambda: self.rotate_view(15))
        self.zoom_in_btn.clicked.connect(lambda: self.zoom_view(1.2))
        self.zoom_out_btn.clicked.connect(lambda: self.zoom_view(0.8))
        self.reset_btn.clicked.connect(self.reset_view)
        
        # Initialize plotter
        self.plotter = None
        self.current_mesh = None
        self.rotation_angle = 0
        
        # Initialize plotter
        self._initialize_plotter()
        
        debug_print("STLViewerWidgetOffscreen: Initialization complete")
        logger.info("STLViewerWidgetOffscreen: Initialization complete")
    
    def _initialize_plotter(self):
        """Initialize the offscreen plotter."""
        try:
            debug_print("STLViewerWidgetOffscreen: Creating offscreen plotter...")
            logger.info("STLViewerWidgetOffscreen: Creating offscreen plotter...")
            
            # Create offscreen plotter
            self.plotter = pv.Plotter(off_screen=True, window_size=[800, 600])
            self.plotter.background_color = 'white'
            
            debug_print("STLViewerWidgetOffscreen: Offscreen plotter created")
            logger.info("STLViewerWidgetOffscreen: Offscreen plotter created")
            
            # Render empty scene
            self._render_scene()
            
        except Exception as e:
            debug_print(f"STLViewerWidgetOffscreen: ERROR during initialization: {e}")
            logger.error(f"STLViewerWidgetOffscreen: Error during initialization: {e}", exc_info=True)
            self.image_label.setText(f"Error initializing 3D viewer: {str(e)}")
    
    def _render_scene(self):
        """Render the current scene to an image and display it."""
        if self.plotter is None:
            return
        
        try:
            # Render to numpy array
            image = self.plotter.screenshot()
            
            # Convert numpy array to QPixmap
            height, width, channel = image.shape
            bytes_per_line = 3 * width
            q_image = QImage(image.data, width, height, bytes_per_line, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(q_image)
            
            # Scale to fit label while maintaining aspect ratio
            label_size = self.image_label.size()
            if label_size.width() > 0 and label_size.height() > 0:
                pixmap = pixmap.scaled(label_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            
            # Display in label
            self.image_label.setPixmap(pixmap)
            self.image_label.setText("")  # Clear text
            
        except Exception as e:
            debug_print(f"STLViewerWidgetOffscreen: Error rendering scene: {e}")
            logger.error(f"STLViewerWidgetOffscreen: Error rendering scene: {e}", exc_info=True)
    
    def load_stl(self, file_path):
        """
        Load and display an STL file.
        
        Args:
            file_path (str): Path to the STL file
            
        Returns:
            bool: True if successful, False otherwise
        """
        logger.info(f"load_stl: Starting to load STL file: {file_path}")
        try:
            # Clear previous mesh
            if self.current_mesh is not None:
                self.plotter.clear()
            
            logger.info("load_stl: Reading STL file with PyVista...")
            # Read STL file using PyVista
            mesh = pv.read(file_path)
            logger.info(f"load_stl: STL file read successfully. Mesh info: {mesh}")
            
            logger.info("load_stl: Adding mesh to plotter...")
            # Add mesh to plotter
            self.plotter.add_mesh(
                mesh,
                color='lightblue',
                show_edges=False,
                smooth_shading=True,
                ambient=0.3,
                diffuse=0.6,
                specular=0.3,
                specular_power=30
            )
            
            # Add axes
            self.plotter.add_axes()
            
            logger.info("load_stl: Resetting camera...")
            # Fit view to show entire model
            self.plotter.reset_camera()
            
            # Update reference
            self.current_mesh = mesh
            self.rotation_angle = 0
            
            # Render and display
            self._render_scene()
            
            logger.info("load_stl: STL file loaded successfully")
            return True
            
        except Exception as e:
            logger.error(f"load_stl: Error loading STL file: {e}", exc_info=True)
            return False
    
    def rotate_view(self, angle):
        """Rotate the view by the specified angle."""
        if self.plotter is None or self.current_mesh is None:
            return
        
        self.rotation_angle += angle
        self.plotter.camera_position = self.plotter.camera_position
        self.plotter.camera.azimuth(angle)
        self._render_scene()
    
    def zoom_view(self, factor):
        """Zoom the view by the specified factor."""
        if self.plotter is None or self.current_mesh is None:
            return
        
        self.plotter.camera.zoom(factor)
        self._render_scene()
    
    def reset_view(self):
        """Reset the view to default."""
        if self.plotter is None or self.current_mesh is None:
            return
        
        self.plotter.reset_camera()
        self.rotation_angle = 0
        self._render_scene()
    
    def clear_viewer(self):
        """Clear the 3D viewer."""
        if self.plotter is None:
            return
        logger.info("clear_viewer: Clearing viewer...")
        self.plotter.clear()
        self.plotter.add_axes()
        self.current_mesh = None
        self.rotation_angle = 0
        self._render_scene()
        logger.info("clear_viewer: Viewer cleared")
    
    def resizeEvent(self, event):
        """Handle resize events to update the displayed image."""
        super().resizeEvent(event)
        if self.plotter is not None and self.current_mesh is not None:
            # Re-render on resize
            QTimer.singleShot(100, self._render_scene)
