# FluStudio

A cross-platform desktop application for managing Flutter projects, built with Python and PyQt6.

## Features

- 🚀 **Project Creation** - Create new Flutter projects with templates
- 📊 **Project Dashboard** - View and manage recent projects
- 🔍 **Project Scanner** - Automatically detect Flutter projects on your system
- 🔧 **Flutter SDK Manager** - Manage multiple Flutter SDK installations
- 📦 **Quick Actions** - Run, build, clean projects with one click
- 🎨 **Template Manager** - Create and use custom project templates
- 📱 **Device Management** - View connected devices and emulators
- 📝 **Log Console** - Real-time command output with error highlighting

## Requirements

- Python 3.8 or higher
- Flutter SDK installed
- PyQt6

## Installation

### Windows Setup

1. **Open Command Prompt or PowerShell** in the project directory

2. **Run setup script:**
   ```bash
   setup.bat
   ```
   This will:
   - Create a virtual environment
   - Install all dependencies (PyQt6, PyYAML)

3. **Run the application:**
   ```bash
   run.bat
   ```
   Or directly:
   ```bash
   venv\Scripts\python.exe main.py
   ```

**Note:** If you encounter PowerShell execution policy errors, the scripts are designed to work around this by using the Python executable directly.

### Linux/macOS Setup

1. **Open Terminal** in the project directory

2. **Make scripts executable (first time only):**
   ```bash
   chmod +x setup.sh run.sh
   ```

3. **Run setup script:**
   ```bash
   ./setup.sh
   ```
   This will:
   - Create a virtual environment
   - Install all dependencies (PyQt6, PyYAML)

4. **Run the application:**
   ```bash
   ./run.sh
   ```
   Or manually:
   ```bash
   source venv/bin/activate
   python main.py
   ```

## Usage

### First Time Setup

1. Launch the application
2. Go to **Tools → Settings** (or press `Ctrl+,`)
3. In the **Flutter SDK** tab:
   - Click **Auto-detect SDKs** to find existing installations
   - Or manually **Add SDK** by selecting your Flutter SDK directory
   - Set a default SDK if you have multiple installations

### Creating a New Project

1. Click **➕ Create Project** button or use `Ctrl+N`
2. Enter project name
3. Select project location
4. Choose a template (optional)
5. Click **Create Project**

### Managing Projects

- **Run Project**: Select a project and click **🏃 Run**
- **Build APK**: Click **📦 Build APK** to build Android APK
- **Build Bundle**: Click **🎁 Build Bundle** to build Android App Bundle
- **Pub Get**: Click **🔄 Pub Get** to fetch dependencies
- **Clean**: Click **♻ Clean** to clean build files
- **Open in Editor**: Use **📝 VS Code** or **🛠 Android Studio** buttons
- **Open Folder**: Click **📂 Open Folder** to open in file explorer

### Scanning for Projects

1. Go to **Tools → Scan for Projects...**
2. Select a directory to scan
3. Found projects will be added to your dashboard

## Project Structure

```
FluStudio/
├── main.py                 # Application entry point
├── requirements.txt        # Python dependencies
├── README.md              # This file
├── QUICKSTART.md          # Quick start guide
├── setup.bat / setup.sh   # Setup scripts
├── run.bat / run.sh       # Run scripts
│
├── core/                  # Core utilities
│   ├── commands.py       # Command execution
│   ├── logger.py         # Logging
│   └── settings.py       # Settings management
│
├── services/             # Business logic
│   ├── flutter_service.py
│   ├── project_service.py
│   ├── template_service.py
│   └── device_service.py
│
├── ui/                   # UI components
│   ├── main_window.py
│   ├── dashboard_widget.py
│   ├── project_creator.py
│   ├── settings_dialog.py
│   └── console_widget.py
│
├── widgets/              # Reusable widgets
│   ├── project_item.py
│   ├── template_item.py
│   └── command_console.py
│
├── utils/                # Utilities
│   ├── file_utils.py
│   └── path_utils.py
│
├── data/                 # Data storage
│   ├── projects.json
│   ├── settings.json
│   └── templates/
│
└── assets/               # Static resources
    ├── icons/
    └── styles/
```

## Configuration

Application settings are stored in `data/settings.json`. You can also manage settings through the UI.

Project metadata is stored in `data/projects.json`.

Logs are stored in `~/.flutter_launcher/logs/`.

## Troubleshooting

### PowerShell Execution Policy Error

If you see an error about execution policies when activating the virtual environment:

**Solution 1 (Recommended):** Use the provided scripts which work around this issue:
```bash
run.bat
```

**Solution 2:** Run Python directly:
```bash
venv\Scripts\python.exe main.py
```

**Solution 3:** Change execution policy (requires admin):
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Flutter SDK Not Found

1. Ensure Flutter SDK is installed
2. Go to **Settings → Flutter SDK**
3. Click **Auto-detect SDKs** or manually add SDK path

### Projects Not Showing

1. Click **🔄 Refresh** button
2. Or go to **Tools → Scan for Projects...** to scan directories

### Command Execution Errors

- Check that Flutter SDK is properly configured
- Verify Flutter is in your system PATH (or configure SDK in settings)
- Check the console output for detailed error messages

### ModuleNotFoundError

- Make sure you've run `setup.bat` (Windows) or `./setup.sh` (Linux/macOS)
- Verify virtual environment exists: `venv\Scripts\python.exe` (Windows) or `venv/bin/python` (Linux/macOS)

## Development

### Running in Development Mode

**Windows:**
```bash
venv\Scripts\python.exe main.py
```

**Linux/macOS:**
```bash
source venv/bin/activate
python main.py
```

### Code Style

- Follow PEP 8 Python style guide
- Use type hints where possible
- Document functions and classes

## License

[Add your license here]

## Contributing

[Add contribution guidelines here]

## Support

[Add support information here]
