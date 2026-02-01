"""
STEP file loader for converting STEP files to PyVista meshes.
Uses meshio as primary loader, with cadquery as fallback.
"""
import logging
import sys
import os
import traceback
from pathlib import Path
import pyvista as pv

logger = logging.getLogger(__name__)


def _log_windows_info(logger_instance, context=""):
    """Log Windows-specific system information for debugging."""
    if sys.platform != 'win32':
        return
    
    logger_instance.info(f"=== Windows System Information {context} ===")
    logger_instance.info(f"Python version: {sys.version}")
    logger_instance.info(f"Python executable: {sys.executable}")
    logger_instance.info(f"Platform: {sys.platform}")
    logger_instance.info(f"Architecture: {sys.maxsize > 2**32 and '64-bit' or '32-bit'}")
    logger_instance.info(f"Frozen (PyInstaller): {getattr(sys, 'frozen', False)}")
    if getattr(sys, 'frozen', False):
        logger_instance.info(f"MEIPASS: {getattr(sys, '_MEIPASS', 'N/A')}")
    
    # Log PATH environment variable
    path_env = os.environ.get('PATH', '')
    path_dirs = path_env.split(os.pathsep) if path_env else []
    logger_instance.info(f"PATH contains {len(path_dirs)} directories")
    if path_dirs:
        logger_instance.info(f"First 5 PATH entries: {path_dirs[:5]}")
    
    # Log sys.path
    logger_instance.info(f"sys.path contains {len(sys.path)} entries")
    if sys.path:
        logger_instance.info(f"First 5 sys.path entries: {sys.path[:5]}")
    
    # Try to find OCP installation
    try:
        import site
        site_packages = site.getsitepackages()
        logger_instance.info(f"Site packages locations: {site_packages}")
        
        # Look for OCP in site-packages
        for site_pkg in site_packages:
            ocp_path = Path(site_pkg) / 'OCP'
            if ocp_path.exists():
                logger_instance.info(f"Found OCP at: {ocp_path}")
                # Look for DLLs
                dll_files = list(ocp_path.glob('*.dll'))
                if dll_files:
                    logger_instance.info(f"Found {len(dll_files)} DLL files in OCP directory")
                    logger_instance.info(f"DLL files: {[f.name for f in dll_files[:10]]}")
                break
    except Exception as e:
        logger_instance.warning(f"Could not inspect site packages: {e}")
    
    logger_instance.info("=== End Windows System Information ===")


