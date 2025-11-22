"""Flutter SDK service for Flutter Project Launcher Tool."""
import os
import subprocess
from pathlib import Path
from typing import Optional, List, Dict, Any
from core.logger import Logger
from core.settings import Settings
from utils.path_utils import validate_flutter_sdk, get_flutter_executable
from core.commands import CommandExecutor


class FlutterService:
    """Service for Flutter SDK operations."""
    
    def __init__(self):
        self.logger = Logger()
        self.settings = Settings()
        self.sdk_path: Optional[str] = None
    
    def detect_flutter_sdks(self) -> List[str]:
        """Scan common locations for Flutter SDK installations."""
        common_paths = []
        
        # Windows paths
        if os.name == 'nt':
            common_paths.extend([
                Path.home() / "flutter",
                Path("C:/flutter"),
                Path("C:/src/flutter"),
                Path("D:/flutter"),
            ])
        else:
            # Unix-like paths
            common_paths.extend([
                Path.home() / "flutter",
                Path.home() / "development" / "flutter",
                Path("/opt/flutter"),
                Path("/usr/local/flutter"),
            ])
        
        # Check environment variable
        env_flutter = os.environ.get("FLUTTER_ROOT")
        if env_flutter:
            common_paths.append(Path(env_flutter))
        
        # Validate and return valid SDKs
        valid_sdks = []
        for path in common_paths:
            if validate_flutter_sdk(str(path)):
                valid_sdks.append(str(path.resolve()))
        
        # Also check settings
        for sdk in self.settings.get_flutter_sdks():
            if validate_flutter_sdk(sdk) and sdk not in valid_sdks:
                valid_sdks.append(sdk)
        
        return valid_sdks
    
    def get_flutter_version(self, sdk_path: Optional[str] = None) -> Optional[str]:
        """Get Flutter version for a given SDK."""
        flutter_exe = get_flutter_executable(sdk_path or self.get_default_sdk())
        if not flutter_exe:
            return None
        
        output, exit_code = CommandExecutor.run_command([flutter_exe, "--version"])
        if exit_code == 0:
            # Parse version from output (first line usually contains version)
            lines = output.strip().split('\n')
            if lines:
                return lines[0].strip()
        return None
    
    def get_default_sdk(self) -> Optional[str]:
        """Get default Flutter SDK path."""
        default = self.settings.get_default_sdk()
        if default and validate_flutter_sdk(default):
            return default
        
        # Try to find any valid SDK
        sdks = self.detect_flutter_sdks()
        if sdks:
            return sdks[0]
        
        return None
    
    def set_default_sdk(self, sdk_path: str):
        """Set default Flutter SDK."""
        if validate_flutter_sdk(sdk_path):
            self.settings.add_flutter_sdk(sdk_path)
            self.settings.set_default_sdk(sdk_path)
            self.sdk_path = sdk_path
            
            # Also update database
            from core.database import Database
            db = Database()
            db.set_default_sdk(sdk_path)
            
            self.logger.info(f"Set default Flutter SDK: {sdk_path}")
    
    def run_flutter_command(self, args: List[str], cwd: Optional[str] = None) -> tuple[str, int]:
        """Run Flutter command and return output."""
        sdk = self.get_default_sdk()
        flutter_exe = get_flutter_executable(sdk)
        
        if not flutter_exe:
            return "Flutter SDK not found. Please configure Flutter SDK in settings.", 1
        
        command = [flutter_exe] + args
        self.logger.info(f"Running: {' '.join(command)}")
        
        return CommandExecutor.run_command(command, cwd=cwd)
    
    def flutter_doctor(self) -> Dict[str, Any]:
        """Run flutter doctor and parse output."""
        output, exit_code = self.run_flutter_command(["doctor", "-v"])
        
        return {
            "output": output,
            "exit_code": exit_code,
            "status": "ok" if exit_code == 0 else "error"
        }
    
    def get_flutter_info(self) -> Dict[str, Any]:
        """Get comprehensive Flutter SDK information."""
        sdk = self.get_default_sdk()
        if not sdk:
            return {
                "sdk_path": None,
                "version": None,
                "status": "not_found"
            }
        
        version = self.get_flutter_version(sdk)
        return {
            "sdk_path": sdk,
            "version": version,
            "status": "ok" if version else "error"
        }
    
    def get_dart_version(self) -> Optional[str]:
        """Get Dart version."""
        sdk = self.get_default_sdk()
        if not sdk:
            return None
        
        flutter_exe = get_flutter_executable(sdk)
        if not flutter_exe:
            return None
        
        output, exit_code = CommandExecutor.run_command([flutter_exe, "--version"])
        if exit_code == 0:
            # Parse Dart version from output
            lines = output.split('\n')
            for line in lines:
                if 'Dart' in line:
                    return line.strip()
        return None
    
    def clear_pub_cache(self) -> tuple[str, int]:
        """Clear Flutter pub cache."""
        return self.run_flutter_command(["pub", "cache", "clean"])
    
    def repair_pub_cache(self) -> tuple[str, int]:
        """Repair Flutter pub cache."""
        return self.run_flutter_command(["pub", "cache", "repair"])
    
    def check_flutter_upgrade(self) -> Dict[str, Any]:
        """Check if Flutter upgrade is available."""
        output, exit_code = self.run_flutter_command(["upgrade", "--dry-run"])
        
        return {
            "output": output,
            "exit_code": exit_code,
            "upgrade_available": "upgrade available" in output.lower() or "new version" in output.lower()
        }


