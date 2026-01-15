"""
Minimal PyVista + PyQt6 test
"""
import sys
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_pyvista_qt():
    print("=" * 50)
    print("Testing PyVista + PyQt6 Integration")
    print("=" * 50)
    
    try:
        print("Step 1: Importing PyQt6...")
        from PyQt6.QtWidgets import QApplication, QMainWindow
        print("✓ PyQt6 imported")
        
        print("Step 2: Creating QApplication...")
        app = QApplication(sys.argv)
        print("✓ QApplication created")
        
        print("Step 3: Creating main window...")
        window = QMainWindow()
        window.setWindowTitle("PyVista Qt Test")
        window.setGeometry(100, 100, 800, 600)
        print("✓ Main window created")
        
        print("Step 4: Importing PyVista...")
        import pyvista as pv
        from pyvistaqt import QtInteractor
        print(f"✓ PyVista imported (version: {pv.__version__})")
        
        print("Step 5: Creating QtInteractor (THIS IS WHERE IT MIGHT HANG)...")
        plotter = QtInteractor(window)
        print("✓ QtInteractor created")
        
        print("Step 6: Setting up plotter...")
        plotter.background_color = 'white'
        plotter.add_axes()
        print("✓ Plotter configured")
        
        print("Step 7: Showing window...")
        window.show()
        print("✓ Window show() called")
        
        # Process events
        app.processEvents()
        print("✓ Events processed")
        
        print("Step 8: Starting event loop...")
        print("If window appears, the integration works!")
        sys.exit(app.exec())
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    test_pyvista_qt()
