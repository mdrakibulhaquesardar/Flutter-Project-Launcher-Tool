# Quick Start Guide

## Windows Setup

1. **Open Command Prompt or PowerShell** in the project directory

2. **Run setup script:**
   ```bash
   setup.bat
   ```
   This will:
   - Create a virtual environment
   - Install all dependencies (PyQt6, PyYAML)
   
   **Note:** The script works around PowerShell execution policy issues by using Python directly.

3. **Run the application:**
   ```bash
   run.bat
   ```
   Or directly (no activation needed):
   ```bash
   venv\Scripts\python.exe main.py
   ```
   
   **If you see PowerShell execution policy errors:** The scripts are designed to bypass this by calling Python directly. You can always use `venv\Scripts\python.exe main.py` instead.

## Linux/macOS Setup

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

## First Launch

1. **Configure Flutter SDK:**
   - Go to **Tools → Settings** (or press `Ctrl+,`)
   - Click **Auto-detect SDKs** to find your Flutter installation
   - Or manually **Add SDK** by selecting your Flutter SDK directory
   - Set a default SDK if you have multiple

2. **Create your first project:**
   - Click **➕ Create Project**
   - Enter project name and location
   - Click **Create Project**

## Troubleshooting

### "ModuleNotFoundError: No module named 'PyQt6'"
- Make sure you've run `setup.bat` (Windows) or `./setup.sh` (Linux/macOS)
- Activate the virtual environment before running

### "Flutter SDK not found"
- Configure Flutter SDK in Settings (Tools → Settings)
- Ensure Flutter is installed and accessible

### Application won't start
- Check that Python 3.8+ is installed: `python --version`
- Verify virtual environment is activated
- Check console for error messages

## Next Steps

- Read the full [README.md](README.md) for detailed documentation
- Explore the project structure
- Customize templates in `data/templates/`

