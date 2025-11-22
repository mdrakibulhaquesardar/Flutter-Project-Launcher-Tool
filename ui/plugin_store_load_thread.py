"""Background thread for loading plugin store data."""
from PyQt6.QtCore import QThread, pyqtSignal
from services.github_plugin_service import GitHubPluginService
from pathlib import Path
from typing import List, Dict, Any
from utils.file_utils import read_json


class PluginStoreLoadThread(QThread):
    """Thread for async plugin store data loading."""
    progress = pyqtSignal(str)  # Progress message
    finished = pyqtSignal(list, list)  # (github_plugins, local_plugins)
    error = pyqtSignal(str)  # Error message
    
    def __init__(self, use_cache: bool = False):
        super().__init__()
        self.use_cache = use_cache
        self.github_service = GitHubPluginService()
    
    def run(self):
        """Execute plugin store loading."""
        github_plugins = []
        local_plugins = []
        
        try:
            # Load GitHub plugins
            self.progress.emit("Fetching plugins from GitHub...")
            try:
                github_plugins = self.github_service.fetch_plugins_from_github(use_cache=self.use_cache)
                self.progress.emit(f"Fetched {len(github_plugins)} plugins from GitHub")
            except Exception as e:
                self.progress.emit(f"Error fetching from GitHub: {str(e)}")
                github_plugins = []
            
            # Load local plugins
            self.progress.emit("Loading local plugins...")
            store_file = Path("data/plugin_store.json")
            if store_file.exists():
                try:
                    store_data = read_json(str(store_file))
                    local_plugins = store_data.get("plugins", [])
                    self.progress.emit(f"Loaded {len(local_plugins)} local plugins")
                except Exception as e:
                    self.progress.emit(f"Error loading local plugins: {str(e)}")
                    local_plugins = []
            
            self.progress.emit(f"Loaded {len(github_plugins)} GitHub and {len(local_plugins)} local plugins")
            self.finished.emit(github_plugins, local_plugins)
        except Exception as e:
            self.error.emit(f"Error loading plugin store: {str(e)}")
            self.finished.emit([], [])

