#!/usr/bin/env python3
"""
Convert logo.png to icon.icns (macOS) and icon.ico (Windows).

This script creates icon files from logo.png for use in application builds.
"""

import sys
import subprocess
import shutil
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("Error: Pillow (PIL) is required. Install it with: pip install Pillow")
    sys.exit(1)


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
        
        print(f"✓ Successfully created {ico_path} with {len(sizes)} sizes")
        return True
        
    except Exception as e:
        print(f"✗ Error creating .ico file: {e}")
        return False


def create_icns_from_png(png_path: Path, icns_path: Path) -> bool:
    """
    Create a .icns file from a PNG image using iconutil (macOS only).
    
    Creates an iconset with all required sizes and converts it to .icns.
    """
    if sys.platform != 'darwin':
        print("Warning: .icns creation requires macOS. Skipping...")
        return False
    
    if not shutil.which('iconutil'):
        print("✗ Error: iconutil not found. Cannot create .icns file.")
        return False
    
    try:
        import tempfile
        
        # Create temporary iconset directory
        with tempfile.TemporaryDirectory() as temp_dir:
            iconset_dir = Path(temp_dir) / 'icon.iconset'
            iconset_dir.mkdir()
            
            # Required icon sizes for macOS
            icon_sizes = [
                ('icon_16x16.png', 16),
                ('icon_16x16@2x.png', 32),
                ('icon_32x32.png', 32),
                ('icon_32x32@2x.png', 64),
                ('icon_128x128.png', 128),
                ('icon_128x128@2x.png', 256),
                ('icon_256x256.png', 256),
                ('icon_256x256@2x.png', 512),
                ('icon_512x512.png', 512),
                ('icon_512x512@2x.png', 1024),
            ]
            
            # Open source image
            img = Image.open(png_path)
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
            
            # Create all required sizes
            for filename, size in icon_sizes:
                resized = img.resize((size, size), Image.Resampling.LANCZOS)
                output_path = iconset_dir / filename
                resized.save(output_path, format='PNG')
            
            # Convert iconset to .icns using iconutil
            result = subprocess.run(
                ['iconutil', '--convert', 'icns', '--output', str(icns_path), str(iconset_dir)],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                print(f"✗ iconutil error: {result.stderr}")
                return False
            
            if icns_path.exists():
                print(f"✓ Successfully created {icns_path}")
                return True
            else:
                print(f"✗ Failed to create {icns_path}")
                return False
                
    except Exception as e:
        print(f"✗ Error creating .icns file: {e}")
        return False


def main():
    """Main entry point."""
    # Get project root (parent of scripts directory)
    project_root = Path(__file__).parent.parent
    assets_dir = project_root / 'assets'
    
    logo_path = assets_dir / 'logo.png'
    icns_path = assets_dir / 'icon.icns'
    ico_path = assets_dir / 'icon.ico'
    
    if not logo_path.exists():
        print(f"✗ Error: {logo_path} does not exist")
        print(f"Please ensure logo.png is in the assets directory")
        sys.exit(1)
    
    print(f"Converting {logo_path} to icon files...")
    print()
    
    # Create .ico file (works on all platforms)
    print("Creating icon.ico for Windows...")
    if create_ico_from_png(logo_path, ico_path):
        print(f"  File size: {ico_path.stat().st_size / 1024:.1f} KB")
    else:
        print("  Failed to create icon.ico")
    
    print()
    
    # Create .icns file (macOS only)
    print("Creating icon.icns for macOS...")
    if create_icns_from_png(logo_path, icns_path):
        print(f"  File size: {icns_path.stat().st_size / 1024:.1f} KB")
    else:
        print("  Failed to create icon.icns (this is normal on non-macOS systems)")
    
    print()
    print("Icon conversion complete!")


if __name__ == "__main__":
    main()
