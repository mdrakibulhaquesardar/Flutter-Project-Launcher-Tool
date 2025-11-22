"""Settings management for Flutter Project Launcher Tool."""
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from core.database import Database
from core.logger import Logger


class Settings:
    """Database-based settings manager with JSON fallback."""
    
    def __init__(self):
        self.logger = Logger()
        self.db = Database()
        # Use user directory for settings file (backward compatibility)
        # Try to use app data directory, fallback to current directory if writable
        try:
            app_data_dir = Path.home() / ".flutter_launcher" / "data"
            app_data_dir.mkdir(parents=True, exist_ok=True)
            self.settings_file = app_data_dir / "settings.json"
        except Exception:
            # Fallback: try current directory, but don't fail if it doesn't work
            try:
                self.settings_file = Path("data/settings.json")
                self.settings_file.parent.mkdir(parents=True, exist_ok=True)
            except Exception:
                # If both fail, use a temp location (settings are in DB anyway)
                import tempfile
                self.settings_file = Path(tempfile.gettempdir()) / "flustudio_settings.json"
    
    def _default_settings(self) -> Dict[str, Any]:
        """Return default settings."""
        return {
            "flutter_sdks": [],
            "default_sdk": None,
            "default_project_location": str(Path.home() / "flutter_projects"),
            "theme": "light",
            "auto_scan": True,
            "scan_paths": [],
            "window_geometry": None,
            "window_state": None,
            "vscode_path": None,
            "android_studio_path": None,
            "debug_mode": False,
            "log_level": "INFO",
            "console_font_size": 9,
            "console_max_lines": 1000
        }
    
    def save(self):
        """Save settings to database (for backward compatibility)."""
        # Settings are saved immediately via set() method
        pass
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get setting value from database."""
        value = self.db.get_setting(key)
        if value is None:
            # Fallback to default settings
            defaults = self._default_settings()
            return defaults.get(key, default)
        
        # Convert string values to appropriate types based on default
        if isinstance(value, str):
            # Try to convert based on default type
            if default is not None:
                if isinstance(default, bool):
                    # Convert string to bool
                    return value.lower() in ('true', '1', 'yes', 'on')
                elif isinstance(default, int):
                    try:
                        return int(value)
                    except ValueError:
                        return default
                elif isinstance(default, float):
                    try:
                        return float(value)
                    except ValueError:
                        return default
                elif isinstance(default, list):
                    # Try to parse as JSON list
                    try:
                        parsed = json.loads(value)
                        if isinstance(parsed, list):
                            return parsed
                    except:
                        pass
                elif isinstance(default, dict):
                    # Try to parse as JSON dict
                    try:
                        parsed = json.loads(value)
                        if isinstance(parsed, dict):
                            return parsed
                    except:
                        pass
        
        return value
    
    def set(self, key: str, value: Any):
        """Set setting value in database."""
        self.db.set_setting(key, value)
    
    def add_flutter_sdk(self, sdk_path: str) -> bool:
        """Add Flutter SDK path."""
        sdks = self.get_flutter_sdks()
        if sdk_path not in sdks:
            sdks.append(sdk_path)
            self.set("flutter_sdks", sdks)
            return True
        return False
    
    def remove_flutter_sdk(self, sdk_path: str):
        """Remove Flutter SDK path."""
        sdks = self.get_flutter_sdks()
        if sdk_path in sdks:
            sdks.remove(sdk_path)
            self.set("flutter_sdks", sdks)
            if self.get_default_sdk() == sdk_path:
                self.set_default_sdk(None)
    
    def set_default_sdk(self, sdk_path: Optional[str]):
        """Set default Flutter SDK."""
        self.set("default_sdk", sdk_path)
    
    def get_flutter_sdks(self) -> List[str]:
        """Get list of Flutter SDK paths."""
        return self.get("flutter_sdks", [])
    
    def get_default_sdk(self) -> Optional[str]:
        """Get default Flutter SDK path."""
        return self.get("default_sdk")
    
    # Editor path methods
    def get_vscode_path(self) -> Optional[str]:
        """Get VS Code executable path."""
        return self.get("vscode_path")
    
    def set_vscode_path(self, path: Optional[str]):
        """Set VS Code executable path."""
        self.set("vscode_path", path)
    
    def get_android_studio_path(self) -> Optional[str]:
        """Get Android Studio executable path."""
        return self.get("android_studio_path")
    
    def set_android_studio_path(self, path: Optional[str]):
        """Set Android Studio executable path."""
        self.set("android_studio_path", path)
    
    # Advanced settings methods
    def get_debug_mode(self) -> bool:
        """Get debug mode setting."""
        return self.get("debug_mode", False)
    
    def set_debug_mode(self, enabled: bool):
        """Set debug mode."""
        self.set("debug_mode", enabled)
    
    def get_log_level(self) -> str:
        """Get log level setting."""
        return self.get("log_level", "INFO")
    
    def set_log_level(self, level: str):
        """Set log level."""
        if level in ["DEBUG", "INFO", "WARNING", "ERROR"]:
            self.set("log_level", level)
    
    def get_console_font_size(self) -> int:
        """Get console font size."""
        return self.get("console_font_size", 9)
    
    def set_console_font_size(self, size: int):
        """Set console font size."""
        self.set("console_font_size", max(6, min(24, size)))  # Clamp between 6-24
    
    def get_console_max_lines(self) -> int:
        """Get console max lines."""
        return self.get("console_max_lines", 1000)
    
    def set_console_max_lines(self, max_lines: int):
        """Set console max lines."""
        self.set("console_max_lines", max(100, min(10000, max_lines)))  # Clamp between 100-10000


