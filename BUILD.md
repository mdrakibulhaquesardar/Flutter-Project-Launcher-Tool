# Building FluStudio Executable and Installer

This guide explains how to build FluStudio as a standalone executable (.exe) and create an installer for distribution.

## Prerequisites

1. **Python 3.8+** installed
2. **Virtual Environment** (will be created automatically)
3. **Inno Setup** (for creating installer) - Download from [jrsoftware.org](https://jrsoftware.org/isdl.php)

## Quick Build

### Step 1: Build Executable

Run the build script:

```bash
build.bat
```

This will:
- Create/activate virtual environment
- Install dependencies (including PyInstaller)
- Build the executable using PyInstaller
- Output: `dist\FluStudio\FluStudio.exe`

### Step 2: Create Installer

After the executable is built, create the installer:

```bash
build_installer.bat
```

This will:
- Check if executable exists
- Compile the Inno Setup script
- Create installer: `dist\installer\FluStudio-Setup-1.0.0.exe`

## Manual Build Process

### 1. Setup Environment

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Build Executable

```bash
pyinstaller build_exe.spec --clean --noconfirm
```

### 3. Create Installer

Open `build_installer.iss` in Inno Setup Compiler and click "Compile".

Or use command line:
```bash
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" build_installer.iss
```

## Build Configuration

### PyInstaller Spec (`build_exe.spec`)

The spec file configures:
- **Application name**: FluStudio
- **Icon**: `assets/icons/app_icon.ico`
- **Data files**: assets, plugins, data directories
- **Hidden imports**: PyQt6 modules, yaml, requests, etc.
- **Console**: Disabled (GUI application)

### Inno Setup Script (`build_installer.iss`)

The installer script configures:
- **App name**: FluStudio
- **Version**: 1.0.0
- **Publisher**: NextCode Studio
- **Install location**: `C:\Program Files\FluStudio`
- **Desktop shortcut**: Optional
- **Start menu**: Yes
- **Uninstaller**: Included

## Output Files

After building:

```
dist/
├── FluStudio/              # Executable directory
│   ├── FluStudio.exe      # Main executable
│   ├── assets/            # Application assets
│   ├── plugins/            # Plugin files
│   └── [other files]      # Dependencies
└── installer/
    └── FluStudio-Setup-1.0.0.exe  # Installer
```

## Troubleshooting

### Build Fails

1. **Missing dependencies**: Run `pip install -r requirements.txt`
2. **PyInstaller not found**: Install with `pip install pyinstaller`
3. **Module not found**: Add to `hiddenimports` in `build_exe.spec`

### Executable Doesn't Run

1. **Check console output**: Temporarily set `console=True` in spec file
2. **Missing DLLs**: Check PyQt6 installation
3. **Path issues**: Ensure data files are included in `datas` list

### Installer Issues

1. **Inno Setup not found**: Install Inno Setup from official website
2. **EXE not found**: Run `build.bat` first
3. **Icon not found**: Ensure `assets/icons/app_icon.ico` exists

## Customization

### Change App Name/Version

Edit `core/branding.py`:
```python
APP_NAME = "YourAppName"
APP_VERSION = "1.0.0"
```

Then update `build_exe.spec` and `build_installer.iss` accordingly.

### Change Installer Settings

Edit `build_installer.iss`:
- `AppName`: Application name
- `AppVersion`: Version number
- `AppPublisher`: Publisher name
- `DefaultDirName`: Default install location
- `SetupIconFile`: Installer icon

### Add License File

1. Create `LICENSE.txt` in project root
2. Update `build_installer.iss`:
   ```iss
   LicenseFile=LICENSE.txt
   ```

### Add Additional Files

Edit `build_exe.spec`:
```python
datas = [
    (str(assets_dir), 'assets'),
    ('path/to/extra/file.txt', '.'),  # Add extra files
]
```

## Distribution

The installer (`FluStudio-Setup-1.0.0.exe`) can be distributed to users. They can:
1. Download the installer
2. Run it
3. Follow the installation wizard
4. Launch FluStudio from Start Menu or Desktop shortcut

## Testing

Before distribution, test:
1. ✅ Executable runs on clean Windows system
2. ✅ All features work correctly
3. ✅ Installer installs correctly
4. ✅ Uninstaller removes all files
5. ✅ Shortcuts work properly
6. ✅ Application data is stored correctly

## Advanced Options

### One-file Executable

To create a single-file executable, modify `build_exe.spec`:
```python
exe = EXE(
    # ... existing options ...
    onefile=True,  # Single file instead of directory
)
```

**Note**: One-file executables are slower to start but easier to distribute.

### Code Signing

To sign the executable (for Windows):
1. Obtain a code signing certificate
2. Add to `build_exe.spec`:
   ```python
   codesign_identity='Your Certificate Name'
   ```

### UPX Compression

UPX compression is enabled by default. To disable:
```python
exe = EXE(
    # ... existing options ...
    upx=False,
)
```

## Build Scripts

- `build.bat` - Builds executable
- `build_installer.bat` - Creates installer
- `build_exe.spec` - PyInstaller configuration
- `build_installer.iss` - Inno Setup script

## Notes

- The executable includes all dependencies (PyQt6, PyYAML, etc.)
- Total size: ~100-150 MB (typical for PyQt6 applications)
- No Python installation required on target system
- First launch may be slower (extracting files)

