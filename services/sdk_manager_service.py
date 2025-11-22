"""Flutter SDK Manager service for downloading and managing SDK versions."""
import json
import zipfile
import shutil
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from core.logger import Logger
from core.settings import Settings
from utils.downloader import Downloader
from utils.path_manager import PathManager
from utils.path_utils import validate_flutter_sdk
import requests
import os


class SDKManagerService:
    """Service for managing Flutter SDK versions."""
    
    def __init__(self):
        self.logger = Logger()
        self.settings = Settings()
        self.downloader = Downloader()
        self.path_manager = PathManager()
        self.sdk_base_dir = Path.home() / ".flutter_launcher" / "sdks"
        self.sdk_base_dir.mkdir(parents=True, exist_ok=True)
        
        # Cache directory for versions JSON (like FVM)
        self.cache_dir = Path.home() / ".flutter_launcher" / "cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.versions_cache_file = self.cache_dir / "flutter_versions.json"
        self.cache_max_age_hours = 24  # Update cache every 24 hours
    
    def get_available_versions(self, use_cache: bool = True) -> List[Dict[str, Any]]:
        """
        Fetch available Flutter versions directly from FVM's GitHub JSON files.
        Uses cached JSON if available and fresh, otherwise fetches from FVM repo.
        
        Args:
            use_cache: Whether to use cached versions if available
        
        Returns:
            List of version dictionaries with version, channel, release_date, etc.
        """
        # Check cache first (like FVM)
        if use_cache and self._is_cache_valid():
            cached_versions = self._load_cached_versions()
            if cached_versions:
                self.logger.info(f"Using cached versions ({len(cached_versions)} versions)")
                return cached_versions
        
        # Get platform-specific FVM releases JSON URL
        system = "windows" if os.name == 'nt' else "macos" if os.name == 'darwin' else "linux"
        fvm_releases_url = f"https://raw.githubusercontent.com/leoafarias/fvm/main/releases_{system}.json"
        
        self.logger.info(f"Fetching Flutter versions from FVM: {fvm_releases_url}")
        
        versions = []  # Initialize versions list
        
        try:
            response = requests.get(fvm_releases_url, timeout=15)
            response.raise_for_status()
            
            releases_data = response.json()
            releases = releases_data.get("releases", [])
            
            self.logger.info(f"Found {len(releases)} Flutter releases from FVM JSON")
            
            # Parse FVM JSON format
            for release in releases:
                version = release.get("version", "")
                channel = release.get("channel", "stable")
                release_date = release.get("release_date", "")
                hash_value = release.get("hash", "")
                archive = release.get("archive", "")
                
                # Skip if no version
                if not version:
                    continue
                
                # FVM JSON already has channel, but ensure it's valid
                if channel not in ["stable", "beta", "dev"]:
                    # Determine channel from version string if not explicit
                    version_lower = version.lower()
                    if "beta" in version_lower:
                        channel = "beta"
                    elif "dev" in version_lower or "-" in version or ".pre" in version:
                        channel = "dev"
                    else:
                        channel = "stable"
                
                # Use archive URL if available (construct full URL if relative), otherwise construct
                if archive:
                    # FVM JSON provides relative paths like "stable/windows/flutter_windows_3.38.3-stable.zip"
                    if archive.startswith("http"):
                        download_url = archive
                    else:
                        # Construct full URL from relative path
                        base_url = "https://storage.googleapis.com/flutter_infra_release/releases"
                        download_url = f"{base_url}/{archive}"
                else:
                    download_url = self._get_download_url(version, channel)
                
                versions.append({
                    "version": version,
                    "channel": channel,
                    "release_date": release_date,
                    "hash": hash_value,
                    "archive": archive,
                    "download_url": download_url,
                    "tag": version,
                    "name": f"Flutter {version} ({channel})",
                    "prerelease": channel != "stable"
                })
            
            # Sort by release date (newest first), then by version
            def sort_key(v):
                date = v.get("release_date", "")
                version_str = v.get("version", "0.0.0")
                # Handle version parsing (e.g., "3.24.0", "3.24.0-1.2.pre", "3.24.0-dev.1")
                try:
                    # Extract numeric parts
                    version_match = re.match(r'(\d+)\.(\d+)\.(\d+)', version_str)
                    if version_match:
                        version_parts = tuple(map(int, version_match.groups()))
                    else:
                        version_parts = (0, 0, 0)
                except:
                    version_parts = (0, 0, 0)
                return (date, version_parts)
            
            versions.sort(key=sort_key, reverse=True)
            
            # Save to cache (like FVM)
            self._save_versions_to_cache(versions)
            
            self.logger.info(f"Returning {len(versions)} Flutter versions")
            return versions
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Network error fetching Flutter versions from FVM: {e}")
            # Fallback to GitHub tags API if FVM JSON fails
            self.logger.info("Falling back to GitHub tags API")
            releases = self._fetch_all_github_tags()
            versions = []
            for release in releases:
                version = release.get("version", "")
                channel = release.get("channel", "stable")
                versions.append({
                    "version": version,
                    "channel": channel,
                    "release_date": release.get("release_date", ""),
                    "hash": release.get("hash", ""),
                    "archive": release.get("archive", ""),
                    "download_url": self._get_download_url(version, channel),
                    "tag": release.get("tag", version),
                    "name": f"Flutter {version} ({channel})",
                    "prerelease": channel != "stable"
                })
            # Sort and cache
            def sort_key(v):
                date = v.get("release_date", "")
                version_str = v.get("version", "0.0.0")
                try:
                    version_match = re.match(r'(\d+)\.(\d+)\.(\d+)', version_str)
                    if version_match:
                        version_parts = tuple(map(int, version_match.groups()))
                    else:
                        version_parts = (0, 0, 0)
                except:
                    version_parts = (0, 0, 0)
                return (date, version_parts)
            versions.sort(key=sort_key, reverse=True)
            self._save_versions_to_cache(versions)
            return versions
        except Exception as e:
            self.logger.error(f"Error fetching Flutter versions: {e}")
            # Fallback to GitHub API
            return self._get_versions_from_github_fallback()
    
    def _fetch_all_github_tags(self) -> List[Dict[str, Any]]:
        """
        Fetch all Flutter tags from GitHub API with pagination (like FVM).
        This gets ALL versions including stable, beta, and dev.
        """
        all_tags = []
        page = 1
        per_page = 100
        
        while True:
            try:
                github_tags_url = f"https://api.github.com/repos/flutter/flutter/tags?per_page={per_page}&page={page}"
                response = requests.get(github_tags_url, timeout=15)
                response.raise_for_status()
                
                tags_data = response.json()
                
                if not tags_data:
                    break
                
                all_tags.extend(tags_data)
                
                # Check if there are more pages
                if len(tags_data) < per_page:
                    break
                
                page += 1
                
            except Exception as e:
                self.logger.error(f"Error fetching GitHub tags page {page}: {e}")
                break
        
        releases = []
        
        # Convert tags to release format
        for tag in all_tags:
            tag_name = tag.get("name", "")
            # Extract version (handles v3.24.0, 3.24.0, 3.24.0-1.2.pre, 3.24.0-dev.1, etc.)
            version_match = re.match(r'v?(\d+\.\d+\.\d+(?:[-.][\w.]+)?)', tag_name)
            if version_match:
                version = version_match.group(1)
                version_lower = version.lower()
                
                # Determine channel (like FVM)
                if "beta" in version_lower or (re.search(r'-\d+\.\d+\.pre', version)):
                    channel = "beta"
                elif "dev" in version_lower or ".pre" in version or re.search(r'-\d+\.\d+\.\d+', version):
                    channel = "dev"
                else:
                    channel = "stable"
                
                releases.append({
                    "version": version,
                    "channel": channel,
                    "release_date": "",  # GitHub tags don't have dates
                    "hash": tag.get("commit", {}).get("sha", "")[:7] if isinstance(tag.get("commit"), dict) else "",
                    "archive": "",
                    "tag": tag_name
                })
        
        return releases
    
    def _get_versions_from_github_fallback(self) -> List[Dict[str, Any]]:
        """Fallback to GitHub API if releases.json fails."""
        try:
            self.logger.info("Falling back to GitHub API")
            url = "https://api.github.com/repos/flutter/flutter/releases"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            releases = response.json()
            versions = []
            
            for release in releases:
                tag_name = release.get("tag_name", "")
                version_match = re.match(r'v?(\d+\.\d+\.\d+)', tag_name)
                if version_match:
                    version = version_match.group(1)
                    versions.append({
                        "version": version,
                        "tag": tag_name,
                        "name": release.get("name", tag_name),
                        "published_at": release.get("published_at", ""),
                        "release_date": release.get("published_at", ""),
                        "prerelease": release.get("prerelease", False),
                        "channel": "beta" if release.get("prerelease") else "stable",
                        "url": release.get("html_url", ""),
                        "download_url": self._get_download_url(version)
                    })
            
            versions.sort(key=lambda x: tuple(map(int, x["version"].split('.'))), reverse=True)
            return versions
            
        except Exception as e:
            self.logger.error(f"GitHub fallback also failed: {e}")
            return []
    
    def _get_download_url_from_release(self, release: Dict[str, Any]) -> Optional[str]:
        """Get download URL from release data for current platform."""
        system = "windows" if os.name == 'nt' else "linux" if os.name == 'posix' else "macos"
        archive = release.get("archive", "")
        
        # If archive URL is provided, use it
        if archive:
            return archive
        
        # Otherwise construct URL
        version = release.get("version", "")
        channel = release.get("channel", "stable")
        
        return self._get_download_url(version, channel)
    
    def _get_download_url(self, version: str, channel: str = "stable") -> str:
        """Get download URL for a Flutter SDK version."""
        system = "windows" if os.name == 'nt' else "linux" if os.name == 'posix' else "macos"
        arch = "x64"
        
        # Flutter SDK download URLs
        # Try to get from releases.json first for accurate URLs
        try:
            releases_url = "https://storage.googleapis.com/flutter_infra_release/releases/releases.json"
            response = requests.get(releases_url, timeout=5)
            if response.status_code == 200:
                releases_data = response.json()
                releases = releases_data.get("releases", [])
                
                # Find matching version
                for release in releases:
                    if release.get("version") == version or release.get("hash") == version:
                        # Get download URL for current platform
                        archive = release.get("archive", "")
                        if archive:
                            return archive
                        # Fallback: construct URL
                        break
        except Exception as e:
            self.logger.debug(f"Could not fetch releases.json: {e}")
        
        # Fallback: construct URL manually
        base_url = "https://storage.googleapis.com/flutter_infra_release/releases"
        
        # Normalize version (remove 'v' prefix if present)
        version_clean = version.lstrip('v')
        
        if system == "windows":
            filename = f"flutter_windows_{arch}_{version_clean}-{channel}.zip"
        elif system == "linux":
            filename = f"flutter_linux_{arch}_{version_clean}-{channel}.zip"
        else:  # macOS
            filename = f"flutter_macos_{arch}_{version_clean}-{channel}.zip"
        
        return f"{base_url}/{channel}/{system}/{filename}"
    
    def download_sdk(self, version: str, channel: str = "stable", 
                    download_url: Optional[str] = None,
                    progress_callback: Optional[callable] = None) -> tuple[bool, str]:
        """
        Download Flutter SDK for a specific version.
        
        Args:
            version: Flutter version (e.g., "3.24.0")
            channel: Release channel (stable, beta, dev)
            download_url: Direct download URL (from FVM JSON archive field)
            progress_callback: Callback function(bytes_downloaded, total_bytes)
        
        Returns:
            (success, message_or_path)
        """
        try:
            # Use provided download_url if available (from FVM JSON), otherwise construct
            if not download_url:
                download_url = self._get_download_url(version, channel)
            
            zip_path = self.sdk_base_dir / f"flutter_{version}_{channel}.zip"
            
            self.logger.info(f"Downloading Flutter {version} ({channel}) from {download_url}")
            
            # Verify URL exists before downloading
            try:
                head_response = requests.head(download_url, timeout=5, allow_redirects=True)
                if head_response.status_code == 404:
                    return False, f"SDK version {version} not found at {download_url}"
            except Exception as e:
                self.logger.warning(f"Could not verify URL: {e}")
            
            success = self.downloader.download_file(
                download_url,
                str(zip_path),
                progress_callback
            )
            
            if success:
                return True, str(zip_path)
            else:
                return False, f"Download failed. URL: {download_url}"
                
        except Exception as e:
            self.logger.error(f"Error downloading SDK: {e}")
            return False, str(e)
    
    def install_sdk(self, zip_path: str, version: str) -> tuple[bool, str]:
        """
        Install Flutter SDK from ZIP file.
        NOTE: This method is kept for backward compatibility but should use SDKInstallThread instead.
        
        Returns:
            (success, message_or_install_path)
        """
        try:
            install_dir = self.sdk_base_dir / f"flutter_{version}"
            
            # Remove existing installation if any
            if install_dir.exists():
                shutil.rmtree(install_dir)
            
            # Extract ZIP
            self.logger.info(f"Extracting Flutter SDK to {install_dir}")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(self.sdk_base_dir)
            
            # Flutter SDK is extracted to a 'flutter' folder, rename it
            extracted_flutter = self.sdk_base_dir / "flutter"
            if extracted_flutter.exists():
                extracted_flutter.rename(install_dir)
            
            # Verify installation
            flutter_bin = install_dir / "bin" / ("flutter.bat" if os.name == 'nt' else "flutter")
            if not flutter_bin.exists():
                return False, "SDK installation verification failed"
            
            # Clean up ZIP file with retry logic
            zip_deleted = False
            max_retries = 5
            zip_path_obj = Path(zip_path)
            
            for attempt in range(max_retries):
                try:
                    if zip_path_obj.exists():
                        os.remove(zip_path)
                        zip_deleted = True
                        self.logger.info(f"Deleted ZIP file: {zip_path}")
                        break
                except PermissionError:
                    if attempt < max_retries - 1:
                        import time
                        time.sleep(0.5)
                        self.logger.warning(f"Retry {attempt + 1}/{max_retries} deleting ZIP file")
                    else:
                        self.logger.warning(f"Could not delete ZIP file after {max_retries} attempts")
                except Exception as e:
                    self.logger.warning(f"Error deleting ZIP file: {e}")
                    break
            
            if not zip_deleted:
                self.logger.warning(f"ZIP file not deleted: {zip_path} (may be in use)")
            
            sdk_path = str(install_dir)
            
            # Add to settings and database
            from services.flutter_service import FlutterService
            from core.database import Database
            flutter_service = FlutterService()
            flutter_service.settings.add_flutter_sdk(sdk_path)
            
            # Also add to SDKs table in database
            db = Database()
            sdk_data = {
                "path": sdk_path,
                "version": version,
                "channel": "stable",
                "is_default": False,
                "is_managed": True
            }
            db.add_sdk(sdk_data)
            
            self.logger.info(f"Flutter SDK {version} installed at {sdk_path}")
            return True, sdk_path
            
        except Exception as e:
            self.logger.error(f"Error installing SDK: {e}")
            return False, str(e)
    
    def get_installed_sdks(self) -> List[Dict[str, Any]]:
        """Get list of all installed SDKs."""
        from core.database import Database
        db = Database()
        
        installed = []
        db_paths = set()
        
        # Load from database first
        db_sdks = db.get_sdks()
        for db_sdk in db_sdks:
            sdk_path = db_sdk["path"]
            if validate_flutter_sdk(sdk_path):
                db_paths.add(sdk_path)
                installed.append({
                    "path": sdk_path,
                    "version": db_sdk.get("version") or self._get_sdk_version(sdk_path),
                    "managed": bool(db_sdk.get("is_managed", False))
                })
        
        # Check managed SDKs directory
        if self.sdk_base_dir.exists():
            for sdk_dir in self.sdk_base_dir.iterdir():
                if sdk_dir.is_dir() and validate_flutter_sdk(str(sdk_dir)):
                    sdk_path = str(sdk_dir)
                    if sdk_path not in db_paths:
                        version = self._get_sdk_version(sdk_path)
                        # Add to database
                        sdk_data = {
                            "path": sdk_path,
                            "version": version,
                            "channel": "stable",
                            "is_default": False,
                            "is_managed": True
                        }
                        db.add_sdk(sdk_data)
                        installed.append({
                            "path": sdk_path,
                            "version": version,
                            "managed": True
                        })
        
        # Also check manually installed SDKs from settings
        from services.flutter_service import FlutterService
        flutter_service = FlutterService()
        for sdk_path in flutter_service.settings.get_flutter_sdks():
            if validate_flutter_sdk(sdk_path) and sdk_path not in db_paths:
                version = self._get_sdk_version(sdk_path)
                # Add to database
                sdk_data = {
                    "path": sdk_path,
                    "version": version,
                    "channel": "stable",
                    "is_default": False,
                    "is_managed": False
                }
                db.add_sdk(sdk_data)
                installed.append({
                    "path": sdk_path,
                    "version": version,
                    "managed": False
                })
        
        return installed
    
    def _get_sdk_version(self, sdk_path: str) -> Optional[str]:
        """Get version of an installed SDK."""
        try:
            from services.flutter_service import FlutterService
            from utils.path_utils import get_flutter_executable
            from core.commands import CommandExecutor
            
            flutter_exe = get_flutter_executable(sdk_path)
            if not flutter_exe:
                return None
            
            output, exit_code = CommandExecutor.run_command([flutter_exe, "--version"])
            if exit_code == 0:
                match = re.search(r'Flutter\s+([\d.]+)', output)
                if match:
                    return match.group(1)
        except:
            pass
        return None
    
    def remove_sdk(self, sdk_path: str) -> bool:
        """Remove an installed SDK."""
        try:
            from core.database import Database
            db = Database()
            
            # Check if it's a managed SDK
            sdk_path_obj = Path(sdk_path)
            if self.sdk_base_dir in sdk_path_obj.parents:
                # Managed SDK - delete directory
                if sdk_path_obj.exists():
                    shutil.rmtree(sdk_path_obj)
                    self.logger.info(f"Removed managed SDK: {sdk_path}")
            else:
                # Manual SDK - just remove from settings
                from services.flutter_service import FlutterService
                flutter_service = FlutterService()
                flutter_service.settings.remove_flutter_sdk(sdk_path)
                self.logger.info(f"Removed SDK from settings: {sdk_path}")
            
            # Remove from database
            db.delete_sdk(sdk_path)
            return True
            
        except Exception as e:
            self.logger.error(f"Error removing SDK: {e}")
            return False
    
    def switch_sdk(self, sdk_path: str, update_path: bool = True) -> bool:
        """Switch to a different Flutter SDK."""
        try:
            if not validate_flutter_sdk(sdk_path):
                self.logger.error(f"Invalid Flutter SDK: {sdk_path}")
                return False
            
            # Set as default
            from services.flutter_service import FlutterService
            from core.database import Database
            flutter_service = FlutterService()
            flutter_service.set_default_sdk(sdk_path)
            
            # Update database
            db = Database()
            db.set_default_sdk(sdk_path)
            
            # Update PATH if requested
            if update_path:
                flutter_bin = Path(sdk_path) / "bin"
                if flutter_bin.exists():
                    bin_path_str = str(flutter_bin.resolve())
                    
                    # Remove old Flutter from PATH first
                    self._remove_flutter_from_path()
                    
                    # Add new Flutter to PATH
                    success = self.path_manager.add_to_path(bin_path_str)
                    if success:
                        self.logger.info(f"Added {bin_path_str} to PATH")
                    else:
                        self.logger.warning(f"Failed to add {bin_path_str} to PATH")
                else:
                    self.logger.warning(f"Flutter bin directory not found: {flutter_bin}")
            
            self.logger.info(f"Switched to Flutter SDK: {sdk_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error switching SDK: {e}")
            return False
    
    def _remove_flutter_from_path(self):
        """Remove all Flutter SDKs from PATH (helper method)."""
        # Get all installed SDKs
        sdks = self.get_installed_sdks()
        removed_count = 0
        for sdk in sdks:
            sdk_path = Path(sdk["path"])
            bin_path = sdk_path / "bin"
            if bin_path.exists():
                bin_path_str = str(bin_path.resolve())
                if self.path_manager.remove_from_path(bin_path_str):
                    removed_count += 1
                    self.logger.info(f"Removed {bin_path_str} from PATH")
        
        # Also check for common Flutter paths that might not be in our list
        common_flutter_paths = [
            str(Path.home() / "flutter" / "bin"),
            "C:\\flutter\\bin",
            "D:\\flutter\\bin",
        ]
        
        for path in common_flutter_paths:
            if self.path_manager.is_in_path(path):
                self.path_manager.remove_from_path(path)
                self.logger.info(f"Removed common Flutter path: {path}")
        
        if removed_count > 0:
            self.logger.info(f"Removed {removed_count} Flutter SDK path(s) from PATH")
    
    def _is_cache_valid(self) -> bool:
        """Check if cached versions file is valid and not too old."""
        if not self.versions_cache_file.exists():
            return False
        
        try:
            import time
            cache_age = time.time() - self.versions_cache_file.stat().st_mtime
            cache_age_hours = cache_age / 3600
            return cache_age_hours < self.cache_max_age_hours
        except Exception:
            return False
    
    def _load_cached_versions(self) -> Optional[List[Dict[str, Any]]]:
        """Load versions from cache file."""
        try:
            if not self.versions_cache_file.exists():
                return None
            
            with open(self.versions_cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get("versions", [])
        except Exception as e:
            self.logger.warning(f"Error loading cached versions: {e}")
            return None
    
    def _save_versions_to_cache(self, versions: List[Dict[str, Any]]):
        """Save versions to cache file."""
        try:
            cache_data = {
                "cached_at": str(Path.home() / ".flutter_launcher" / "cache"),  # Timestamp placeholder
                "versions": versions
            }
            with open(self.versions_cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)
            self.logger.info(f"Cached {len(versions)} versions to {self.versions_cache_file}")
        except Exception as e:
            self.logger.warning(f"Error saving versions to cache: {e}")

