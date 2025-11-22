# FluStudio Branding Guide

## Overview

FluStudio now includes a comprehensive branding system that allows you to customize the application's visual identity with your own icons and branding elements.

## Branding Features

### 1. Application Icon
- **Window Icon**: Displayed in the window title bar and taskbar
- **Dialog Icons**: Applied to all dialogs (Settings, Project Creator, Project Details, etc.)
- **About Dialog**: Enhanced About dialog with logo support

### 2. Branding Configuration

All branding configuration is centralized in `core/branding.py`:

```python
class Branding:
    APP_NAME = "FluStudio"
    APP_VERSION = "1.0.0"
    ORGANIZATION_NAME = "FlutterTools"
    ORGANIZATION_DOMAIN = "fluttertools.dev"
```

## Adding Your Own Icons

### Step 1: Prepare Your Icons

Create the following icon files:

1. **app_icon.ico** (Windows)
   - Format: ICO
   - Recommended sizes: 16x16, 32x32, 48x48, 64x64, 128x128, 256x256
   - Location: `assets/icons/app_icon.ico`

2. **app_icon.png** (Cross-platform)
   - Format: PNG with transparency
   - Recommended size: 256x256 or 512x512 pixels
   - Location: `assets/icons/app_icon.png`

3. **logo.png** (Optional - for About dialog)
   - Format: PNG with transparency
   - Recommended size: 128x128 or 256x256 pixels
   - Location: `assets/icons/logo.png`

### Step 2: Place Icons

Place your icon files in the `assets/icons/` directory:

```
assets/
  icons/
    app_icon.ico      # Windows icon
    app_icon.png      # Cross-platform icon
    logo.png          # About dialog logo (optional)
```

### Step 3: Verify

After placing your icons, restart the application. The icons will automatically be applied to:
- Main window title bar
- All dialog windows
- About dialog
- Taskbar (Windows)

## Creating Placeholder Icons

If you don't have custom icons yet, you can generate placeholder icons using the provided script:

```bash
python utils/create_placeholder_icon.py
```

**Note**: This requires Pillow library:
```bash
pip install Pillow
```

The script will create:
- `assets/icons/app_icon.png` (256x256)
- `assets/icons/app_icon.ico` (Windows, multiple sizes)

## Customizing Branding Information

To change branding text (name, version, organization), edit `core/branding.py`:

```python
class Branding:
    APP_NAME = "YourAppName"
    APP_VERSION = "1.0.0"
    ORGANIZATION_NAME = "YourOrganization"
    ORGANIZATION_DOMAIN = "yourdomain.com"
```

## Branding API

### Using Branding in Your Code

```python
from core.branding import Branding
from PyQt6.QtGui import QIcon

# Get icon path
icon_path = Branding.get_app_icon_path()
if icon_path:
    icon = QIcon(str(icon_path))
    widget.setWindowIcon(icon)

# Apply icon to any widget
Branding.apply_window_icon(my_dialog)

# Get About dialog text
about_text = Branding.get_about_text()
```

## Icon Specifications

### Windows ICO File
- **Format**: ICO (multi-resolution)
- **Sizes**: 16, 32, 48, 64, 128, 256 pixels
- **Color depth**: 32-bit (RGBA) recommended
- **Tools**: 
  - Online: [ICO Convert](https://icoconvert.com/)
  - Desktop: IconWorkshop, GIMP with ICO plugin

### PNG File
- **Format**: PNG-24 or PNG-32 (with alpha channel)
- **Size**: 256x256 or 512x512 pixels
- **Background**: Transparent
- **Tools**: Any image editor (GIMP, Photoshop, etc.)

## Current Implementation

The branding system is integrated into:

- ✅ `main.py` - Application icon
- ✅ `ui/main_window.py` - Window icon and About dialog
- ✅ `ui/project_creator.py` - Dialog icon
- ✅ `ui/settings_dialog.py` - Dialog icon
- ✅ `ui/project_details_dialog.py` - Dialog icon

## Troubleshooting

### Icons Not Showing

1. **Check file paths**: Ensure icons are in `assets/icons/` directory
2. **Check file names**: Must be exactly `app_icon.ico` and `app_icon.png`
3. **Check file format**: ICO for Windows, PNG for cross-platform
4. **Restart application**: Icons are loaded at startup

### About Dialog Logo Not Showing

- Ensure `logo.png` exists in `assets/icons/`
- If not found, the app icon will be used instead
- Check that the image format is valid PNG

## Future Enhancements

Potential future branding features:
- Splash screen support
- Custom color themes
- Custom fonts
- Branded installer
- Application metadata (author, copyright, etc.)

