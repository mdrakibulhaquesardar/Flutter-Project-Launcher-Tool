"""Project management service for Flutter Project Launcher Tool."""
import json
import yaml
import re
from pathlib import Path
from typing import List, Dict, Optional, Any
from datetime import datetime
from core.logger import Logger
from core.settings import Settings
from utils.file_utils import is_flutter_project, read_json, write_json
from utils.icon_utils import find_flutter_project_icon
from services.flutter_service import FlutterService


class ProjectService:
    """Service for Flutter project operations."""
    
    def __init__(self):
        self.logger = Logger()
        self.settings = Settings()
        self.flutter_service = FlutterService()
        self.projects_file = Path("data/projects.json")  # Keep for backward compatibility
        self.projects_file.parent.mkdir(parents=True, exist_ok=True)
        from core.database import Database
        self.db = Database()
    
    def create_project(self, name: str, location: str, template: Optional[str] = None) -> tuple[bool, str]:
        """
        Create a new Flutter project.
        
        Returns:
            tuple: (success, message_or_path)
        """
        project_path = Path(location) / name
        
        if project_path.exists():
            return False, f"Directory already exists: {project_path}"
        
        # Build flutter create command
        args = ["create", name]
        if template:
            args.extend(["--template", template])
        
        # Run command in parent directory
        output, exit_code = self.flutter_service.run_flutter_command(args, cwd=str(location))
        
        if exit_code == 0:
            project_path = Path(location) / name
            if is_flutter_project(str(project_path)):
                self.add_project(str(project_path))
                self.logger.info(f"Created project: {project_path}")
                return True, str(project_path)
            else:
                return False, "Project created but validation failed"
        else:
            return False, f"Failed to create project: {output}"
    
    def add_project(self, project_path: str):
        """Add project to recent projects list."""
        if not is_flutter_project(project_path):
            return
        
        project_data = self.get_project_metadata(project_path)
        
        # Add/update in database
        self.db.add_project(project_data)
        
        # Update access time
        self.db.update_project_access(project_path)
        
        # Also update JSON for backward compatibility
        projects = self.load_recent_projects()
        write_json(str(self.projects_file), {"projects": projects[:50]})
    
    def load_recent_projects(self) -> List[Dict[str, Any]]:
        """Load recent projects from database."""
        # Load from database
        projects = self.db.get_projects(limit=50)
        
        # Convert database format to expected format and validate
        formatted_projects = []
        for project in projects:
            path = project.get("path")
            # Validate project still exists
            if path and Path(path).exists() and is_flutter_project(path):
                # Get package name from metadata or use name
                metadata = {}
                if project.get("metadata"):
                    try:
                        metadata = json.loads(project["metadata"])
                    except:
                        pass
                
                formatted = {
                    "name": project.get("name", ""),
                    "package_name": metadata.get("package_name") or project.get("name", ""),
                    "path": path,
                    "flutter_version": project.get("flutter_version"),
                    "flutter_sdk_constraint": project.get("flutter_sdk_constraint"),
                    "fvm_enabled": bool(project.get("fvm_enabled", 0)),
                    "icon_path": project.get("icon_path"),
                    "last_modified": project.get("last_modified"),
                    "dependencies": project.get("dependencies", {})
                }
                formatted_projects.append(formatted)
            else:
                # Remove invalid project from database
                if path:
                    self.db.delete_project(path)
        
        return formatted_projects
    
    def get_project_metadata(self, project_path: str) -> Dict[str, Any]:
        """Get metadata for a Flutter project."""
        path = Path(project_path)
        pubspec = path / "pubspec.yaml"
        
        metadata = {
            "name": path.name,
            "path": str(path.resolve()),
            "last_modified": datetime.fromtimestamp(path.stat().st_mtime).isoformat(),
            "flutter_version": None,
            "dependencies": {},
            "icon_path": None,
        }
        
        # Read pubspec.yaml
        if pubspec.exists():
            try:
                with open(pubspec, 'r', encoding='utf-8') as f:
                    pubspec_data = yaml.safe_load(f)
                    if pubspec_data:
                        # Package name from pubspec.yaml
                        package_name = pubspec_data.get("name", path.name)
                        metadata["name"] = package_name
                        metadata["package_name"] = package_name  # Explicit package name field
                        metadata["dependencies"] = pubspec_data.get("dependencies", {})
            except Exception as e:
                self.logger.warning(f"Error reading pubspec.yaml: {e}")
        
        # Try to detect Flutter version from project
        try:
            # First, check if project has .fvm folder (FVM version manager)
            fvm_config = path / ".fvm" / "fvm_config.json"
            if fvm_config.exists():
                try:
                    import json
                    with open(fvm_config, 'r') as f:
                        fvm_data = json.load(f)
                        if "flutterSdkVersion" in fvm_data:
                            metadata["flutter_version"] = f"FVM: {fvm_data['flutterSdkVersion']}"
                            return metadata
                except:
                    pass
            
            # Check pubspec.yaml for Flutter SDK constraint
            if pubspec.exists():
                try:
                    with open(pubspec, 'r', encoding='utf-8') as f:
                        content = f.read()
                        # Look for sdk constraint like: sdk: ">=2.0.0 <3.0.0"
                        sdk_match = re.search(r'sdk:\s*["\']?([^"\']+)["\']?', content)
                        if sdk_match:
                            sdk_constraint = sdk_match.group(1).strip()
                            metadata["flutter_sdk_constraint"] = sdk_constraint
                except:
                    pass
            
            # Try to get Flutter version by running flutter --version in project directory
            # This will use the project's Flutter SDK if available
            output, exit_code = self.flutter_service.run_flutter_command(
                ["--version"], 
                cwd=str(path)
            )
            if exit_code == 0:
                # Parse version from output (first line usually contains version)
                lines = output.strip().split('\n')
                if lines:
                    version_line = lines[0].strip()
                    # Extract version number (e.g., "Flutter 3.24.0")
                    version_match = re.search(r'Flutter\s+([\d.]+)', version_line)
                    if version_match:
                        # Store clean version: "3.24.0" or "Flutter 3.24.0"
                        version_number = version_match.group(1)
                        metadata["flutter_version"] = f"Flutter {version_number}"
                        metadata["flutter_version_number"] = version_number  # Store clean version number
                    else:
                        metadata["flutter_version"] = version_line
        except Exception as e:
            self.logger.debug(f"Could not detect Flutter version for {project_path}: {e}")
        
        # Find project icon
        try:
            icon_path = find_flutter_project_icon(project_path)
            if icon_path:
                metadata["icon_path"] = icon_path
        except Exception as e:
            self.logger.debug(f"Could not find icon for {project_path}: {e}")
        
        return metadata
    
    def scan_projects(self, search_paths: List[str], max_depth: int = 3) -> List[Dict[str, Any]]:
        """
        Scan directories for Flutter projects.
        
        Args:
            search_paths: List of paths to scan
            max_depth: Maximum directory depth to scan
        
        Returns:
            List of project metadata dictionaries
        """
        found_projects = []
        
        def scan_directory(path: Path, depth: int = 0):
            if depth > max_depth:
                return
            
            if not path.exists() or not path.is_dir():
                return
            
            # Check if current directory is a Flutter project
            if is_flutter_project(str(path)):
                found_projects.append(self.get_project_metadata(str(path)))
                return  # Don't scan inside Flutter projects
            
            # Scan subdirectories
            try:
                for item in path.iterdir():
                    if item.is_dir() and not item.name.startswith('.'):
                        scan_directory(item, depth + 1)
            except PermissionError:
                pass
        
        for search_path in search_paths:
            scan_directory(Path(search_path))
        
        return found_projects
    
    def remove_project(self, project_path: str):
        """Remove project from recent projects list."""
        # Remove from database
        self.db.delete_project(project_path)
        
        # Also update JSON for backward compatibility
        projects = self.load_recent_projects()
        projects = [p for p in projects if p.get("path") != project_path]
        write_json(str(self.projects_file), {"projects": projects})
    
    def run_project(self, project_path: str, device_id: Optional[str] = None) -> tuple[str, int]:
        """Run Flutter project on device."""
        args = ["run"]
        if device_id:
            args.extend(["-d", device_id])
        
        return self.flutter_service.run_flutter_command(args, cwd=project_path)
    
    def build_apk(self, project_path: str, release: bool = True) -> tuple[str, int]:
        """Build APK for Android."""
        args = ["build", "apk"]
        if release:
            args.append("--release")
        
        return self.flutter_service.run_flutter_command(args, cwd=project_path)
    
    def build_appbundle(self, project_path: str, release: bool = True) -> tuple[str, int]:
        """Build App Bundle for Android."""
        args = ["build", "appbundle"]
        if release:
            args.append("--release")
        
        return self.flutter_service.run_flutter_command(args, cwd=project_path)
    
    def pub_get(self, project_path: str) -> tuple[str, int]:
        """Run flutter pub get."""
        return self.flutter_service.run_flutter_command(["pub", "get"], cwd=project_path)
    
    def clean_project(self, project_path: str) -> tuple[str, int]:
        """Clean Flutter project."""
        return self.flutter_service.run_flutter_command(["clean"], cwd=project_path)


