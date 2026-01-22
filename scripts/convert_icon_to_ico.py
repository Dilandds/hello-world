#!/usr/bin/env python3
"""
Convert icon.icns to icon.ico for Windows builds.

This script extracts PNG images from a macOS .icns file and creates
a Windows .ico file with multiple sizes.
"""

import sys
import subprocess
import shutil
from pathlib import Path
import tempfile

try:
    from PIL import Image
except ImportError:
    print("Error: Pillow (PIL) is required. Install it with: pip install Pillow")
    sys.exit(1)


def extract_icns_to_pngs(icns_path: Path, output_dir: Path) -> bool:
    """
    Extract PNG images from .icns file using iconutil (macOS only).
    
    Returns True if successful, False otherwise.
    """
    if not shutil.which('iconutil'):
        print("Warning: iconutil not found. Trying alternative method...")
        return False
    
    try:
        # iconutil extracts to a .iconset directory
        iconset_dir = output_dir / 'icon.iconset'
        iconset_dir.mkdir(exist_ok=True)
        
        # Extract using iconutil
        result = subprocess.run(
            ['iconutil', '--convert', 'iconset', '--output', str(iconset_dir), str(icns_path)],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print(f"iconutil error: {result.stderr}")
            return False
        
        # Check if iconset was created
        if iconset_dir.exists() and any(iconset_dir.glob('*.png')):
            return True
        
        return False
    except Exception as e:
        print(f"Error extracting .icns: {e}")
        return False


def find_largest_png(png_dir: Path) -> Path:
    """Find the largest PNG image in the directory."""
    png_files = list(png_dir.glob('*.png'))
    if not png_files:
        return None
    
    # Sort by file size (largest first)
    png_files.sort(key=lambda p: p.stat().st_size, reverse=True)
    return png_files[0]


def create_ico_from_png(png_path: Path, ico_path: Path) -> bool:
    """
    Create a .ico file from a PNG image with multiple sizes.
    
    The .ico file will contain: 256x256, 128x128, 64x64, 48x48, 32x32, 16x16
    """
    try:
        # Open the source image
        img = Image.open(png_path)
        
        # Ensure it's RGBA
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        
        # Create list of sizes for the .ico file
        sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]
        
        # Create resized images
        images = []
        for size in sizes:
            resized = img.resize(size, Image.Resampling.LANCZOS)
            images.append(resized)
        
        # Save as .ico with multiple sizes
        images[0].save(
            ico_path,
            format='ICO',
            sizes=[(img.width, img.height) for img in images]
        )
        
        print(f"Successfully created {ico_path} with {len(sizes)} sizes")
        return True
        
    except Exception as e:
        print(f"Error creating .ico file: {e}")
        return False


def convert_icns_to_ico(icns_path: Path, ico_path: Path) -> bool:
    """
    Convert .icns file to .ico file.
    
    Args:
        icns_path: Path to input .icns file
        ico_path: Path to output .ico file
    
    Returns:
        True if successful, False otherwise
    """
    if not icns_path.exists():
        print(f"Error: {icns_path} does not exist")
        return False
    
    # Create temporary directory for extraction
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Try to extract PNGs from .icns
        if extract_icns_to_pngs(icns_path, temp_path):
            # Find the largest PNG (usually the best quality)
            png_path = find_largest_png(temp_path / 'icon.iconset')
            if png_path:
                return create_ico_from_png(png_path, ico_path)
        
        # Alternative: Try to read .icns directly with Pillow (may not work)
        # If iconutil extraction failed, try direct conversion
        try:
            # Some .icns files can be read directly by Pillow
            img = Image.open(icns_path)
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
            
            # Create .ico with multiple sizes
            sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]
            images = [img.resize(size, Image.Resampling.LANCZOS) for size in sizes]
            
            images[0].save(
                ico_path,
                format='ICO',
                sizes=[(img.width, img.height) for img in images]
            )
            
            print(f"Successfully created {ico_path} from {icns_path}")
            return True
            
        except Exception as e:
            print(f"Error: Could not convert {icns_path} to {ico_path}")
            print(f"Details: {e}")
            print("\nAlternative: Create icon.ico manually using:")
            print("  1. Extract PNG from icon.icns using iconutil")
            print("  2. Use online converter: https://cloudconvert.com/png-to-ico")
            print("  3. Or use ImageMagick: convert icon.png -define icon:auto-resize=256,48,32,16 icon.ico")
            return False


def main():
    """Main entry point."""
    # Get project root (parent of scripts directory)
    project_root = Path(__file__).parent.parent
    assets_dir = project_root / 'assets'
    
    icns_path = assets_dir / 'icon.icns'
    ico_path = assets_dir / 'icon.ico'
    
    print(f"Converting {icns_path} to {ico_path}...")
    
    if not icns_path.exists():
        print(f"Error: {icns_path} does not exist")
        print(f"Please ensure icon.icns is in the assets directory")
        sys.exit(1)
    
    if convert_icns_to_ico(icns_path, ico_path):
        print(f"\n✓ Successfully created {ico_path}")
        print(f"  File size: {ico_path.stat().st_size / 1024:.1f} KB")
        sys.exit(0)
    else:
        print(f"\n✗ Failed to create {ico_path}")
        sys.exit(1)


if __name__ == "__main__":
    main()