class StepLoader:
    """Handles loading STEP files and converting them to PyVista meshes."""
    
    @staticmethod
    def load_with_meshio(file_path):
        """
        Load STEP file using meshio library.
        
        Args:
            file_path (str): Path to the STEP file
            
        Returns:
            pyvista.PolyData: PyVista mesh object, or None if failed
        """
        try:
            if sys.platform == 'win32':
                logger.info("StepLoader: [Windows] Before meshio import")
                logger.info(f"StepLoader: [Windows] sys.path before import: {len(sys.path)} entries")
            
            import meshio
            
            if sys.platform == 'win32':
                logger.info("StepLoader: [Windows] meshio imported successfully")
                try:
                    logger.info(f"StepLoader: [Windows] meshio version: {meshio.__version__ if hasattr(meshio, '__version__') else 'unknown'}")
                    logger.info(f"StepLoader: [Windows] meshio location: {meshio.__file__ if hasattr(meshio, '__file__') else 'unknown'}")
                except Exception as e:
                    logger.warning(f"StepLoader: [Windows] Could not get meshio info: {e}")
            
            logger.info(f"StepLoader: Attempting to load STEP file with meshio: {file_path}")
            
            if sys.platform == 'win32':
                logger.info(f"StepLoader: [Windows] Calling meshio.read() with file: {file_path}")
            
            meshio_mesh = meshio.read(file_path)
            
            if sys.platform == 'win32':
                logger.info("StepLoader: [Windows] meshio.read() completed successfully")
            
            # Convert meshio mesh to PyVista
            # meshio stores points and cells separately
            points = meshio_mesh.points
            
            # Find the first cell block that contains triangles or other 3D cells
            cells = None
            cell_type = None
            
            for cell_block in meshio_mesh.cells:
                # Look for triangle cells first
                if cell_block.type == "triangle":
                    cells = cell_block.data
                    cell_type = "triangle"
                    break
                # Fallback to other 3D cell types
                elif cell_block.type in ["tetra", "hexahedron", "wedge", "pyramid"]:
                    cells = cell_block.data
                    cell_type = cell_block.type
                    break
            
            if cells is None:
                # Try to find any cell block
                if len(meshio_mesh.cells) > 0:
                    cells = meshio_mesh.cells[0].data
                    cell_type = meshio_mesh.cells[0].type
                    logger.warning(f"StepLoader: Using cell type {cell_type} (may not be optimal)")
                else:
                    logger.error("StepLoader: No cells found in meshio mesh")
                    return None
            
            # Create PyVista mesh
            # For triangle cells, use PolyData
            if cell_type == "triangle":
                pv_mesh = pv.PolyData(points, cells)
            else:
                # For other cell types, create UnstructuredGrid
                # Convert to PolyData by extracting surface
                unstructured = pv.UnstructuredGrid(cells, cell_type, points)
                pv_mesh = unstructured.extract_surface()
            
            logger.info(f"StepLoader: Successfully loaded STEP file with meshio. Points: {len(points)}, Cells: {len(cells)}")
            return pv_mesh
            
        except ImportError as e:
            if sys.platform == 'win32':
                logger.error("StepLoader: [Windows] meshio import failed")
                logger.error(f"StepLoader: [Windows] ImportError type: {type(e).__name__}")
                logger.error(f"StepLoader: [Windows] ImportError message: {str(e)}")
                logger.error(f"StepLoader: [Windows] Full traceback:", exc_info=True)
            logger.error("StepLoader: meshio library not available")
            return None
        except Exception as e:
            if sys.platform == 'win32':
                logger.warning("StepLoader: [Windows] meshio.read() failed")
                logger.warning(f"StepLoader: [Windows] Exception type: {type(e).__name__}")
                logger.warning(f"StepLoader: [Windows] Exception message: {str(e)}")
                logger.warning(f"StepLoader: [Windows] Full traceback:", exc_info=True)
            logger.warning(f"StepLoader: Failed to load with meshio: {e}")
            return None
    
    @staticmethod
    def load_with_cadquery(file_path):
        """
        Load STEP file using cadquery library (fallback).
        
        Args:
            file_path (str): Path to the STEP file
            
        Returns:
            pyvista.PolyData: PyVista mesh object, or None if failed
        """
        try:
            if sys.platform == 'win32':
                logger.info("StepLoader: [Windows] Before cadquery import")
                logger.info(f"StepLoader: [Windows] sys.path before import: {len(sys.path)} entries")
            
            import cadquery as cq
            
            if sys.platform == 'win32':
                logger.info("StepLoader: [Windows] cadquery imported successfully")
                try:
                    logger.info(f"StepLoader: [Windows] cadquery version: {cq.__version__ if hasattr(cq, '__version__') else 'unknown'}")
                    logger.info(f"StepLoader: [Windows] cadquery location: {cq.__file__ if hasattr(cq, '__file__') else 'unknown'}")
                except Exception as e:
                    logger.warning(f"StepLoader: [Windows] Could not get cadquery info: {e}")
            
            logger.info(f"StepLoader: Attempting to load STEP file with cadquery: {file_path}")
            
            if sys.platform == 'win32':
                logger.info(f"StepLoader: [Windows] Calling cq.importers.importStep() with file: {file_path}")
            
            # Import STEP file
            result = cq.importers.importStep(file_path)
            
            if sys.platform == 'win32':
                logger.info("StepLoader: [Windows] cq.importers.importStep() completed successfully")
                logger.info(f"StepLoader: [Windows] Result type: {type(result)}")
                logger.info(f"StepLoader: [Windows] Result has 'val' attribute: {hasattr(result, 'val')}")
            
            # Convert cadquery object to mesh
            # cadquery objects need to be tessellated (triangulated) first
            if hasattr(result, 'val'):
                # If it's a Workplane, get the solid
                if hasattr(result.val, 'objects'):
                    # Multiple objects - take first one
                    solid = result.val.objects[0] if len(result.val.objects) > 0 else result.val
                else:
                    solid = result.val
            else:
                solid = result
            
            # Tessellate the solid to get triangles
            # cadquery uses OCP (OpenCASCADE Python) internally
            try:
                if sys.platform == 'win32':
                    logger.info("StepLoader: [Windows] Before OCP module imports")
                    logger.info(f"StepLoader: [Windows] sys.path before OCP import: {len(sys.path)} entries")
                
                from OCP.BRepMesh import BRepMesh_IncrementalMesh
                
                if sys.platform == 'win32':
                    logger.info("StepLoader: [Windows] BRepMesh_IncrementalMesh imported successfully")
                
                from OCP.TopTools import TopTools_ListOfShape
                from OCP.TopAbs import TopAbs_FACE
                from OCP.TopExp import TopExp_Explorer
                from OCP.BRep import BRep_Tool
                from OCP.TopLoc import TopLoc_Location
                from OCP.Poly import Poly_Triangulation
                from OCP.TColgp import TColgp_Array1OfPnt
                
                if sys.platform == 'win32':
                    logger.info("StepLoader: [Windows] All OCP modules imported successfully")
                    try:
                        import OCP
                        logger.info(f"StepLoader: [Windows] OCP location: {OCP.__file__ if hasattr(OCP, '__file__') else 'unknown'}")
                    except Exception as e:
                        logger.warning(f"StepLoader: [Windows] Could not get OCP info: {e}")
                
                # Get the underlying OCP shape
                if sys.platform == 'win32':
                    logger.info("StepLoader: [Windows] Extracting OCP shape from solid")
                    logger.info(f"StepLoader: [Windows] solid type: {type(solid)}")
                    logger.info(f"StepLoader: [Windows] solid has 'wrapped' attribute: {hasattr(solid, 'wrapped')}")
                
                ocp_shape = solid.wrapped if hasattr(solid, 'wrapped') else solid
                
                if sys.platform == 'win32':
                    logger.info(f"StepLoader: [Windows] ocp_shape type: {type(ocp_shape)}")
                    logger.info(f"StepLoader: [Windows] ocp_shape is None: {ocp_shape is None}")
                
                # Mesh the shape
                if sys.platform == 'win32':
                    logger.info("StepLoader: [Windows] Before BRepMesh_IncrementalMesh creation")
                    logger.info(f"StepLoader: [Windows] Parameters: ocp_shape type={type(ocp_shape)}, deflection=0.1")
                
                mesh_tool = BRepMesh_IncrementalMesh(ocp_shape, 0.1)  # 0.1 is deflection
                
                if sys.platform == 'win32':
                    logger.info("StepLoader: [Windows] BRepMesh_IncrementalMesh created successfully")
                    logger.info("StepLoader: [Windows] Calling mesh_tool.Perform()")
                
                mesh_tool.Perform()
                
                if sys.platform == 'win32':
                    logger.info("StepLoader: [Windows] mesh_tool.Perform() completed successfully")
                
                # Extract triangles from faces
                if sys.platform == 'win32':
                    logger.info("StepLoader: [Windows] Starting triangle extraction from faces")
                
                points_list = []
                faces_list = []
                point_index = 0
                
                if sys.platform == 'win32':
                    logger.info("StepLoader: [Windows] Creating TopExp_Explorer")
                
                explorer = TopExp_Explorer(ocp_shape, TopAbs_FACE)
                
                if sys.platform == 'win32':
                    logger.info("StepLoader: [Windows] TopExp_Explorer created successfully")
                    face_count = 0
                
                while explorer.More():
                    if sys.platform == 'win32':
                        face_count += 1
                        if face_count == 1:
                            logger.info("StepLoader: [Windows] Processing first face")
                    
                    face = explorer.Current()
                    
                    if sys.platform == 'win32' and face_count == 1:
                        logger.info(f"StepLoader: [Windows] face type: {type(face)}")
                    
                    location = TopLoc_Location()
                    
                    if sys.platform == 'win32' and face_count == 1:
                        logger.info("StepLoader: [Windows] Calling BRep_Tool.Triangulation()")
                    
                    triangulation = BRep_Tool.Triangulation(face, location)
                    
                    if sys.platform == 'win32' and face_count == 1:
                        logger.info(f"StepLoader: [Windows] triangulation result: {triangulation is not None}")
                    
                    if triangulation:
                        # Get points
                        nodes = triangulation.Nodes()
                        num_nodes = nodes.Length()
                        face_points = []
                        
                        for i in range(1, num_nodes + 1):
                            node = nodes.Value(i)
                            face_points.append([node.X(), node.Y(), node.Z()])
                            points_list.append([node.X(), node.Y(), node.Z()])
                        
                        # Get triangles
                        triangles = triangulation.Triangles()
                        num_triangles = triangles.Length()
                        
                        for i in range(1, num_triangles + 1):
                            triangle = triangles.Value(i)
                            # Triangle indices are 1-based, convert to 0-based
                            idx1 = triangle.Value(1) - 1 + point_index
                            idx2 = triangle.Value(2) - 1 + point_index
                            idx3 = triangle.Value(3) - 1 + point_index
                            faces_list.append([3, idx1, idx2, idx3])
                        
                        point_index += num_nodes
                    
                    explorer.Next()
                
                if len(points_list) == 0:
                    logger.error("StepLoader: No triangles extracted from cadquery mesh")
                    return None
                
                # Create PyVista mesh
                import numpy as np
                points_array = np.array(points_list)
                faces_array = np.array(faces_list, dtype=np.int32)
                
                pv_mesh = pv.PolyData(points_array, faces_array)
                
                logger.info(f"StepLoader: Successfully loaded STEP file with cadquery. Points: {len(points_array)}, Faces: {len(faces_array)}")
                return pv_mesh
                
            except Exception as e:
                if sys.platform == 'win32':
                    logger.error("StepLoader: [Windows] Exception during OCP mesh extraction")
                    logger.error(f"StepLoader: [Windows] Exception type: {type(e).__name__}")
                    logger.error(f"StepLoader: [Windows] Exception message: {str(e)}")
                    logger.error(f"StepLoader: [Windows] Full traceback:", exc_info=True)
                    # Log variable states
                    try:
                        logger.error(f"StepLoader: [Windows] solid type at error: {type(solid)}")
                        logger.error(f"StepLoader: [Windows] solid has 'wrapped': {hasattr(solid, 'wrapped')}")
                        if hasattr(solid, 'wrapped'):
                            logger.error(f"StepLoader: [Windows] solid.wrapped type: {type(solid.wrapped)}")
                    except:
                        pass
                
                logger.warning(f"StepLoader: Failed to extract mesh from cadquery object: {e}")
                # Fallback: try to export to STL and read back
                if sys.platform == 'win32':
                    logger.info("StepLoader: [Windows] Attempting STL export fallback")
                
                try:
                    import tempfile
                    import os
                    with tempfile.NamedTemporaryFile(suffix='.stl', delete=False) as tmp:
                        tmp_path = tmp.name
                    
                    if sys.platform == 'win32':
                        logger.info(f"StepLoader: [Windows] Temporary STL path: {tmp_path}")
                        logger.info("StepLoader: [Windows] Calling cq.exporters.export()")
                    
                    cq.exporters.export(result, tmp_path)
                    
                    if sys.platform == 'win32':
                        logger.info("StepLoader: [Windows] STL export successful, reading with PyVista")
                        logger.info(f"StepLoader: [Windows] Temporary file exists: {os.path.exists(tmp_path)}")
                        if os.path.exists(tmp_path):
                            logger.info(f"StepLoader: [Windows] Temporary file size: {os.path.getsize(tmp_path)} bytes")
                    
                    pv_mesh = pv.read(tmp_path)
                    os.unlink(tmp_path)
                    logger.info("StepLoader: Successfully loaded via STL export fallback")
                    return pv_mesh
                except Exception as e2:
                    if sys.platform == 'win32':
                        logger.error("StepLoader: [Windows] STL export fallback failed")
                        logger.error(f"StepLoader: [Windows] Exception type: {type(e2).__name__}")
                        logger.error(f"StepLoader: [Windows] Exception message: {str(e2)}")
                        logger.error(f"StepLoader: [Windows] Full traceback:", exc_info=True)
                    logger.error(f"StepLoader: STL export fallback also failed: {e2}")
                    return None
            
        except ImportError as e:
            if sys.platform == 'win32':
                logger.error("StepLoader: [Windows] cadquery import failed")
                logger.error(f"StepLoader: [Windows] ImportError type: {type(e).__name__}")
                logger.error(f"StepLoader: [Windows] ImportError message: {str(e)}")
                logger.error(f"StepLoader: [Windows] Full traceback:", exc_info=True)
            logger.error("StepLoader: cadquery library not available")
            return None
        except Exception as e:
            if sys.platform == 'win32':
                logger.error("StepLoader: [Windows] Exception during cadquery STEP loading")
                logger.error(f"StepLoader: [Windows] Exception type: {type(e).__name__}")
                logger.error(f"StepLoader: [Windows] Exception message: {str(e)}")
                logger.error(f"StepLoader: [Windows] Full traceback:", exc_info=True)
            logger.warning(f"StepLoader: Failed to load with cadquery: {e}")
            return None
    
    @staticmethod
    def load_step(file_path):
        """
        Load STEP file using meshio first, then cadquery as fallback.
        
        Args:
            file_path (str): Path to the STEP file
            
        Returns:
            pyvista.PolyData: PyVista mesh object, or None if both methods fail
            
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file cannot be loaded by either method
        """
        import os
        
        # Log Windows system information at start
        if sys.platform == 'win32':
            _log_windows_info(logger, "at STEP loading start")
            logger.info(f"StepLoader: Loading STEP file on Windows: {file_path}")
            logger.info(f"StepLoader: File path type: {type(file_path)}")
            logger.info(f"StepLoader: File path absolute: {os.path.abspath(file_path) if file_path else 'N/A'}")
        
        if not os.path.exists(file_path):
            if sys.platform == 'win32':
                logger.error(f"StepLoader: File not found on Windows: {file_path}")
                logger.error(f"StepLoader: Absolute path: {os.path.abspath(file_path) if file_path else 'N/A'}")
                logger.error(f"StepLoader: Current working directory: {os.getcwd()}")
            raise FileNotFoundError(f"STEP file not found: {file_path}")
        
        logger.info(f"StepLoader: Loading STEP file: {file_path}")
        
        if sys.platform == 'win32':
            file_size = os.path.getsize(file_path)
            logger.info(f"StepLoader: File size: {file_size} bytes")
            logger.info(f"StepLoader: File readable: {os.access(file_path, os.R_OK)}")
        
        # Try meshio first (lighter, faster)
        mesh = StepLoader.load_with_meshio(file_path)
        if mesh is not None:
            return mesh
        
        # Fallback to cadquery
        logger.info("StepLoader: meshio failed, trying cadquery fallback...")
        mesh = StepLoader.load_with_cadquery(file_path)
        if mesh is not None:
            return mesh
        
        # Both methods failed
        error_msg = (
            f"Failed to load STEP file: {file_path}\n\n"
            "Both meshio and cadquery failed to load the file.\n"
            "Please ensure:\n"
            "1. The file is a valid STEP format\n"
            "2. meshio and cadquery are properly installed\n"
            "3. The file is not corrupted"
        )
        logger.error(f"StepLoader: {error_msg}")
        raise ValueError(error_msg)
