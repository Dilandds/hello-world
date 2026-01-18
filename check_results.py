#!/usr/bin/env python3
"""Quick script to check which volume methods match target."""
import sys
from core.mesh_calculator import MeshCalculator
import pyvista as pv

if len(sys.argv) < 3:
    print("Usage: python check_results.py <stl_file> <target_volume>")
    sys.exit(1)

file_path = sys.argv[1]
target = float(sys.argv[2])

mesh = pv.read(file_path)
results = MeshCalculator.calculate_volume_multiple_methods(mesh, target)

# Filter successful and sort by difference
successful = [(k, v) for k, v in results.items() if v.get('volume', 0) > 0]
sorted_results = sorted(successful, key=lambda x: x[1].get('diff_from_target', float('inf')) if x[1].get('diff_from_target') is not None else float('inf'))

print(f"\nTarget: {target:.2f} mm³\n")
print(f"{'Method':<35} | {'Volume':<15} | {'Difference':<12} | {'% Error':<10}")
print("-" * 80)

for key, result in sorted_results[:10]:  # Top 10
    vol = result['volume']
    diff = result.get('diff_from_target')
    method = result['method']
    if diff is not None:
        pct = 100 * diff / target if target > 0 else 0
        marker = "⭐" if diff < 1.0 else "  "
        print(f"{method:<35} | {vol:>14.2f} | {diff:>+11.2f} {marker} | {pct:>8.4f}%")
    else:
        print(f"{method:<35} | {vol:>14.2f} | {'N/A':<12} | {'N/A':<10}")

print()
