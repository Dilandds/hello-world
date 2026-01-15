"""
Minimal PyQt6 test - just a basic window
"""
import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel

def test_basic_window():
    print("Creating QApplication...")
    app = QApplication(sys.argv)
    print("QApplication created")
    
    print("Creating window...")
    window = QMainWindow()
    window.setWindowTitle("Test Window")
    window.setGeometry(100, 100, 400, 300)
    
    label = QLabel("If you see this, PyQt6 works!", window)
    label.move(50, 50)
    
    print("Showing window...")
    window.show()
    print("Window shown - check if it appears")
    
    print("Starting event loop...")
    sys.exit(app.exec())

if __name__ == "__main__":
    test_basic_window()
