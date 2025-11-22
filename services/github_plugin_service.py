"""GitHub plugin store service for fetching plugins from GitHub repository."""
import json
import requests
from pathlib import Path
from typing import List, Dict, Optional, Any
from core.logger import Logger
from utils.file_utils import read_json, write_json


class GitHubPluginService:
    """Service for fetching plugins from GitHub repository."""
    
    def __init__(self, repo_owner: str = "mdrakibulhaquesardar", 
                 repo_name: str = "Flutter-Project-Launcher-Tool"):
        self.logger = Logger()
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.base_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}"
        self.raw_base_url = f"https://raw.githubusercontent.com/{repo_owner}/{repo_name}/main"
        self.cache_file = Path.home() / ".flutter_launcher" / "cache" / "github_plugins.json"
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)
    
    def fetch_plugins_from_github(self, use_cache: bool = True) -> List[Dict[str, Any]]:
        """Fetch available plugins from GitHub repository."""
        # Check cache first
        if use_cache and self.cache_file.exists():
            try:
                cache_data = read_json(str(self.cache_file))
                # Cache valid for 1 hour
                import time
                if time.time() - cache_data.get("cached_at", 0) < 3600:
                    self.logger.info("Using cached plugin list")
                    return cache_data.get("plugins", [])
            except Exception as e:
                self.logger.warning(f"Error reading cache: {e}")
        
        try:
            # Fetch plugins directory structure from GitHub API
            plugins_url = f"{self.base_url}/contents/plugins"
            response = requests.get(plugins_url, timeout=10)
            
            if response.status_code != 200:
                self.logger.error(f"Failed to fetch plugins: {response.status_code}")
                return []
            
            plugins_data = response.json()
            plugins = []
            
            # Filter for directories only
            plugin_dirs = [item for item in plugins_data if item.get("type") == "dir" 
                          and not item.get("name").startswith(".")]
            
            for plugin_dir in plugin_dirs:
                plugin_id = plugin_dir.get("name")
                
                # Fetch plugin.json
                plugin_json_url = f"{self.raw_base_url}/plugins/{plugin_id}/plugin.json"
                try:
                    json_response = requests.get(plugin_json_url, timeout=5)
                    if json_response.status_code == 200:
                        plugin_metadata = json_response.json()
                        
                        # Add GitHub-specific info
                        plugin_info = {
                            "id": plugin_id,
                            "name": plugin_metadata.get("name", plugin_id),
                            "version": plugin_metadata.get("version", "1.0.0"),
                            "author": plugin_metadata.get("author", "Unknown"),
                            "description": plugin_metadata.get("description", ""),
                            "plugin_type": plugin_metadata.get("plugin_type", "general"),
                            "download_url": f"{self.raw_base_url}/plugins/{plugin_id}",
                            "repository": "github",
                            "repo_owner": self.repo_owner,
                            "repo_name": self.repo_name,
                            "branch": "main"
                        }
                        plugins.append(plugin_info)
                except Exception as e:
                    self.logger.warning(f"Error fetching plugin {plugin_id}: {e}")
                    continue
            
            # Cache the results
            try:
                import time
                cache_data = {
                    "plugins": plugins,
                    "cached_at": time.time()
                }
                write_json(str(self.cache_file), cache_data)
            except Exception as e:
                self.logger.warning(f"Error caching plugins: {e}")
            
            return plugins
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Network error fetching plugins: {e}")
            return []
        except Exception as e:
            self.logger.error(f"Error fetching plugins from GitHub: {e}")
            return []
    
    def download_plugin(self, plugin_id: str, download_url: str, 
                       target_dir: Path) -> bool:
        """Download plugin from GitHub and extract to target directory."""
        try:
            import tempfile
            import shutil
            
            # Create temp directory
            temp_dir = Path(tempfile.mkdtemp())
            
            # First, check if plugin exists in GitHub using API
            plugin_api_url = f"{self.base_url}/contents/plugins/{plugin_id}"
            try:
                api_response = requests.get(plugin_api_url, timeout=10)
                if api_response.status_code != 200:
                    self.logger.error(f"Plugin {plugin_id} not found in GitHub: {api_response.status_code}")
                    shutil.rmtree(temp_dir)
                    return False
                
                plugin_contents = api_response.json()
                if not isinstance(plugin_contents, list):
                    self.logger.error(f"Invalid plugin structure in GitHub")
                    shutil.rmtree(temp_dir)
                    return False
            except Exception as e:
                self.logger.error(f"Error checking plugin in GitHub: {e}")
                shutil.rmtree(temp_dir)
                return False
            
            # Download plugin files using GitHub API
            plugin_files = []
            for item in plugin_contents:
                if item.get("type") == "file":
                    file_name = item.get("name")
                    file_download_url = item.get("download_url")
                    if file_download_url and file_name in ["plugin.json", "main.py"]:
                        plugin_files.append((file_name, file_download_url))
            
            downloaded_files = []
            for file_name, file_url in plugin_files:
                try:
                    response = requests.get(file_url, timeout=10)
                    if response.status_code == 200:
                        file_path = temp_dir / file_name
                        file_path.parent.mkdir(parents=True, exist_ok=True)
                        file_path.write_bytes(response.content)
                        downloaded_files.append(file_name)
                        self.logger.info(f"Downloaded {file_name}")
                    else:
                        self.logger.warning(f"Failed to download {file_name}: {response.status_code}")
                except Exception as e:
                    self.logger.warning(f"Error downloading {file_name}: {e}")
            
            # Check if plugin.json was downloaded
            if "plugin.json" not in downloaded_files:
                self.logger.error("plugin.json not found in downloaded files")
                shutil.rmtree(temp_dir)
                return False
            
            # Check if main.py was downloaded (optional but recommended)
            if "main.py" not in downloaded_files:
                self.logger.warning("main.py not found, plugin may be incomplete")
            
            # Copy to target directory
            target_dir.mkdir(parents=True, exist_ok=True)
            for file_name in downloaded_files:
                src_file = temp_dir / file_name
                dst_file = target_dir / file_name
                if src_file.exists():
                    shutil.copy2(src_file, dst_file)
            
            # Try to download resources folder if exists (using GitHub API)
            try:
                resources_api_url = f"{self.base_url}/contents/plugins/{plugin_id}/resources"
                resources_response = requests.get(resources_api_url, timeout=5)
                if resources_response.status_code == 200:
                    resources_data = resources_response.json()
                    resources_dir = target_dir / "resources"
                    resources_dir.mkdir(exist_ok=True)
                    
                    # Download each file in resources
                    if isinstance(resources_data, list):
                        for resource_file in resources_data:
                            if resource_file.get("type") == "file":
                                file_name = resource_file.get("name")
                                file_url = resource_file.get("download_url")
                                if file_url:
                                    file_response = requests.get(file_url, timeout=10)
                                    if file_response.status_code == 200:
                                        file_path = resources_dir / file_name
                                        file_path.write_bytes(file_response.content)
            except:
                pass  # Resources folder is optional
            
            # Cleanup
            shutil.rmtree(temp_dir)
            
            self.logger.info(f"Downloaded plugin {plugin_id} successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error downloading plugin {plugin_id}: {e}", exc_info=True)
            return False
    
    def get_plugin_download_url(self, plugin_id: str) -> str:
        """Get download URL for a plugin."""
        return f"{self.raw_base_url}/plugins/{plugin_id}"

