"""Dependency analysis service for Flutter Project Launcher Tool."""
import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional
from core.logger import Logger
from utils.file_utils import is_flutter_project


class DependencyService:
    """Service for analyzing Flutter project dependencies."""
    
    def __init__(self):
        self.logger = Logger()
    
    def analyze_dependencies(self, project_path: str) -> Dict[str, Any]:
        """
        Analyze dependencies from a Flutter project.
        
        Returns:
            Dictionary with dependency information
        """
        project = Path(project_path)
        pubspec = project / "pubspec.yaml"
        
        if not pubspec.exists():
            return {"error": "pubspec.yaml not found"}
        
        try:
            with open(pubspec, 'r', encoding='utf-8') as f:
                pubspec_data = yaml.safe_load(f)
            
            dependencies = pubspec_data.get("dependencies", {})
            dev_dependencies = pubspec_data.get("dev_dependencies", {})
            
            # Analyze dependencies
            dep_info = {
                "project_name": pubspec_data.get("name", "Unknown"),
                "project_version": pubspec_data.get("version", "Unknown"),
                "dependencies": self._parse_dependencies(dependencies),
                "dev_dependencies": self._parse_dependencies(dev_dependencies),
                "total_dependencies": len(dependencies) + len(dev_dependencies),
                "sdk_constraint": pubspec_data.get("environment", {}).get("sdk", "Not specified")
            }
            
            return dep_info
            
        except Exception as e:
            self.logger.error(f"Error analyzing dependencies: {e}")
            return {"error": str(e)}
    
    def _parse_dependencies(self, deps: Dict[str, Any]) -> List[Dict[str, str]]:
        """Parse dependency dictionary into structured list."""
        parsed = []
        
        for name, version_spec in deps.items():
            if name == "flutter" or name == "flutter_test":
                continue
            
            dep_info = {
                "name": name,
                "version": str(version_spec) if isinstance(version_spec, (str, int, float)) else "See constraint",
                "type": "path" if isinstance(version_spec, dict) and "path" in version_spec else "pub",
                "constraint": str(version_spec) if isinstance(version_spec, dict) else None
            }
            
            if isinstance(version_spec, dict):
                if "path" in version_spec:
                    dep_info["path"] = version_spec["path"]
                if "git" in version_spec:
                    dep_info["git"] = version_spec.get("url", "")
                    dep_info["type"] = "git"
            
            parsed.append(dep_info)
        
        return parsed
    
    def get_dependency_tree(self, project_path: str) -> str:
        """Get dependency tree as text."""
        try:
            from services.flutter_service import FlutterService
            from utils.path_utils import get_flutter_executable
            from core.commands import CommandExecutor
            
            flutter_service = FlutterService()
            sdk = flutter_service.get_default_sdk()
            flutter_exe = get_flutter_executable(sdk)
            
            if not flutter_exe:
                return "Flutter SDK not found"
            
            output, exit_code = CommandExecutor.run_command(
                [flutter_exe, "pub", "deps"],
                cwd=project_path
            )
            
            return output if exit_code == 0 else f"Error: {output}"
            
        except Exception as e:
            return f"Error getting dependency tree: {e}"
    
    def check_outdated_packages(self, project_path: str) -> Dict[str, Any]:
        """Check for outdated packages."""
        try:
            from services.flutter_service import FlutterService
            from utils.path_utils import get_flutter_executable
            from core.commands import CommandExecutor
            
            flutter_service = FlutterService()
            sdk = flutter_service.get_default_sdk()
            flutter_exe = get_flutter_executable(sdk)
            
            if not flutter_exe:
                return {"error": "Flutter SDK not found"}
            
            output, exit_code = CommandExecutor.run_command(
                [flutter_exe, "pub", "outdated"],
                cwd=project_path
            )
            
            return {
                "output": output,
                "has_updates": "can be updated" in output.lower() or "upgradable" in output.lower(),
                "exit_code": exit_code
            }
            
        except Exception as e:
            return {"error": str(e)}

