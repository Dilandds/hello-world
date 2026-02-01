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
                logger.info(f"StepLoader: [Windows] Explicitly specifying file_format='step' to avoid auto-detection issues")
            
            # Explicitly specify format to avoid auto-detection issues with .stp/.STEP extensions
            meshio_mesh = meshio.read(file_path, file_format='step')
            
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
    def _setup_windows_casadi_dlls():
        """
        Setup Windows DLL paths for casadi (multiple strategies).
        Returns True if setup was successful, False otherwise.
        """
        if sys.platform != 'win32':
            return True  # Not Windows, no setup needed
        
        try:
            import site
            import importlib.util
            
            # Strategy 1: Try to find casadi in sys.modules first
            casadi_path = None
            try:
                if 'casadi' in sys.modules:
                    import casadi
                    if hasattr(casadi, '__file__'):
                        casadi_path = Path(casadi.__file__).parent
                        logger.info(f"StepLoader: [Windows] casadi already in sys.modules, location: {casadi_path}")
            except ImportError:
                pass
            
            # Strategy 2: Try to find casadi via importlib
            if casadi_path is None:
                try:
                    spec = importlib.util.find_spec('casadi')
                    if spec and spec.origin:
                        casadi_path = Path(spec.origin).parent
                        logger.info(f"StepLoader: [Windows] Found casadi spec origin: {casadi_path}")
                except Exception as e:
                    logger.debug(f"StepLoader: [Windows] Could not find casadi via importlib: {e}")
            
            # Strategy 3: Search sys.path
            if casadi_path is None:
                for path_entry in sys.path:
                    casadi_candidate = Path(path_entry) / 'casadi'
                    if casadi_candidate.exists() and (casadi_candidate / 'casadi.py').exists():
                        casadi_path = casadi_candidate
                        logger.info(f"StepLoader: [Windows] Found casadi in sys.path: {casadi_path}")
                        break
            
            # Strategy 4: Search in PyInstaller MEIPASS
            if casadi_path is None and getattr(sys, 'frozen', False):
                meipass = getattr(sys, '_MEIPASS', None)
                if meipass:
                    casadi_candidate = Path(meipass) / 'casadi'
                    if casadi_candidate.exists():
                        casadi_path = casadi_candidate
                        logger.info(f"StepLoader: [Windows] Found casadi in MEIPASS: {casadi_path}")
            
            # If found, add DLL directory to search paths
            if casadi_path and casadi_path.exists():
                # Look for DLL files in casadi directory
                dll_files = list(casadi_path.glob('*.dll'))
                if dll_files:
                    logger.info(f"StepLoader: [Windows] Found {len(dll_files)} DLL files in casadi directory")
                    
                    casadi_str = str(casadi_path)
                    
                    # Strategy A: Add to PATH environment variable
                    current_path = os.environ.get('PATH', '')
                    if casadi_str not in current_path:
                        os.environ['PATH'] = casadi_str + os.pathsep + current_path
                        logger.info(f"StepLoader: [Windows] Added casadi directory to PATH: {casadi_str}")
                    
                    # Strategy B: Add to DLL search directories (Python 3.8+)
                    if hasattr(os, 'add_dll_directory'):
                        try:
                            os.add_dll_directory(casadi_str)
                            logger.info(f"StepLoader: [Windows] Added casadi directory to DLL search path via os.add_dll_directory()")
                        except Exception as e:
                            logger.warning(f"StepLoader: [Windows] Could not add casadi to DLL search path: {e}")
                    
                    # Strategy C: Try to preload DLLs explicitly
                    try:
                        import ctypes
                        for dll_file in dll_files[:5]:  # Try first 5 DLLs
                            try:
                                ctypes.CDLL(str(dll_file))
                                logger.debug(f"StepLoader: [Windows] Preloaded DLL: {dll_file.name}")
                            except Exception as e:
                                logger.debug(f"StepLoader: [Windows] Could not preload {dll_file.name}: {e}")
                    except Exception as e:
                        logger.debug(f"StepLoader: [Windows] Could not preload DLLs: {e}")
                    
                    return True
                else:
                    logger.warning(f"StepLoader: [Windows] casadi directory found but no DLL files: {casadi_path}")
            else:
                logger.warning(f"StepLoader: [Windows] Could not find casadi installation directory")
            
            return False
                        
        except Exception as e:
            logger.warning(f"StepLoader: [Windows] Error setting up casadi DLL paths: {e}", exc_info=True)
            return False
    
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
                
                # Setup casadi DLL paths before importing cadquery
                dll_setup_success = StepLoader._setup_windows_casadi_dlls()
                if not dll_setup_success:
                    logger.warning(f"StepLoader: [Windows] DLL setup had issues, but will attempt cadquery import anyway")
            
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
                    
                    face_shape = explorer.Current()
                    
                    if sys.platform == 'win32' and face_count == 1:
                        logger.info(f"StepLoader: [Windows] face_shape type: {type(face_shape)}")
                    
                    # Cast TopoDS_Shape to TopoDS_Face
                    face = TopoDS.Face_s(face_shape)
                    location = TopLoc_Location()
                    
                    if sys.platform == 'win32' and face_count == 1:
                        logger.info("StepLoader: [Windows] Calling BRep_Tool.Triangulation_s()")
                    
                    triangulation = BRep_Tool.Triangulation_s(face, location)
                    
                    if sys.platform == 'win32' and face_count == 1:
                        logger.info(f"StepLoader: [Windows] triangulation result: {triangulation is not None}")
                    
                    if triangulation:
                        # Get number of nodes
                        num_nodes = triangulation.NbNodes()
                        
                        # Get each node individually
                        for i in range(1, num_nodes + 1):
                            node = triangulation.Node(i)
                            points_list.append([node.X(), node.Y(), node.Z()])
                        
                        # Get number of triangles
                        num_triangles = triangulation.NbTriangles()
                        
                        # Get each triangle individually
                        for i in range(1, num_triangles + 1):
                            triangle = triangulation.Triangle(i)
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
    def load_with_ocp_direct(file_path):
        """
        Load STEP file using OCP (OpenCASCADE Python) directly, without cadquery.
        This is a fallback when cadquery fails due to DLL issues.
        
        Args:
            file_path (str): Path to the STEP file
            
        Returns:
            pyvista.PolyData: PyVista mesh object, or None if failed
        """
        try:
            logger.info(f"StepLoader: Attempting to load STEP file with OCP directly: {file_path}")
            
            from OCP.STEPControl import STEPControl_Reader
            from OCP.IFSelect import IFSelect_ReturnStatus
            from OCP.BRepMesh import BRepMesh_IncrementalMesh
            from OCP.TopAbs import TopAbs_FACE
            from OCP.TopExp import TopExp_Explorer
            from OCP.BRep import BRep_Tool
            from OCP.TopLoc import TopLoc_Location
            from OCP.TopoDS import TopoDS
            import numpy as np
            
            # Create STEP reader
            reader = STEPControl_Reader()
            
            # Read the STEP file
            status = reader.ReadFile(file_path)
            
            if status != IFSelect_ReturnStatus.IFSelect_RetDone:
                logger.error(f"StepLoader: Failed to read STEP file. Status: {status}")
                return None
            
            # Transfer roots (get all shapes from the file)
            reader.TransferRoots()
            
            # Get the number of shapes
            nb_shapes = reader.NbShapes()
            if nb_shapes == 0:
                logger.error("StepLoader: No shapes found in STEP file")
                return None
            
            logger.info(f"StepLoader: Found {nb_shapes} shape(s) in STEP file")
            
            # Collect all points and faces from all shapes
            all_points = []
            all_faces = []
            point_offset = 0
            
            # Process each shape
            for i in range(1, nb_shapes + 1):
                shape = reader.Shape(i)
                
                if shape.IsNull():
                    logger.warning(f"StepLoader: Shape {i} is null, skipping")
                    continue
                
                # Mesh the shape
                mesh_tool = BRepMesh_IncrementalMesh(shape, 0.1)  # 0.1 is deflection
                mesh_tool.Perform()
                
                # Extract triangles from faces
                points_list = []
                faces_list = []
                point_index = 0
                
                explorer = TopExp_Explorer(shape, TopAbs_FACE)
                while explorer.More():
                    face_shape = explorer.Current()
                    face = TopoDS.Face_s(face_shape)  # Cast TopoDS_Shape to TopoDS_Face
                    location = TopLoc_Location()
                    triangulation = BRep_Tool.Triangulation_s(face, location)
                    
                    if triangulation:
                        # Get number of nodes
                        num_nodes = triangulation.NbNodes()
                        
                        # Get each node individually
                        for j in range(1, num_nodes + 1):
                            node = triangulation.Node(j)
                            points_list.append([node.X(), node.Y(), node.Z()])
                        
                        # Get number of triangles
                        num_triangles = triangulation.NbTriangles()
                        
                        # Get each triangle individually
                        for j in range(1, num_triangles + 1):
                            triangle = triangulation.Triangle(j)
                            # Triangle indices are 1-based, convert to 0-based
                            idx1 = triangle.Value(1) - 1 + point_index
                            idx2 = triangle.Value(2) - 1 + point_index
                            idx3 = triangle.Value(3) - 1 + point_index
                            faces_list.append([3, idx1, idx2, idx3])
                        
                        point_index += num_nodes
                    
                    explorer.Next()
                
                if len(points_list) > 0:
                    # Add points
                    all_points.extend(points_list)
                    # Add faces with global point offset
                    for face in faces_list:
                        # Create new face array with offset indices
                        offset_face = [face[0], face[1] + point_offset, face[2] + point_offset, face[3] + point_offset]
                        all_faces.append(offset_face)
                    point_offset += len(points_list)
                    logger.debug(f"StepLoader: Extracted {len(points_list)} points, {len(faces_list)} faces from shape {i}")
            
            if len(all_points) == 0:
                logger.error("StepLoader: No triangles extracted from STEP file")
                return None
            
            # Create PyVista mesh
            points_array = np.array(all_points, dtype=np.float64)
            faces_array = np.array(all_faces, dtype=np.int32)
            
            pv_mesh = pv.PolyData(points_array, faces_array)
            
            logger.info(f"StepLoader: Successfully loaded STEP file with OCP directly. Points: {len(points_array)}, Faces: {len(faces_array)}")
            return pv_mesh
            
        except ImportError as e:
            logger.error(f"StepLoader: OCP library not available: {e}")
            return None
        except Exception as e:
            logger.warning(f"StepLoader: Failed to load with OCP directly: {e}", exc_info=True)
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
        
        # Try multiple fallback approaches in order:
        # 1. meshio (lightweight, but may not support STEP)
        # 2. cadquery (requires casadi DLLs on Windows)
        # 3. OCP directly (bypasses cadquery, avoids casadi dependency)
        
        # Try meshio first (lighter, faster, but may not support STEP)
        logger.info("StepLoader: Attempting to load with meshio...")
        mesh = StepLoader.load_with_meshio(file_path)
        if mesh is not None:
            logger.info("StepLoader: Successfully loaded with meshio")
            return mesh
        
        # Fallback to cadquery (may fail on Windows due to DLL issues)
        logger.info("StepLoader: meshio failed, trying cadquery fallback...")
        mesh = StepLoader.load_with_cadquery(file_path)
        if mesh is not None:
            logger.info("StepLoader: Successfully loaded with cadquery")
            return mesh
        
        # Fallback to OCP directly (bypasses cadquery, avoids casadi dependency)
        logger.info("StepLoader: cadquery failed, trying OCP direct fallback...")
        mesh = StepLoader.load_with_ocp_direct(file_path)
        if mesh is not None:
            logger.info("StepLoader: Successfully loaded with OCP directly")
            return mesh
        
        # All methods failed
        error_msg = (
            f"Failed to load STEP file: {file_path}\n\n"
            "All loading methods failed:\n"
            "1. meshio - does not support STEP format\n"
            "2. cadquery - failed (possibly due to DLL loading issues on Windows)\n"
            "3. OCP direct - failed\n\n"
            "Please ensure:\n"
            "1. The file is a valid STEP format\n"
            "2. OCP/cadquery libraries are properly installed\n"
            "3. The file is not corrupted\n"
            "4. On Windows: casadi DLLs are accessible"
        )
        logger.error(f"StepLoader: {error_msg}")
        raise ValueError(error_msg)
