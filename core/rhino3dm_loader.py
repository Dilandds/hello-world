"""
3DM (Rhino 3D) file loader for converting 3DM files to PyVista meshes.
Uses rhino3dm library for loading.
"""
import logging
import numpy as np
import pyvista as pv

logger = logging.getLogger(__name__)


class Rhino3dmLoader:
    """Handles loading 3DM files and converting them to PyVista meshes."""
    
    @staticmethod
    def load_with_rhino3dm(file_path):
        """
        Load 3DM file using rhino3dm library.
        
        Args:
            file_path (str): Path to the 3DM file
            
        Returns:
            pyvista.PolyData: PyVista mesh object, or None if failed
        """
        try:
            import rhino3dm
            
            logger.info(f"Rhino3dmLoader: Attempting to load 3DM file with rhino3dm: {file_path}")
            
            # Read the 3DM file
            model = rhino3dm.File3dm.Read(file_path)
            
            if model is None:
                logger.error("Rhino3dmLoader: Failed to read 3DM file - model is None")
                return None
            
            # Check if model has any objects
            if model.Objects is None or len(model.Objects) == 0:
                logger.error("Rhino3dmLoader: 3DM file contains no objects")
                return None
            
            logger.info(f"Rhino3dmLoader: Found {len(model.Objects)} objects in 3DM file")
            
            # Collect all meshes from the model
            all_points = []
            all_faces = []
            point_offset = 0
            
            # Track geometry types for debugging
            geometry_types = {}
            processed_count = 0
            failed_count = 0
            
            # Iterate through all objects in the model
            for obj in model.Objects:
                geometry = obj.Geometry
                
                if geometry is None:
                    logger.warning("Rhino3dmLoader: Object has no geometry, skipping")
                    continue
                
                # Track geometry type
                geom_type = type(geometry).__name__
                geometry_types[geom_type] = geometry_types.get(geom_type, 0) + 1
                
                # Handle mesh objects
                if isinstance(geometry, rhino3dm.Mesh):
                    mesh = geometry
                    # Get vertices
                    vertices = mesh.Vertices
                    if vertices is None or len(vertices) == 0:
                        continue
                    
                    # Extract points
                    mesh_points = []
                    for vertex in vertices:
                        mesh_points.append([vertex.X, vertex.Y, vertex.Z])
                    
                    # Get faces
                    faces = mesh.Faces
                    if faces is None or len(faces) == 0:
                        continue
                    
                    # Extract face indices
                    mesh_faces = []
                    for face in faces:
                        # Faces are tuples: (A, B, C, D) where triangles have C==D
                        is_quad = face[2] != face[3]
                        if is_quad:
                            # Quad face - split into two triangles
                            idx0 = face[0] + point_offset
                            idx1 = face[1] + point_offset
                            idx2 = face[2] + point_offset
                            idx3 = face[3] + point_offset
                            # First triangle
                            mesh_faces.append([3, idx0, idx1, idx2])
                            # Second triangle
                            mesh_faces.append([3, idx0, idx2, idx3])
                        else:
                            # Triangle face
                            idx0 = face[0] + point_offset
                            idx1 = face[1] + point_offset
                            idx2 = face[2] + point_offset
                            mesh_faces.append([3, idx0, idx1, idx2])
                    
                    all_points.extend(mesh_points)
                    all_faces.extend(mesh_faces)
                    point_offset += len(mesh_points)
                    processed_count += 1
                    logger.debug(f"Rhino3dmLoader: Processed Mesh object with {len(mesh_points)} points, {len(mesh_faces)} faces")
                
                # Handle Brep (boundary representation) objects - convert to mesh
                elif isinstance(geometry, rhino3dm.Brep):
                    try:
                        # Get meshes from each face of the Brep
                        # Use Render mesh type for best quality
                        brep_faces = geometry.Faces
                        if brep_faces is None or len(brep_faces) == 0:
                            logger.warning("Rhino3dmLoader: Brep has no faces")
                            failed_count += 1
                            continue
                        
                        face_meshes = []
                        for brep_face in brep_faces:
                            try:
                                # Get mesh from face - try Render first, then Any
                                mesh = brep_face.GetMesh(rhino3dm.MeshType.Render)
                                if mesh is None:
                                    mesh = brep_face.GetMesh(rhino3dm.MeshType.Any)
                                if mesh is not None:
                                    face_meshes.append(mesh)
                            except Exception as e:
                                logger.debug(f"Rhino3dmLoader: Could not get mesh from BrepFace: {e}")
                                continue
                        
                        if len(face_meshes) == 0:
                            logger.warning("Rhino3dmLoader: No meshes extracted from Brep faces")
                            failed_count += 1
                            continue
                        
                        # Combine all face meshes
                        for mesh in face_meshes:
                            vertices = mesh.Vertices
                            if vertices is None or len(vertices) == 0:
                                continue
                            
                            # Extract points
                            mesh_points = []
                            for vertex in vertices:
                                mesh_points.append([vertex.X, vertex.Y, vertex.Z])
                            
                            # Get faces
                            faces = mesh.Faces
                            if faces is None or len(faces) == 0:
                                continue
                            
                            # Extract face indices
                            mesh_faces = []
                            for face in faces:
                                # Faces are tuples: (A, B, C, D) where triangles have C==D
                                is_quad = face[2] != face[3]
                                if is_quad:
                                    # Quad face - split into two triangles
                                    idx0 = face[0] + point_offset
                                    idx1 = face[1] + point_offset
                                    idx2 = face[2] + point_offset
                                    idx3 = face[3] + point_offset
                                    # First triangle
                                    mesh_faces.append([3, idx0, idx1, idx2])
                                    # Second triangle
                                    mesh_faces.append([3, idx0, idx2, idx3])
                                else:
                                    # Triangle face
                                    idx0 = face[0] + point_offset
                                    idx1 = face[1] + point_offset
                                    idx2 = face[2] + point_offset
                                    mesh_faces.append([3, idx0, idx1, idx2])
                            
                            all_points.extend(mesh_points)
                            all_faces.extend(mesh_faces)
                            point_offset += len(mesh_points)
                        
                        processed_count += 1
                        logger.debug(f"Rhino3dmLoader: Processed Brep object with {len(face_meshes)} faces, {len(all_points)} total points, {len(all_faces)} total faces")
                    except Exception as e:
                        logger.warning(f"Rhino3dmLoader: Failed to convert Brep to mesh: {e}", exc_info=True)
                        failed_count += 1
                        continue
                
                # Handle Surface objects - convert to Brep first, then mesh
                elif isinstance(geometry, rhino3dm.Surface):
                    try:
                        # Convert Surface to Brep, then process as Brep
                        # Create a Brep from the surface
                        brep = rhino3dm.Brep.CreateFromSurface(geometry)
                        if brep is None:
                            logger.debug("Rhino3dmLoader: Could not create Brep from Surface")
                            failed_count += 1
                            continue
                        
                        # Process as Brep (reuse Brep logic)
                        brep_faces = brep.Faces
                        if brep_faces is None or len(brep_faces) == 0:
                            failed_count += 1
                            continue
                        
                        face_meshes = []
                        for brep_face in brep_faces:
                            try:
                                mesh = brep_face.GetMesh(rhino3dm.MeshType.Render)
                                if mesh is None:
                                    mesh = brep_face.GetMesh(rhino3dm.MeshType.Any)
                                if mesh is not None:
                                    face_meshes.append(mesh)
                            except Exception as e:
                                logger.debug(f"Rhino3dmLoader: Could not get mesh from Surface->Brep face: {e}")
                                continue
                        
                        if len(face_meshes) == 0:
                            failed_count += 1
                            continue
                        
                        # Process meshes (same as Brep handling)
                        for mesh in face_meshes:
                            vertices = mesh.Vertices
                            if vertices is None or len(vertices) == 0:
                                continue
                            
                            mesh_points = []
                            for vertex in vertices:
                                mesh_points.append([vertex.X, vertex.Y, vertex.Z])
                            
                            faces = mesh.Faces
                            if faces is None or len(faces) == 0:
                                continue
                            
                            mesh_faces = []
                            for face in faces:
                                # Faces are tuples: (A, B, C, D) where triangles have C==D
                                is_quad = face[2] != face[3]
                                if is_quad:
                                    idx0 = face[0] + point_offset
                                    idx1 = face[1] + point_offset
                                    idx2 = face[2] + point_offset
                                    idx3 = face[3] + point_offset
                                    mesh_faces.append([3, idx0, idx1, idx2])
                                    mesh_faces.append([3, idx0, idx2, idx3])
                                else:
                                    idx0 = face[0] + point_offset
                                    idx1 = face[1] + point_offset
                                    idx2 = face[2] + point_offset
                                    mesh_faces.append([3, idx0, idx1, idx2])
                            
                            all_points.extend(mesh_points)
                            all_faces.extend(mesh_faces)
                            point_offset += len(mesh_points)
                        
                        processed_count += 1
                        continue
                    except Exception as e:
                        logger.warning(f"Rhino3dmLoader: Failed to convert Surface to mesh: {e}")
                        continue
                
                # Handle Extrusion objects - convert to Brep then mesh
                elif isinstance(geometry, rhino3dm.Extrusion):
                    try:
                        brep = geometry.ToBrep()
                        if brep is None:
                            failed_count += 1
                            continue
                        
                        # Process as Brep (reuse Brep logic)
                        brep_faces = brep.Faces
                        if brep_faces is None or len(brep_faces) == 0:
                            failed_count += 1
                            continue
                        
                        face_meshes = []
                        for brep_face in brep_faces:
                            try:
                                mesh = brep_face.GetMesh(rhino3dm.MeshType.Render)
                                if mesh is None:
                                    mesh = brep_face.GetMesh(rhino3dm.MeshType.Any)
                                if mesh is not None:
                                    face_meshes.append(mesh)
                            except Exception as e:
                                logger.debug(f"Rhino3dmLoader: Could not get mesh from Extrusion->Brep face: {e}")
                                continue
                        
                        if len(face_meshes) == 0:
                            failed_count += 1
                            continue
                        
                        # Process meshes (same as Brep handling)
                        for mesh in face_meshes:
                            vertices = mesh.Vertices
                            if vertices is None or len(vertices) == 0:
                                continue
                            
                            mesh_points = []
                            for vertex in vertices:
                                mesh_points.append([vertex.X, vertex.Y, vertex.Z])
                            
                            faces = mesh.Faces
                            if faces is None or len(faces) == 0:
                                continue
                            
                            mesh_faces = []
                            for face in faces:
                                # Faces are tuples: (A, B, C, D) where triangles have C==D
                                is_quad = face[2] != face[3]
                                if is_quad:
                                    idx0 = face[0] + point_offset
                                    idx1 = face[1] + point_offset
                                    idx2 = face[2] + point_offset
                                    idx3 = face[3] + point_offset
                                    mesh_faces.append([3, idx0, idx1, idx2])
                                    mesh_faces.append([3, idx0, idx2, idx3])
                                else:
                                    idx0 = face[0] + point_offset
                                    idx1 = face[1] + point_offset
                                    idx2 = face[2] + point_offset
                                    mesh_faces.append([3, idx0, idx1, idx2])
                            
                            all_points.extend(mesh_points)
                            all_faces.extend(mesh_faces)
                            point_offset += len(mesh_points)
                        
                        processed_count += 1
                    except Exception as e:
                        logger.warning(f"Rhino3dmLoader: Failed to convert Extrusion to mesh: {e}", exc_info=True)
                        failed_count += 1
                        continue
                else:
                    logger.debug(f"Rhino3dmLoader: Skipping unsupported geometry type: {geom_type}")
            
            # Log geometry types found
            if geometry_types:
                logger.info(f"Rhino3dmLoader: Geometry types found: {geometry_types}")
            
            logger.info(f"Rhino3dmLoader: Processed {processed_count} objects successfully, {failed_count} failed")
            
            if len(all_points) == 0:
                error_detail = (
                    f"Found {len(model.Objects)} objects with types: {list(geometry_types.keys())}. "
                    f"Processed {processed_count} successfully, {failed_count} failed. "
                    f"Mesh/Brep objects may be empty or conversion failed."
                )
                logger.error(f"Rhino3dmLoader: No meshable geometry found in 3DM file. {error_detail}")
                return None
            
            if len(all_faces) == 0:
                logger.error("Rhino3dmLoader: No faces found in 3DM file")
                return None
            
            # Convert to numpy arrays
            points_array = np.array(all_points, dtype=np.float64)
            faces_array = np.array(all_faces, dtype=np.int32)
            
            # Create PyVista mesh
            pv_mesh = pv.PolyData(points_array, faces_array)
            
            logger.info(f"Rhino3dmLoader: Successfully loaded 3DM file. Points: {len(points_array)}, Faces: {len(all_faces)}")
            return pv_mesh
            
        except ImportError:
            logger.error("Rhino3dmLoader: rhino3dm library not available. Install with: pip install rhino3dm")
            return None
        except Exception as e:
            logger.warning(f"Rhino3dmLoader: Failed to load with rhino3dm: {e}", exc_info=True)
            return None
    
    @staticmethod
    def load_3dm(file_path):
        """
        Load 3DM file using meshio.
        
        Args:
            file_path (str): Path to the 3DM file
            
        Returns:
            pyvista.PolyData: PyVista mesh object, or None if failed
            
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file cannot be loaded
        """
        import os
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"3DM file not found: {file_path}")
        
        logger.info(f"Rhino3dmLoader: Loading 3DM file: {file_path}")
        
        # Load with rhino3dm
        mesh = Rhino3dmLoader.load_with_rhino3dm(file_path)
        if mesh is not None:
            return mesh
        
        # Loading failed - try to get more details
        try:
            import rhino3dm
            model = rhino3dm.File3dm.Read(file_path)
            if model is None:
                detail = "File could not be read (model is None)"
            elif model.Objects is None or len(model.Objects) == 0:
                detail = "File contains no objects"
            else:
                geometry_types = {}
                for obj in model.Objects:
                    if obj.Geometry:
                        geom_type = type(obj.Geometry).__name__
                        geometry_types[geom_type] = geometry_types.get(geom_type, 0) + 1
                detail = f"File contains {len(model.Objects)} objects with types: {list(geometry_types.keys())}"
        except Exception as e:
            detail = f"Error analyzing file: {str(e)}"
        
        error_msg = (
            f"Failed to load 3DM file: {file_path}\n\n"
            f"Details: {detail}\n\n"
            "rhino3dm failed to convert the geometry to a mesh.\n"
            "Please ensure:\n"
            "1. The file is a valid 3DM format\n"
            "2. rhino3dm is properly installed (pip install rhino3dm)\n"
            "3. The file contains meshable geometry (Mesh, Brep, Surface, or Extrusion)\n"
            "4. The file is not corrupted"
        )
        logger.error(f"Rhino3dmLoader: {error_msg}")
        raise ValueError(error_msg)
