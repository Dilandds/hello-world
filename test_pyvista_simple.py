"""
Minimal PyVista test - just PyVista without Qt
"""
import pyvista as pv

def test_pyvista():
    print("Testing PyVista...")
    print(f"PyVista version: {pv.__version__}")
    
    # Create a simple plotter (not Qt-based)
    plotter = pv.Plotter()
    print("Plotter created")
    
    # Add a simple sphere
    sphere = pv.Sphere()
    plotter.add_mesh(sphere)
    print("Mesh added")
    
    print("Showing plotter (this will open a window)...")
    plotter.show()
    print("If you see a 3D window, PyVista works!")

if __name__ == "__main__":
    test_pyvista()
