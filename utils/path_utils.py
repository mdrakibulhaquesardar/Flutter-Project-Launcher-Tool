"""Path utilities for Flutter Project Launcher Tool."""
import os
from pathlib import Path
from typing import Optional


def validate_flutter_sdk(sdk_path: str) -> bool:
    """Validate if a path contains a valid Flutter SDK."""
    sdk = Path(sdk_path)
    if not sdk.exists() or not sdk.is_dir():
        return False
    
    # Check for Flutter executable
    flutter_bin = sdk / "bin" / "flutter"
    if os.name == 'nt':
        flutter_bin = sdk / "bin" / "flutter.bat"
    
    return flutter_bin.exists()


def get_flutter_executable(sdk_path: Optional[str] = None) -> Optional[str]:
    """Get Flutter executable path."""
    if sdk_path:
        sdk = Path(sdk_path)
        if os.name == 'nt':
            flutter_exe = sdk / "bin" / "flutter.bat"
        else:
            flutter_exe = sdk / "bin" / "flutter"
        
        if flutter_exe.exists():
            return str(flutter_exe)
    
    # Fallback to system PATH
    return "flutter"


def normalize_path(path: str) -> str:
    """Normalize path for cross-platform compatibility."""
    return str(Path(path).resolve())


def expand_user_path(path: str) -> str:
    """Expand user home directory in path."""
    return str(Path(path).expanduser())


