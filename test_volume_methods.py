#!/usr/bin/env python3
"""
Test script to compare different volume calculation methods.

Usage:
    python test_volume_methods.py <path_to_stl_file> [target_volume]
    
Example:
    python test_volume_methods.py test_file.stl 30182.05
"""
import sys
import time
from pathlib import Path
import pyvista as pv
from core.mesh_calculator import MeshCalculator

def print_separator():
    """Print a separator line."""
    print("=" * 100)

def format_volume(volume):
    """Format volume for display."""
    if volume == 0.0:
        return "N/A"
    return f"{volume:.2f}"

def format_diff(diff, target):
    """Format difference from target."""
    if diff is None or target is None:
        return "N/A"
    if diff < 0.01:  # Very close
        return f"{diff:+.2f} ⭐"
    return f"{diff:+.2f}"

def main():
    if len(sys.argv) < 2:
        print("Usage: python test_volume_methods.py <stl_file> [target_volume]")
        print("Example: python test_volume_methods.py test.stl 30182.05")
        sys.exit(1)
    
    stl_file = Path(sys.argv[1])
    target_volume = float(sys.argv[2]) if len(sys.argv) > 2 else None
    
    if not stl_file.exists():
        print(f"Error: File not found: {stl_file}")
        sys.exit(1)
    
    print_separator()
    print(f"Volume Calculation Method Comparison")
    print_separator()
    print(f"STL File: {stl_file}")
    if target_volume:
        print(f"Target Volume: {target_volume:.2f} mm³")
    print_separator()
    
    # Load mesh
    print("Loading mesh...")
    try:
        mesh = pv.read(str(stl_file))
        print(f"✓ Mesh loaded successfully")
    except Exception as e:
        print(f"✗ Error loading mesh: {e}")
        sys.exit(1)
    
    # Check mesh properties
    print("\nMesh Properties:")
    print(f"  Number of points: {mesh.n_points:,}")
    print(f"  Number of cells: {mesh.n_cells:,}")
    try:
        is_watertight = mesh.is_manifold and mesh.is_watertight if hasattr(mesh, 'is_manifold') else None
        if is_watertight is not None:
            print(f"  Is watertight: {is_watertight}")
        else:
            # Try to get watertight status
            try:
                test_vol = mesh.volume
                print(f"  Is watertight: Unknown (volume calculation succeeded)")
            except:
                print(f"  Is watertight: Likely False (volume calculation failed)")
    except:
        pass
    
    bounds = mesh.bounds
    dimensions = MeshCalculator.calculate_dimensions(mesh)
    print(f"  Dimensions: {dimensions['width']:.2f} × {dimensions['height']:.2f} × {dimensions['depth']:.2f} mm")
    print(f"  Bounds: X[{bounds[0]:.2f}, {bounds[1]:.2f}], Y[{bounds[2]:.2f}, {bounds[3]:.2f}], Z[{bounds[4]:.2f}, {bounds[5]:.2f}]")
    
    print_separator()
    
    # Calculate volumes using all methods
    print("Calculating volumes using multiple methods...\n")
    start_time = time.time()
    results = MeshCalculator.calculate_volume_multiple_methods(mesh, target_volume=target_volume)
    total_time = time.time() - start_time
    
    # Sort results by difference from target (if available), or by volume
    if target_volume:
        sorted_results = sorted(
            results.items(),
            key=lambda x: x[1].get('diff_from_target', float('inf')) if x[1].get('diff_from_target') is not None else float('inf')
        )
    else:
        sorted_results = sorted(results.items(), key=lambda x: x[1].get('volume', 0))
    
    # Print results table
    print(f"{'Method':<35} | {'Volume (mm³)':<15} | {'Diff from Target':<18} | Status")
    print("-" * 100)
    
    for key, result in sorted_results:
        method = result.get('method', key)
        volume = result.get('volume', 0.0)
        diff = result.get('diff_from_target')
        error = result.get('error')
        
        vol_str = format_volume(volume)
        diff_str = format_diff(diff, target_volume) if diff is not None else "N/A"
        
        if error:
            status = f"✗ Error: {error[:30]}"
        elif volume == 0.0:
            status = "✗ Failed"
        else:
            status = "✓ Success"
        
        # Truncate method name if too long
        method_display = method[:33] + "..." if len(method) > 35 else method
        
        print(f"{method_display:<35} | {vol_str:>15} | {diff_str:>18} | {status}")
    
    print_separator()
    print(f"Total calculation time: {total_time:.3f} seconds")
    
    # Find best match
    if target_volume:
        best_match = None
        best_diff = float('inf')
        for key, result in results.items():
            diff = result.get('diff_from_target')
            if diff is not None and diff < best_diff:
                best_diff = diff
                best_match = result
        
        if best_match:
            print(f"\n🏆 Best Match:")
            print(f"   Method: {best_match['method']}")
            print(f"   Volume: {best_match['volume']:.2f} mm³")
            print(f"   Difference: {best_diff:+.2f} mm³ ({100 * best_diff / target_volume:.3f}%)")
    
    print_separator()
    
    # Summary statistics
    successful = [r for r in results.values() if r.get('volume', 0) > 0 and 'error' not in r]
    if successful:
        volumes = [r['volume'] for r in successful]
        print(f"\nSummary Statistics (successful methods only):")
        print(f"  Number of successful methods: {len(successful)}")
        print(f"  Average volume: {sum(volumes) / len(volumes):.2f} mm³")
        print(f"  Min volume: {min(volumes):.2f} mm³")
        print(f"  Max volume: {max(volumes):.2f} mm³")
        print(f"  Range: {max(volumes) - min(volumes):.2f} mm³")
        if target_volume:
            print(f"  Target: {target_volume:.2f} mm³")
    
    print_separator()

if __name__ == "__main__":
    main()
