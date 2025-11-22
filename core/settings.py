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
        self.settings_file = Path("data/settings.json")  # Keep for backward compatibility
        self.settings_file.parent.mkdir(parents=True, exist_ok=True)
    
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
            "window_state": None
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


