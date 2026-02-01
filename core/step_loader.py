"""
STEP file loader for converting STEP files to PyVista meshes.
Uses meshio as primary loader, with cadquery as fallback.
"""
import logging
import pyvista as pv

logger = logging.getLogger(__name__)


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
            import meshio
            
            logger.info(f"StepLoader: Attempting to load STEP file with meshio: {file_path}")
            meshio_mesh = meshio.read(file_path)
            
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
            
        except ImportError:
            logger.error("StepLoader: meshio library not available")
            return None
        except Exception as e:
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
            import cadquery as cq
            
            logger.info(f"StepLoader: Attempting to load STEP file with cadquery: {file_path}")
            
            # Import STEP file
            result = cq.importers.importStep(file_path)
            
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
                from OCP.BRepMesh import BRepMesh_IncrementalMesh
                from OCP.TopTools import TopTools_ListOfShape
                from OCP.TopAbs import TopAbs_FACE
                from OCP.TopExp import TopExp_Explorer
                from OCP.BRep import BRep_Tool
                from OCP.TopLoc import TopLoc_Location
                from OCP.Poly import Poly_Triangulation
                from OCP.TColgp import TColgp_Array1OfPnt
                
                # Get the underlying OCP shape
                ocp_shape = solid.wrapped if hasattr(solid, 'wrapped') else solid
                
                # Mesh the shape
                mesh_tool = BRepMesh_IncrementalMesh(ocp_shape, 0.1)  # 0.1 is deflection
                mesh_tool.Perform()
                
                # Extract triangles from faces
                points_list = []
                faces_list = []
                point_index = 0
                
                explorer = TopExp_Explorer(ocp_shape, TopAbs_FACE)
                while explorer.More():
                    face = explorer.Current()
                    location = TopLoc_Location()
                    triangulation = BRep_Tool.Triangulation(face, location)
                    
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
                logger.warning(f"StepLoader: Failed to extract mesh from cadquery object: {e}")
                # Fallback: try to export to STL and read back
                try:
                    import tempfile
                    import os
                    with tempfile.NamedTemporaryFile(suffix='.stl', delete=False) as tmp:
                        tmp_path = tmp.name
                    cq.exporters.export(result, tmp_path)
                    pv_mesh = pv.read(tmp_path)
                    os.unlink(tmp_path)
                    logger.info("StepLoader: Successfully loaded via STL export fallback")
                    return pv_mesh
                except Exception as e2:
                    logger.error(f"StepLoader: STL export fallback also failed: {e2}")
                    return None
            
        except ImportError:
            logger.error("StepLoader: cadquery library not available")
            return None
        except Exception as e:
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
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"STEP file not found: {file_path}")
        
        logger.info(f"StepLoader: Loading STEP file: {file_path}")
        
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
