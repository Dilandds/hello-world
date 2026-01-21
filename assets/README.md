# Application Icons

This directory should contain the application icons for packaging.

## Required Files

### Mac Icon (icon.icns)
- **File**: `icon.icns`
- **Format**: macOS icon format
- **Sizes**: Should include 512x512, 256x256, 128x128, 64x64, 32x32, 16x16
- **How to create**:
  1. Create a 512x512 PNG image
  2. Use `iconutil` to convert: `iconutil -c icns icon.iconset`
  3. Or use online converter: https://cloudconvert.com/png-to-icns

### Windows Icon (icon.ico)
- **File**: `icon.ico`
- **Format**: Windows icon format
- **Sizes**: Should include 256x256, 48x48, 32x32, 16x16
- **How to create**:
  1. Create a 256x256 PNG image
  2. Use online converter: https://cloudconvert.com/png-to-ico
  3. Or use ImageMagick: `convert icon.png -define icon:auto-resize=256,48,32,16 icon.ico`

## Temporary Placeholder

Until actual icons are created, the build scripts will work without icons (PyInstaller will use default icons).

