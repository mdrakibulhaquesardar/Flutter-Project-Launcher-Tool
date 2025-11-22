"""Plugin registry management for Flutter Project Launcher Tool."""
import json
from pathlib import Path
from typing import List, Dict, Optional, Any
from datetime import datetime
from core.logger import Logger
from utils.file_utils import read_json, write_json, ensure_directory


class PluginRegistry:
    """Manages plugin metadata registry in JSON format."""
    
    def __init__(self, plugins_dir: Optional[Path] = None):
        self.logger = Logger()
        if plugins_dir is None:
            plugins_dir = Path("plugins")
        self.plugins_dir = Path(plugins_dir)
        self.registry_file = self.plugins_dir / ".registry.json"
        ensure_directory(str(self.plugins_dir))
        self._init_registry()
    
    def _init_registry(self):
        """Initialize registry file if it doesn't exist."""
        if not self.registry_file.exists():
            self._write_registry({"plugins": []})
    
    def _read_registry(self) -> Dict[str, Any]:
        """Read registry from JSON file."""
        try:
            if self.registry_file.exists():
                return read_json(str(self.registry_file))
            return {"plugins": []}
        except Exception as e:
            self.logger.error(f"Error reading plugin registry: {e}")
            return {"plugins": []}
    
    def _write_registry(self, data: Dict[str, Any]):
        """Write registry to JSON file."""
        try:
            write_json(str(self.registry_file), data)
        except Exception as e:
            self.logger.error(f"Error writing plugin registry: {e}")
    
    def get_all_plugins(self) -> List[Dict[str, Any]]:
        """Get all registered plugins."""
        registry = self._read_registry()
        return registry.get("plugins", [])
    
    def get_plugin(self, plugin_id: str) -> Optional[Dict[str, Any]]:
        """Get plugin by ID."""
        plugins = self.get_all_plugins()
        for plugin in plugins:
            if plugin.get("id") == plugin_id:
                return plugin
        return None
    
    def register_plugin(self, plugin_id: str, name: str, version: str, 
                        author: str, description: str, plugin_type: str,
                        path: str, enabled: bool = True) -> bool:
        """Register a new plugin or update existing one."""
        try:
            registry = self._read_registry()
            plugins = registry.get("plugins", [])
            
            # Remove existing plugin with same ID
            plugins = [p for p in plugins if p.get("id") != plugin_id]
            
            # Add new plugin entry
            plugin_entry = {
                "id": plugin_id,
                "name": name,
                "version": version,
                "author": author,
                "description": description,
                "plugin_type": plugin_type,
                "path": str(path),
                "enabled": enabled,
                "installed_at": datetime.now().isoformat()
            }
            plugins.append(plugin_entry)
            
            registry["plugins"] = plugins
            self._write_registry(registry)
            self.logger.info(f"Registered plugin: {plugin_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error registering plugin {plugin_id}: {e}")
            return False
    
    def unregister_plugin(self, plugin_id: str) -> bool:
        """Remove plugin from registry."""
        try:
            registry = self._read_registry()
            plugins = registry.get("plugins", [])
            plugins = [p for p in plugins if p.get("id") != plugin_id]
            registry["plugins"] = plugins
            self._write_registry(registry)
            self.logger.info(f"Unregistered plugin: {plugin_id}")
            return True
        except Exception as e:
            self.logger.error(f"Error unregistering plugin {plugin_id}: {e}")
            return False
    
    def set_plugin_enabled(self, plugin_id: str, enabled: bool) -> bool:
        """Enable or disable a plugin."""
        try:
            registry = self._read_registry()
            plugins = registry.get("plugins", [])
            
            for plugin in plugins:
                if plugin.get("id") == plugin_id:
                    plugin["enabled"] = enabled
                    registry["plugins"] = plugins
                    self._write_registry(registry)
                    self.logger.info(f"Set plugin {plugin_id} enabled={enabled}")
                    return True
            
            return False
        except Exception as e:
            self.logger.error(f"Error setting plugin enabled state: {e}")
            return False
    
    def is_plugin_enabled(self, plugin_id: str) -> bool:
        """Check if plugin is enabled."""
        plugin = self.get_plugin(plugin_id)
        if plugin:
            return plugin.get("enabled", False)
        return False
    
    def get_enabled_plugins(self) -> List[Dict[str, Any]]:
        """Get all enabled plugins."""
        plugins = self.get_all_plugins()
        return [p for p in plugins if p.get("enabled", False)]

