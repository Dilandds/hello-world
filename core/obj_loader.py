"""
Custom OBJ file loader that handles files with texture coordinate mismatches.
Extracts only geometry data (vertices and faces), ignoring texture coordinates and normals.
"""
import logging
import numpy as np
import pyvista as pv

logger = logging.getLogger(__name__)


class ObjLoader:
    """Handles loading OBJ files with lenient parsing for geometry-only extraction."""
    
    @staticmethod
    def load_obj(file_path):
        """
        Load OBJ file by extracting only vertices and faces, ignoring texture coordinates.
        
        This parser is more lenient than meshio and can handle OBJ files where
        texture coordinates don't match vertex counts.
        
        Args:
            file_path (str): Path to the OBJ file
            
        Returns:
            pyvista.PolyData: PyVista mesh object
            
        Raises:
            ValueError: If file cannot be read or contains no valid geometry
        """
        logger.info(f"ObjLoader: Loading OBJ file with custom parser: {file_path}")
        
        vertices = []
        faces = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    
                    # Skip empty lines and comments
                    if not line or line.startswith('#'):
                        continue
                    
                    parts = line.split()
                    if not parts:
                        continue
                    
                    command = parts[0].lower()
                    
                    # Parse vertex (v x y z [w])
                    if command == 'v':
                        try:
                            # OBJ format: v x y z [w] where w is optional
                            x = float(parts[1])
                            y = float(parts[2])
                            z = float(parts[3]) if len(parts) > 3 else 0.0
                            vertices.append([x, y, z])
                        except (ValueError, IndexError) as e:
                            logger.warning(f"ObjLoader: Skipping invalid vertex at line {line_num}: {e}")
                            continue
                    
                    # Parse face (f v1 v2 v3 ... or f v1/vt1/vn1 v2/vt2/vn2 ...)
                    elif command == 'f':
                        try:
                            face_vertices = []
                            
                            # Parse each vertex reference in the face
                            for vertex_ref in parts[1:]:
                                # Handle different face formats:
                                # - f 1 2 3 (vertex indices only)
                                # - f 1/2/3 4/5/6 (vertex/texture/normal)
                                # - f 1/2 3/4 (vertex/texture)
                                # - f 1//3 2//4 (vertex//normal)
                                
                                # Split by '/' to get vertex/texture/normal indices
                                indices = vertex_ref.split('/')
                                
                                # First number is always the vertex index
                                vertex_idx = int(indices[0])
                                
                                # OBJ uses 1-based indexing, convert to 0-based
                                # Also handle negative indices (relative indexing)
                                if vertex_idx < 0:
                                    vertex_idx = len(vertices) + vertex_idx + 1
                                else:
                                    vertex_idx = vertex_idx - 1
                                
                                # Validate vertex index
                                if 0 <= vertex_idx < len(vertices):
                                    face_vertices.append(vertex_idx)
                                else:
                                    logger.warning(f"ObjLoader: Invalid vertex index {vertex_idx} at line {line_num}")
                            
                            # Only add face if it has at least 3 vertices
                            if len(face_vertices) >= 3:
                                # Convert polygon to triangles (fan triangulation)
                                # For a face with n vertices: (0,1,2), (0,2,3), (0,3,4), ...
                                for i in range(1, len(face_vertices) - 1):
                                    faces.append([
                                        face_vertices[0],
                                        face_vertices[i],
                                        face_vertices[i + 1]
                                    ])
                            else:
                                logger.warning(f"ObjLoader: Face with less than 3 vertices at line {line_num}")
                        
                        except (ValueError, IndexError) as e:
                            logger.warning(f"ObjLoader: Skipping invalid face at line {line_num}: {e}")
                            continue
                    
                    # Ignore other commands (vt, vn, mtl, etc.)
                    # These are optional and can cause validation issues
        
        except IOError as e:
            error_msg = f"Failed to read OBJ file: {e}"
            logger.error(f"ObjLoader: {error_msg}")
            raise ValueError(error_msg)
        except Exception as e:
            error_msg = f"Unexpected error while parsing OBJ file: {e}"
            logger.error(f"ObjLoader: {error_msg}", exc_info=True)
            raise ValueError(error_msg)
        
        # Validate that we have geometry
        if len(vertices) == 0:
            error_msg = "OBJ file contains no vertices"
            logger.error(f"ObjLoader: {error_msg}")
            raise ValueError(error_msg)
        
        if len(faces) == 0:
            error_msg = "OBJ file contains no faces"
            logger.error(f"ObjLoader: {error_msg}")
            raise ValueError(error_msg)
        
        logger.info(f"ObjLoader: Parsed {len(vertices)} vertices and {len(faces)} triangles")
        
        # Convert to numpy arrays
        try:
            points = np.array(vertices, dtype=np.float64)
            
            # PyVista expects cells in a specific format:
            # For triangles: [3, i1, i2, i3, 3, i4, i5, i6, ...]
            # Where the first number is the number of vertices in the cell
            cells = []
            for face in faces:
                cells.append(3)  # Triangle has 3 vertices
                cells.extend(face)
            
            cells = np.array(cells, dtype=np.int32)
            
            # Create PyVista PolyData
            mesh = pv.PolyData(points, cells)
            
            logger.info(f"ObjLoader: Created PyVista mesh with {mesh.n_points} points and {mesh.n_cells} cells")
            
            return mesh
            
        except Exception as e:
            error_msg = f"Failed to create PyVista mesh from parsed data: {e}"
            logger.error(f"ObjLoader: {error_msg}", exc_info=True)
            raise ValueError(error_msg)
