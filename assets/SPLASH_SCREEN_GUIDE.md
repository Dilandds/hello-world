# Splash Screen Logo Guide

## Logo Requirements

### Recommended Sizes

**For Splash Screen Image:**
- **Optimal Size**: 600x450 pixels (4:3 aspect ratio)
- **Alternative Sizes**: 
  - 800x600 pixels (larger, higher quality)
  - 400x300 pixels (smaller, faster loading)
- **Format**: PNG (preferred) or JPG
- **Background**: Should match app theme (#121212 dark background recommended)

### Logo Placement

The logo will be displayed centered on the splash screen. The loading message appears at the bottom.

## How to Add Your Logo

1. **Create or prepare your logo image**
   - Size: 600x450 pixels (or one of the recommended sizes)
   - Format: PNG (with transparency) or JPG
   - Background: Transparent PNG or dark background (#121212)

2. **Save the image to the assets folder**
   - Place your image in: `assets/splash.png` (preferred)
   - Or use one of these alternative names:
     - `assets/splash.jpg`
     - `assets/logo.png`
     - `assets/logo.jpg`

3. **Rebuild the application**
   ```bash
   ./build_mac.sh
   ```

## Design Tips

- **Keep it simple**: The splash screen shows briefly, so a simple, recognizable logo works best
- **Use high contrast**: Ensure your logo is visible on dark backgrounds
- **Consider transparency**: PNG with transparency allows the dark background to show through
- **File size**: Keep the image under 500KB for faster loading
- **Aspect ratio**: Stick to 4:3 ratio (width:height) for best results

## Example Splash Screen Layout

```
┌─────────────────────────────┐
│                             │
│                             │
│      [Your Logo Here]       │
│                             │
│                             │
│                             │
│                             │
│  Loading Jewelry STL        │
│  Analyzer...                │
└─────────────────────────────┘
```

The loading message appears at the bottom in gold color (#D4AF37).

## Testing

After adding your logo, test the splash screen:
1. Run the app from the built .app bundle
2. The splash screen should appear immediately with your logo
3. It will disappear when the main window is ready

## Troubleshooting

- **Logo not showing?** 
  - Check that the file exists in `assets/` folder
  - Verify the filename matches one of: `splash.png`, `splash.jpg`, `logo.png`, or `logo.jpg`
  - Rebuild the app after adding the image

- **Logo too small/large?**
  - Resize your image to 600x450 pixels for optimal display
  - The splash screen will scale the image to fit

- **Logo looks blurry?**
  - Use a higher resolution image (800x600 or larger)
  - Ensure you're using PNG format for best quality
