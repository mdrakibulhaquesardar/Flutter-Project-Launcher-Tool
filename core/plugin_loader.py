"""Plugin loader for Flutter Project Launcher Tool."""
import importlib.util
import sys
from pathlib import Path
from typing import Dict, Optional, Any, List
from core.logger import Logger
from core.plugin_registry import PluginRegistry
from core.plugin_api import PluginAPI


class PluginLoader:
    """Manages plugin discovery, loading, and lifecycle."""
    
    def __init__(self, plugins_dir: Optional[Path] = None, app_instance=None):
        self.logger = Logger()
        self.registry = PluginRegistry(plugins_dir)
        self.api = PluginAPI(app_instance)
        self.app_instance = app_instance
        
        # Loaded plugin modules
        self._loaded_plugins: Dict[str, Any] = {}
        self._plugin_modules: Dict[str, Any] = {}
    
    def load_plugins(self) -> int:
        """Load all enabled plugins."""
        # Auto-register plugins that exist but aren't in registry
        self._auto_register_plugins()
        
        enabled_plugins = self.registry.get_enabled_plugins()
        loaded_count = 0
        
        for plugin_info in enabled_plugins:
            plugin_id = plugin_info.get("id")
            if plugin_id and self.load_plugin(plugin_id):
                loaded_count += 1
        
        self.logger.info(f"Loaded {loaded_count} plugin(s)")
        return loaded_count
    
    def _auto_register_plugins(self):
        """Auto-register plugins that exist in plugins directory but aren't registered."""
        plugins_dir = self.registry.plugins_dir
        
        if not plugins_dir.exists():
            return
        
        # Scan for plugin directories
        for item in plugins_dir.iterdir():
            if not item.is_dir() or item.name.startswith('.'):
                continue
            
            plugin_id = item.name
            plugin_json = item / "plugin.json"
            
            # Skip if already registered
            if self.registry.get_plugin(plugin_id):
                continue
            
            # Try to register if plugin.json exists
            if plugin_json.exists():
                try:
                    metadata = self._load_plugin_json(plugin_json)
                    if metadata:
                        self.registry.register_plugin(
                            plugin_id=plugin_id,
                            name=metadata.get("name", plugin_id),
                            version=metadata.get("version", "1.0.0"),
                            author=metadata.get("author", "Unknown"),
                            description=metadata.get("description", ""),
                            plugin_type=metadata.get("plugin_type", "general"),
                            path=str(item),
                            enabled=metadata.get("enabled", True)
                        )
                        self.logger.info(f"Auto-registered plugin: {plugin_id}")
                except Exception as e:
                    self.logger.warning(f"Failed to auto-register plugin {plugin_id}: {e}")
    
    def load_plugin(self, plugin_id: str) -> bool:
        """Load a single plugin."""
        try:
            plugin_info = self.registry.get_plugin(plugin_id)
            if not plugin_info:
                self.logger.warning(f"Plugin not found in registry: {plugin_id}")
                return False
            
            if not plugin_info.get("enabled", False):
                self.logger.debug(f"Plugin {plugin_id} is disabled, skipping")
                return False
            
            plugin_path = Path(plugin_info.get("path"))
            if not plugin_path.exists():
                self.logger.error(f"Plugin path does not exist: {plugin_path}")
                return False
            
            # Load plugin.json
            plugin_json_path = plugin_path / "plugin.json"
            if not plugin_json_path.exists():
                self.logger.error(f"plugin.json not found: {plugin_json_path}")
                return False
            
            plugin_metadata = self._load_plugin_json(plugin_json_path)
            if not plugin_metadata:
                return False
            
            # Validate required fields
            required_fields = ["name", "id", "version", "entry"]
            for field in required_fields:
                if field not in plugin_metadata:
                    self.logger.error(f"Plugin {plugin_id} missing required field: {field}")
                    return False
            
            # Load plugin entry point
            entry_file = plugin_path / plugin_metadata.get("entry", "main.py")
            if not entry_file.exists():
                self.logger.error(f"Plugin entry file not found: {entry_file}")
                return False
            
            # Dynamically import plugin module
            spec = importlib.util.spec_from_file_location(
                f"plugin_{plugin_id}",
                str(entry_file)
            )
            
            if spec is None or spec.loader is None:
                self.logger.error(f"Failed to create spec for plugin {plugin_id}")
                return False
            
            module = importlib.util.module_from_spec(spec)
            
            # Add plugin path to sys.path temporarily for imports
            plugin_parent = str(plugin_path.parent)
            if plugin_parent not in sys.path:
                sys.path.insert(0, plugin_parent)
            
            try:
                spec.loader.exec_module(module)
                
                # Call initialize function if it exists
                if hasattr(module, "initialize"):
                    module.initialize(self.api)
                    self.logger.info(f"Initialized plugin: {plugin_id}")
                else:
                    self.logger.warning(f"Plugin {plugin_id} has no initialize() function")
                
                self._loaded_plugins[plugin_id] = plugin_info
                self._plugin_modules[plugin_id] = module
                
                return True
                
            except Exception as e:
                self.logger.error(f"Error loading plugin {plugin_id}: {e}", exc_info=True)
                return False
            finally:
                # Remove plugin path from sys.path
                if plugin_parent in sys.path:
                    sys.path.remove(plugin_parent)
        
        except Exception as e:
            self.logger.error(f"Error loading plugin {plugin_id}: {e}", exc_info=True)
            return False
    
    def unload_plugin(self, plugin_id: str) -> bool:
        """Unload a plugin."""
        try:
            if plugin_id in self._loaded_plugins:
                # Call cleanup function if it exists
                module = self._plugin_modules.get(plugin_id)
                if module and hasattr(module, "cleanup"):
                    try:
                        module.cleanup()
                    except Exception as e:
                        self.logger.warning(f"Error calling cleanup for plugin {plugin_id}: {e}")
                
                del self._loaded_plugins[plugin_id]
                if plugin_id in self._plugin_modules:
                    del self._plugin_modules[plugin_id]
                
                self.logger.info(f"Unloaded plugin: {plugin_id}")
                return True
            
            return False
        except Exception as e:
            self.logger.error(f"Error unloading plugin {plugin_id}: {e}")
            return False
    
    def reload_plugin(self, plugin_id: str) -> bool:
        """Reload a plugin."""
        self.unload_plugin(plugin_id)
        return self.load_plugin(plugin_id)
    
    def get_plugin(self, plugin_id: str) -> Optional[Dict[str, Any]]:
        """Get loaded plugin info."""
        return self._loaded_plugins.get(plugin_id)
    
    def get_all_plugins(self) -> Dict[str, Dict[str, Any]]:
        """Get all loaded plugins."""
        return self._loaded_plugins.copy()
    
    def _load_plugin_json(self, json_path: Path) -> Optional[Dict[str, Any]]:
        """Load and validate plugin.json."""
        try:
            from utils.file_utils import read_json
            metadata = read_json(str(json_path))
            
            # Basic validation
            if not isinstance(metadata, dict):
                self.logger.error(f"Invalid plugin.json format: {json_path}")
                return None
            
            return metadata
        except Exception as e:
            self.logger.error(f"Error loading plugin.json {json_path}: {e}")
            return None
    
    def execute_plugin_hook(self, plugin_id: str, hook_name: str, *args, **kwargs) -> Any:
        """Execute a plugin hook function."""
        module = self._plugin_modules.get(plugin_id)
        if module and hasattr(module, hook_name):
            try:
                hook_func = getattr(module, hook_name)
                return hook_func(*args, **kwargs)
            except Exception as e:
                self.logger.error(f"Error executing hook {hook_name} for plugin {plugin_id}: {e}")
                return None
        return None
    
    def get_api(self) -> PluginAPI:
        """Get PluginAPI instance."""
        return self.api

