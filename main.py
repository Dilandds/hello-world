"""
Main entry point for the STL 3D Viewer application.
"""
import sys
import logging
import os

# Set OpenGL environment variables for macOS compatibility
# These help with PyVista/VTK rendering issues on macOS
os.environ.setdefault('MESA_GL_VERSION_OVERRIDE', '3.3')
os.environ.setdefault('VTK_USE_OSMESA', '0')  # Try hardware rendering first
# Uncomment below if hardware rendering fails:
# os.environ['VTK_USE_OSMESA'] = '1'  # Force software rendering

# Configure logging FIRST, before any other imports
log_file = os.path.join(os.path.dirname(__file__), 'app_debug.log')
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ],
    force=True  # Override any existing configuration
)

logger = logging.getLogger(__name__)

# Print immediately to stdout (before Qt might interfere)
print("=" * 50, file=sys.stderr)
print("STL Viewer: Starting application...", file=sys.stderr)
print(f"Log file: {log_file}", file=sys.stderr)
print("=" * 50, file=sys.stderr)
sys.stderr.flush()

from PyQt5.QtWidgets import QApplication, QMessageBox, QDialog
from PyQt5.QtCore import QTimer
from stl_viewer import STLViewerWindow
from core.license_validator import is_license_valid_stored
from ui.license_dialog import LicenseDialog
from ui.styles import get_global_stylesheet


def main():
    """Initialize and run the STL viewer application."""
    print("=" * 50, file=sys.stderr)
    print("Starting STL 3D Viewer Application", file=sys.stderr)
    print("=" * 50, file=sys.stderr)
    sys.stderr.flush()
    
    logger.info("=" * 50)
    logger.info("Starting STL 3D Viewer Application")
    logger.info("=" * 50)
    
    try:
        print("Step 1: Creating QApplication...", file=sys.stderr)
        sys.stderr.flush()
        logger.info("Step 1: Creating QApplication...")
        app = QApplication(sys.argv)
        print("✓ QApplication created successfully", file=sys.stderr)
        sys.stderr.flush()
        logger.info("✓ QApplication created successfully")
        
        # Apply global stylesheet early to ensure QMessageBox dialogs are styled
        app.setStyleSheet(get_global_stylesheet())
        print("✓ Global stylesheet applied", file=sys.stderr)
        sys.stderr.flush()
        logger.info("✓ Global stylesheet applied")
        
        print("Step 2: Setting application properties...", file=sys.stderr)
        sys.stderr.flush()
        logger.info("Step 2: Setting application properties...")
        app.setApplicationName("STL 3D Viewer")
        app.setOrganizationName("Jewellery Viewer")
        print("✓ Application properties set", file=sys.stderr)
        sys.stderr.flush()
        logger.info("✓ Application properties set")
        
        # Step 2.5: Check license
        print("Step 2.5: Checking license...", file=sys.stderr)
        sys.stderr.flush()
        logger.info("Step 2.5: Checking license...")
        
        if not is_license_valid_stored():
            print("License not valid, showing license dialog...", file=sys.stderr)
            sys.stderr.flush()
            logger.info("License not valid, showing license dialog...")
            
            license_dialog = LicenseDialog()
            if license_dialog.exec() != QDialog.Accepted:
                print("License dialog cancelled, exiting application", file=sys.stderr)
                sys.stderr.flush()
                logger.info("License dialog cancelled, exiting application")
                QMessageBox.information(
                    None,
                    "License Required",
                    "A valid license key is required to use this application.\n"
                    "The application will now exit."
                )
                return 0  # Exit application
            
            print("✓ License validated successfully", file=sys.stderr)
            sys.stderr.flush()
            logger.info("✓ License validated successfully")
        else:
            print("✓ Valid license found in cache", file=sys.stderr)
            sys.stderr.flush()
            logger.info("✓ Valid license found in cache")
        
        print("Step 3: Creating main window...", file=sys.stderr)
        sys.stderr.flush()
        logger.info("Step 3: Creating main window...")
        window = STLViewerWindow()
        print("✓ Main window created successfully", file=sys.stderr)
        sys.stderr.flush()
        logger.info("✓ Main window created successfully")
        
        print("Step 4: Showing window...", file=sys.stderr)
        sys.stderr.flush()
        logger.info("Step 4: Showing window...")
        window.show()
        
        # Process events to ensure window renders before QtInteractor initialization
        app.processEvents()
        
        # Ensure window is raised and activated (especially important on macOS)
        window.raise_()
        window.activateWindow()
        app.processEvents()
        
        print(f"✓ Window shown - Position: {window.pos()}, Size: {window.size()}, Visible: {window.isVisible()}", file=sys.stderr)
        sys.stderr.flush()
        logger.info(f"✓ Window shown - Position: {window.pos()}, Size: {window.size()}, Visible: {window.isVisible()}")
        
        # Give QtInteractor time to initialize (it will be triggered by showEvent)
        app.processEvents()
        
        print("Step 5: Starting event loop...", file=sys.stderr)
        sys.stderr.flush()
        logger.info("Step 5: Starting event loop...")
        # Run application event loop
        sys.exit(app.exec())
    except Exception as e:
        print(f"FATAL ERROR: {e}", file=sys.stderr)
        sys.stderr.flush()
        logger.error(f"Fatal error in main: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
