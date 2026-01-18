"""
Mesh analysis and calculation utilities.
"""
import logging
import numpy as np
import pyvista as pv

logger = logging.getLogger(__name__)


class MeshCalculator:
    """Handles mesh analysis and calculations."""
    
    @staticmethod
    def calculate_dimensions(mesh):
        """
        Calculate bounding box dimensions from a mesh.
        
        Args:
            mesh: PyVista mesh object
            
        Returns:
            dict: Dictionary with 'width', 'height', 'depth' in mm
        """
        if mesh is None:
            return {
                'width': 0.0,
                'height': 0.0,
                'depth': 0.0
            }
        
        bounds = mesh.bounds  # (xmin, xmax, ymin, ymax, zmin, zmax)
        width = bounds[1] - bounds[0]   # X dimension
        height = bounds[3] - bounds[2]  # Y dimension
        depth = bounds[5] - bounds[4]   # Z dimension
        
        return {
            'width': width,
            'height': height,
            'depth': depth
        }
    
    @staticmethod
    def calculate_volume(mesh):
        """
        Calculate volume of a mesh.
        
        Args:
            mesh: PyVista mesh object
            
        Returns:
            float: Volume in mm³, or 0.0 if calculation fails
        """
        if mesh is None:
            return 0.0
        
        try:
            volume = mesh.volume
            return volume
        except Exception as e:
            logger.warning(f"Failed to calculate volume: {e}")
            return 0.0
    
    @staticmethod
    def calculate_surface_area(mesh):
        """
        Calculate surface area of a mesh.
        
        Args:
            mesh: PyVista mesh object
            
        Returns:
            dict: Dictionary with 'mm2' and 'cm2' surface area values
        """
        if mesh is None:
            return {
                'mm2': 0.0,
                'cm2': 0.0
            }
        
        try:
            surface_area_mm2 = mesh.area
        except Exception as e:
            logger.warning(f"Failed to calculate surface area: {e}")
            surface_area_mm2 = 0.0
        
        # Convert surface area from mm² to cm²
        surface_area_cm2 = surface_area_mm2 / 100.0
        
        return {
            'mm2': surface_area_mm2,
            'cm2': surface_area_cm2
        }
    
    @staticmethod
    def estimate_weight(volume_mm3, density_g_per_cm3):
        """
        Estimate weight based on volume and material density.
        
        Args:
            volume_mm3: Volume in mm³
            density_g_per_cm3: Material density in g/cm³
            
        Returns:
            dict: Dictionary with 'grams' and formatted 'display' string
        """
        if volume_mm3 <= 0 or density_g_per_cm3 <= 0:
            return {
                'grams': 0.0,
                'display': '--'
            }
        
        # Convert volume from mm³ to cm³ (1 cm³ = 1000 mm³)
        volume_cm3 = volume_mm3 / 1000.0
        
        # Calculate weight: weight = volume * density
        weight_grams = volume_cm3 * density_g_per_cm3
        
        # Format display string
        if weight_grams >= 1000:
            display = f"{weight_grams / 1000:.3f} kg"
        else:
            display = f"{weight_grams:.2f} g"
        
        return {
            'grams': weight_grams,
            'display': display
        }
    
    @staticmethod
    def calculate_volume_convex_hull(mesh):
        """
        Calculate volume using convex hull approximation.
        Note: PyVista doesn't have direct convex_hull() for PolyData.
        This uses Delaunay 3D triangulation as an approximation.
        
        Args:
            mesh: PyVista mesh object
            
        Returns:
            float: Volume in mm³, or 0.0 if calculation fails
        """
        if mesh is None:
            return 0.0
        
        try:
            # Try Delaunay 3D triangulation which creates a volume mesh
            # This approximates the convex hull
            try:
                convex_mesh = mesh.delaunay_3d()
                if convex_mesh.n_cells > 0:
                    volume = convex_mesh.volume
                    return volume
            except:
                pass
            
            # Fallback: use bounding box as upper bound estimate
            bounds = mesh.bounds
            width = bounds[1] - bounds[0]
            height = bounds[3] - bounds[2]
            depth = bounds[5] - bounds[4]
            logger.warning("Convex hull approximation using bounding box")
            return width * height * depth
        except Exception as e:
            logger.warning(f"Failed to calculate convex hull volume: {e}")
            return 0.0
    
    @staticmethod
    def calculate_volume_voxel(mesh, density=100):
        """
        Calculate volume using voxel-based discretization (simplified Monte Carlo approach).
        Note: Full voxelization requires mesh.contains() which PyVista PolyData doesn't have.
        This method is a placeholder - returns 0.0 to indicate not implemented.
        
        Args:
            mesh: PyVista mesh object
            density: Voxel grid density (points per unit) - unused for now
            
        Returns:
            float: Volume in mm³, or 0.0 if calculation fails/not implemented
        """
        # PyVista PolyData doesn't have easy voxelization or contains() method
        # For proper voxelization, would need trimesh or other library
        # Returning 0.0 as placeholder - will be skipped in comparison
        return 0.0
    
    @staticmethod
    def calculate_volume_repair(mesh, hole_size=None):
        """
        Attempt to repair mesh by filling holes, then calculate volume.
        
        Args:
            mesh: PyVista mesh object
            hole_size: Maximum hole size to fill (None for auto)
            
        Returns:
            float: Volume in mm³, or 0.0 if calculation fails
        """
        if mesh is None:
            return 0.0
        
        try:
            # Copy mesh to avoid modifying original
            repaired = mesh.copy()
            
            # Fill holes
            if hole_size is None:
                # Auto-detect hole size (use mesh bounds to estimate)
                bounds = mesh.bounds
                max_dim = max(bounds[1] - bounds[0], bounds[3] - bounds[2], bounds[5] - bounds[4])
                hole_size = max_dim * 0.1  # 10% of max dimension
            
            repaired = repaired.fill_holes(hole_size=hole_size)
            
            # Try to calculate volume on repaired mesh
            if hasattr(repaired, 'volume'):
                volume = repaired.volume
                return volume
            else:
                return 0.0
        except Exception as e:
            logger.warning(f"Failed to calculate repaired mesh volume: {e}")
            return 0.0
    
    @staticmethod
    def calculate_volume_manual_tetrahedron(mesh, reference_point='origin'):
        """
        Calculate volume using manual signed tetrahedron method.
        
        Args:
            mesh: PyVista mesh object
            reference_point: 'origin' (0,0,0), 'centroid' (mesh center), or custom point
            
        Returns:
            float: Volume in mm³, or 0.0 if calculation fails
        """
        if mesh is None:
            return 0.0
        
        try:
            # Get reference point
            if reference_point == 'origin':
                ref = np.array([0.0, 0.0, 0.0])
            elif reference_point == 'centroid':
                ref = np.array(mesh.center)
            else:
                ref = np.array(reference_point)
            
            # Get mesh points and faces
            points = np.array(mesh.points)
            faces = mesh.faces
            
            # Extract triangles from face array
            # PyVista faces format: [n, v1, v2, v3, n, v1, v2, v3, ...]
            if len(faces) == 0:
                return 0.0
            
            # Reshape faces array (assuming triangular faces)
            num_faces = len(faces) // 4
            if num_faces == 0:
                return 0.0
            
            triangles = faces.reshape(-1, 4)[:, 1:4]  # Skip first element (n), get v1,v2,v3
            
            total_volume = 0.0
            for triangle in triangles:
                v1 = points[triangle[0]]
                v2 = points[triangle[1]]
                v3 = points[triangle[2]]
                
                # Signed volume of tetrahedron: (1/6) * |det([v1-ref, v2-ref, v3-ref])|
                # Using scalar triple product: (1/6) * dot(v1-ref, cross(v2-ref, v3-ref))
                v1_ref = v1 - ref
                v2_ref = v2 - ref
                v3_ref = v3 - ref
                
                vol = np.dot(v1_ref, np.cross(v2_ref, v3_ref)) / 6.0
                total_volume += vol
            
            return abs(total_volume)
        except Exception as e:
            logger.warning(f"Failed to calculate manual tetrahedron volume: {e}")
            return 0.0
    
    @staticmethod
    def calculate_volume_bounding_box(mesh):
        """
        Calculate volume using bounding box (simple approximation).
        
        Args:
            mesh: PyVista mesh object
            
        Returns:
            float: Volume in mm³ (bounding box volume)
        """
        if mesh is None:
            return 0.0
        
        try:
            bounds = mesh.bounds  # (xmin, xmax, ymin, ymax, zmin, zmax)
            width = bounds[1] - bounds[0]
            height = bounds[3] - bounds[2]
            depth = bounds[5] - bounds[4]
            return width * height * depth
        except Exception as e:
            logger.warning(f"Failed to calculate bounding box volume: {e}")
            return 0.0
    
    @staticmethod
    def calculate_volume_with_preprocessing(mesh, preprocessing='triangulate'):
        """
        Calculate volume with mesh preprocessing.
        
        Args:
            mesh: PyVista mesh object
            preprocessing: 'triangulate', 'smooth', 'decimate', or None
            
        Returns:
            float: Volume in mm³, or 0.0 if calculation fails
        """
        if mesh is None:
            return 0.0
        
        try:
            processed = mesh.copy()
            
            if preprocessing == 'triangulate':
                processed = processed.triangulate()
            elif preprocessing == 'smooth':
                processed = processed.smooth(n_iter=10)
            elif preprocessing == 'decimate':
                reduction = 0.1  # 10% reduction
                processed = processed.decimate(reduction)
            
            volume = processed.volume
            return volume
        except Exception as e:
            logger.warning(f"Failed to calculate volume with preprocessing '{preprocessing}': {e}")
            return 0.0
    
    @staticmethod
    def calculate_volume_multiple_methods(mesh, target_volume=None):
        """
        Try multiple volume calculation methods and return results.
        
        Args:
            mesh: PyVista mesh object
            target_volume: Optional target volume for comparison (in mm³)
            
        Returns:
            dict: Dictionary with method names and results containing:
                - 'volume': calculated volume in mm³
                - 'diff_from_target': difference from target (if provided)
                - 'method': method name
                - 'error': error message if calculation failed
        """
        if mesh is None:
            return {}
        
        results = {}
        
        # Method 1: Standard PyVista volume
        try:
            vol = mesh.volume
            results['pyvista_standard'] = {
                'volume': vol,
                'method': 'PyVista Standard',
                'diff_from_target': abs(vol - target_volume) if target_volume else None
            }
        except Exception as e:
            results['pyvista_standard'] = {
                'volume': 0.0,
                'method': 'PyVista Standard',
                'error': str(e),
                'diff_from_target': None
            }
        
        # Method 2: Convex hull
        try:
            vol = MeshCalculator.calculate_volume_convex_hull(mesh)
            results['convex_hull'] = {
                'volume': vol,
                'method': 'Convex Hull',
                'diff_from_target': abs(vol - target_volume) if target_volume else None
            }
        except Exception as e:
            results['convex_hull'] = {
                'volume': 0.0,
                'method': 'Convex Hull',
                'error': str(e),
                'diff_from_target': None
            }
        
        # Method 3: Voxel-based (different densities)
        for density in [50, 100, 200]:
            try:
                vol = MeshCalculator.calculate_volume_voxel(mesh, density=density)
                results[f'voxel_d{density}'] = {
                    'volume': vol,
                    'method': f'Voxel (density={density})',
                    'diff_from_target': abs(vol - target_volume) if target_volume else None
                }
            except Exception as e:
                results[f'voxel_d{density}'] = {
                    'volume': 0.0,
                    'method': f'Voxel (density={density})',
                    'error': str(e),
                    'diff_from_target': None
                }
        
        # Method 4: Mesh repair
        try:
            vol = MeshCalculator.calculate_volume_repair(mesh)
            results['mesh_repair'] = {
                'volume': vol,
                'method': 'Mesh Repair + Volume',
                'diff_from_target': abs(vol - target_volume) if target_volume else None
            }
        except Exception as e:
            results['mesh_repair'] = {
                'volume': 0.0,
                'method': 'Mesh Repair + Volume',
                'error': str(e),
                'diff_from_target': None
            }
        
        # Method 5: Manual tetrahedron (different reference points)
        for ref_point in ['origin', 'centroid']:
            try:
                vol = MeshCalculator.calculate_volume_manual_tetrahedron(mesh, ref_point)
                results[f'manual_tetra_{ref_point}'] = {
                    'volume': vol,
                    'method': f'Manual Tetrahedron ({ref_point})',
                    'diff_from_target': abs(vol - target_volume) if target_volume else None
                }
            except Exception as e:
                results[f'manual_tetra_{ref_point}'] = {
                    'volume': 0.0,
                    'method': f'Manual Tetrahedron ({ref_point})',
                    'error': str(e),
                    'diff_from_target': None
                }
        
        # Method 6: Bounding box
        try:
            vol = MeshCalculator.calculate_volume_bounding_box(mesh)
            results['bounding_box'] = {
                'volume': vol,
                'method': 'Bounding Box',
                'diff_from_target': abs(vol - target_volume) if target_volume else None
            }
        except Exception as e:
            results['bounding_box'] = {
                'volume': 0.0,
                'method': 'Bounding Box',
                'error': str(e),
                'diff_from_target': None
            }
        
        # Method 7: PyVista with preprocessing
        for prep in ['triangulate', 'smooth']:
            try:
                vol = MeshCalculator.calculate_volume_with_preprocessing(mesh, preprocessing=prep)
                results[f'pyvista_{prep}'] = {
                    'volume': vol,
                    'method': f'PyVista + {prep.capitalize()}',
                    'diff_from_target': abs(vol - target_volume) if target_volume else None
                }
            except Exception as e:
                results[f'pyvista_{prep}'] = {
                    'volume': 0.0,
                    'method': f'PyVista + {prep.capitalize()}',
                    'error': str(e),
                    'diff_from_target': None
                }
        
        return results
    
    @staticmethod
    def calculate_scale_for_target_weight(current_weight_grams, target_weight_grams):
        """
        Calculate the uniform scale factor needed to achieve a target weight.
        
        Weight scales with volume (length^3), so:
        target_weight = current_weight * scale^3
        scale = (target_weight / current_weight)^(1/3)
        
        Args:
            current_weight_grams: Current weight in grams
            target_weight_grams: Target weight in grams
            
        Returns:
            dict: Dictionary with scale factor and validity
        """
        if current_weight_grams <= 0 or target_weight_grams <= 0:
            return {
                'scale_factor': 1.0,
                'valid': False,
                'error': 'Invalid weight values'
            }
        
        scale_factor = (target_weight_grams / current_weight_grams) ** (1.0 / 3.0)
        
        return {
            'scale_factor': scale_factor,
            'valid': True,
            'error': None
        }
    
    @staticmethod
    def apply_scale_to_dimensions(width, height, depth, scale_factor):
        """
        Calculate new dimensions after applying uniform scale.
        
        Args:
            width: Original width (X) in mm
            height: Original height (Y) in mm
            depth: Original depth (Z) in mm
            scale_factor: Uniform scale factor to apply
            
        Returns:
            dict: Dictionary with new dimensions
        """
        return {
            'width': width * scale_factor,
            'height': height * scale_factor,
            'depth': depth * scale_factor
        }
    
    @staticmethod
    def apply_scale_to_volume(volume_mm3, scale_factor):
        """
        Calculate new volume after applying uniform scale.
        Volume scales with the cube of the linear scale factor.
        
        Args:
            volume_mm3: Original volume in mm³
            scale_factor: Uniform scale factor
            
        Returns:
            dict: Dictionary with new volume values
        """
        new_volume_mm3 = volume_mm3 * (scale_factor ** 3)
        new_volume_cm3 = new_volume_mm3 / 1000.0
        
        return {
            'volume_mm3': new_volume_mm3,
            'volume_cm3': new_volume_cm3
        }
    
    @staticmethod
    def scale_mesh(mesh, scale_factor):
        """
        Create a scaled copy of the mesh.
        
        Args:
            mesh: PyVista mesh object
            scale_factor: Uniform scale factor to apply
            
        Returns:
            pv.PolyData: Scaled mesh, or None if operation fails
        """
        if mesh is None or scale_factor <= 0:
            return None
        
        try:
            # Create a copy and scale it
            scaled_mesh = mesh.copy()
            scaled_mesh.points *= scale_factor
            return scaled_mesh
        except Exception as e:
            logger.warning(f"Failed to scale mesh: {e}")
            return None
    
    @staticmethod
    def export_stl(mesh, file_path):
        """
        Export mesh to STL file.
        
        Args:
            mesh: PyVista mesh object
            file_path: Path to save the STL file
            
        Returns:
            bool: True if successful, False otherwise
        """
        if mesh is None:
            return False
        
        try:
            mesh.save(file_path)
            return True
        except Exception as e:
            logger.warning(f"Failed to export STL: {e}")
            return False
    
    @staticmethod
    def get_mesh_data(mesh):
        """
        Get all mesh data in a single call.
        
        Args:
            mesh: PyVista mesh object
            
        Returns:
            dict: Dictionary containing all calculated mesh properties
        """
        if mesh is None:
            return {
                'width': 0.0,
                'height': 0.0,
                'depth': 0.0,
                'volume_mm3': 0.0,
                'volume_cm3': 0.0,
                'surface_area_mm2': 0.0,
                'surface_area_cm2': 0.0
            }
        
        dimensions = MeshCalculator.calculate_dimensions(mesh)
        volume_mm3 = MeshCalculator.calculate_volume(mesh)
        surface_area = MeshCalculator.calculate_surface_area(mesh)
        
        return {
            'width': dimensions['width'],
            'height': dimensions['height'],
            'depth': dimensions['depth'],
            'volume_mm3': volume_mm3,
            'volume_cm3': volume_mm3 / 1000.0,
            'surface_area_mm2': surface_area['mm2'],
            'surface_area_cm2': surface_area['cm2']
        }
