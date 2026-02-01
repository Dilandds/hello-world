"""
IGES file loader for converting IGES files to PyVista meshes.
Uses OCP (OpenCASCADE Python) via cadquery for loading.
"""
import logging
import pyvista as pv
import numpy as np

logger = logging.getLogger(__name__)


class IgesLoader:
    """Handles loading IGES files and converting them to PyVista meshes."""
    
    @staticmethod
    def load_with_ocp(file_path):
        """
        Load IGES file using OCP (OpenCASCADE Python) library.
        
        Args:
            file_path (str): Path to the IGES file
            
        Returns:
            pyvista.PolyData: PyVista mesh object, or None if failed
        """
        try:
            from OCP.IGESControl import IGESControl_Reader
            from OCP.IFSelect import IFSelect_ReturnStatus
            from OCP.BRepMesh import BRepMesh_IncrementalMesh
            from OCP.TopAbs import TopAbs_FACE
            from OCP.TopExp import TopExp_Explorer
            from OCP.BRep import BRep_Tool
            from OCP.TopLoc import TopLoc_Location
            from OCP.TopoDS import TopoDS
            
            logger.info(f"IgesLoader: Attempting to load IGES file with OCP: {file_path}")
            
            # Create IGES reader
            reader = IGESControl_Reader()
            
            # Read the IGES file
            status = reader.ReadFile(file_path)
            
            if status != IFSelect_ReturnStatus.IFSelect_RetDone:
                logger.error(f"IgesLoader: Failed to read IGES file. Status: {status}")
                return None
            
            # Transfer roots (get all shapes from the file)
            reader.TransferRoots()
            
            # Get the number of shapes
            nb_shapes = reader.NbShapes()
            if nb_shapes == 0:
                logger.error("IgesLoader: No shapes found in IGES file")
                return None
            
            logger.info(f"IgesLoader: Found {nb_shapes} shape(s) in IGES file")
            
            # Collect all points and faces from all shapes
            all_points = []
            all_faces = []
            point_offset = 0
            
            # Process each shape
            for i in range(1, nb_shapes + 1):
                shape = reader.Shape(i)
                
                if shape.IsNull():
                    logger.warning(f"IgesLoader: Shape {i} is null, skipping")
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
                            # Triangle() returns a Poly_Triangle object with Value(1), Value(2), Value(3) methods
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
                    logger.debug(f"IgesLoader: Extracted {len(points_list)} points, {len(faces_list)} faces from shape {i}")
            
            if len(all_points) == 0:
                logger.error("IgesLoader: No triangles extracted from IGES file")
                return None
            
            # Create PyVista mesh
            points_array = np.array(all_points, dtype=np.float64)
            faces_array = np.array(all_faces, dtype=np.int32)
            
            pv_mesh = pv.PolyData(points_array, faces_array)
            
            logger.info(f"IgesLoader: Successfully loaded IGES file with OCP. Points: {len(points_array)}, Faces: {len(faces_array)}")
            return pv_mesh
            
        except ImportError:
            logger.error("IgesLoader: OCP library not available (install cadquery)")
            return None
        except Exception as e:
            logger.warning(f"IgesLoader: Failed to load with OCP: {e}", exc_info=True)
            return None
    
    @staticmethod
    def load_iges(file_path):
        """
        Load IGES file using OCP.
        
        Args:
            file_path (str): Path to the IGES file
            
        Returns:
            pyvista.PolyData: PyVista mesh object, or None if failed
            
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file cannot be loaded
        """
        import os
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"IGES file not found: {file_path}")
        
        logger.info(f"IgesLoader: Loading IGES file: {file_path}")
        
        # Try OCP
        mesh = IgesLoader.load_with_ocp(file_path)
        if mesh is not None:
            return mesh
        
        # Loading failed
        error_msg = (
            f"Failed to load IGES file: {file_path}\n\n"
            "OCP failed to load the file.\n"
            "Please ensure:\n"
            "1. The file is a valid IGES format\n"
            "2. cadquery is properly installed (pip install cadquery)\n"
            "3. The file is not corrupted"
        )
        logger.error(f"IgesLoader: {error_msg}")
        raise ValueError(error_msg)
