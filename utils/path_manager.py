"""Environment PATH management utilities for Flutter Project Launcher Tool."""
import os
import platform
from pathlib import Path
from typing import List, Optional
from core.logger import Logger
import subprocess


class PathManager:
    """Cross-platform PATH management."""
    
    def __init__(self):
        self.logger = Logger()
        self.system = platform.system()
    
    def add_to_path(self, path: str, user_only: bool = True) -> bool:
        """
        Add path to system PATH.
        
        Args:
            path: Path to add
            user_only: If True, modify user PATH only (recommended)
        
        Returns:
            True if successful
        """
        try:
            if self.system == "Windows":
                return self._add_to_path_windows(path, user_only)
            elif self.system in ["Linux", "Darwin"]:
                return self._add_to_path_unix(path, user_only)
            return False
        except Exception as e:
            self.logger.error(f"Error adding to PATH: {e}")
            return False
    
    def remove_from_path(self, path: str) -> bool:
        """Remove path from system PATH."""
        try:
            if self.system == "Windows":
                return self._remove_from_path_windows(path)
            elif self.system in ["Linux", "Darwin"]:
                return self._remove_from_path_unix(path)
            return False
        except Exception as e:
            self.logger.error(f"Error removing from PATH: {e}")
            return False
    
    def is_in_path(self, path: str) -> bool:
        """Check if path is in system PATH."""
        current_path = os.environ.get("PATH", "")
        path_str = str(Path(path).resolve())
        return path_str in current_path or path in current_path
    
    def _add_to_path_windows(self, path: str, user_only: bool) -> bool:
        """Add path to Windows PATH."""
        try:
            import winreg
            
            path_str = str(Path(path).resolve())
            
            # Get current PATH
            if user_only:
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment", 0, winreg.KEY_READ | winreg.KEY_WRITE)
            else:
                key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 
                                    r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment",
                                    0, winreg.KEY_READ | winreg.KEY_WRITE)
            
            try:
                current_path, _ = winreg.QueryValueEx(key, "Path")
            except FileNotFoundError:
                current_path = ""
            
            # Check if already in PATH
            path_entries = current_path.split(os.pathsep) if current_path else []
            if path_str in path_entries:
                return True  # Already in PATH
            
            # Add to PATH
            new_path = current_path + os.pathsep + path_str if current_path else path_str
            winreg.SetValueEx(key, "Path", 0, winreg.REG_EXPAND_SZ, new_path)
            winreg.CloseKey(key)
            
            # Broadcast environment change
            import ctypes
            ctypes.windll.user32.SendMessageW(0xFFFF, 0x001A, 0, "Environment")
            
            self.logger.info(f"Added {path_str} to PATH")
            return True
            
        except Exception as e:
            self.logger.error(f"Windows PATH update failed: {e}")
            return False
    
    def _remove_from_path_windows(self, path: str) -> bool:
        """Remove path from Windows PATH."""
        try:
            import winreg
            
            path_str = str(Path(path).resolve())
            
            # Try user PATH first
            try:
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment", 0, winreg.KEY_READ | winreg.KEY_WRITE)
                current_path, _ = winreg.QueryValueEx(key, "Path")
                path_entries = [p for p in current_path.split(os.pathsep) if p and p != path_str]
                new_path = os.pathsep.join(path_entries)
                winreg.SetValueEx(key, "Path", 0, winreg.REG_EXPAND_SZ, new_path)
                winreg.CloseKey(key)
                
                # Broadcast environment change
                import ctypes
                ctypes.windll.user32.SendMessageW(0x001A, 0x001A, 0, "Environment")
                
                self.logger.info(f"Removed {path_str} from PATH")
                return True
            except:
                pass
            
            return False
            
        except Exception as e:
            self.logger.error(f"Windows PATH removal failed: {e}")
            return False
    
    def _add_to_path_unix(self, path: str, user_only: bool) -> bool:
        """Add path to Unix-like system PATH."""
        try:
            path_str = str(Path(path).resolve())
            shell_config = self._get_shell_config()
            
            if not shell_config:
                return False
            
            # Check if already in PATH
            if self.is_in_path(path_str):
                return True
            
            # Add to shell config
            path_line = f'\nexport PATH="$PATH:{path_str}"\n'
            
            with open(shell_config, 'a') as f:
                f.write(path_line)
            
            self.logger.info(f"Added {path_str} to PATH in {shell_config}")
            return True
            
        except Exception as e:
            self.logger.error(f"Unix PATH update failed: {e}")
            return False
    
    def _remove_from_path_unix(self, path: str) -> bool:
        """Remove path from Unix-like system PATH."""
        try:
            path_str = str(Path(path).resolve())
            shell_config = self._get_shell_config()
            
            if not shell_config or not os.path.exists(shell_config):
                return False
            
            # Read config file
            with open(shell_config, 'r') as f:
                lines = f.readlines()
            
            # Remove lines containing this path
            new_lines = [line for line in lines if path_str not in line]
            
            # Write back
            with open(shell_config, 'w') as f:
                f.writelines(new_lines)
            
            self.logger.info(f"Removed {path_str} from PATH in {shell_config}")
            return True
            
        except Exception as e:
            self.logger.error(f"Unix PATH removal failed: {e}")
            return False
    
    def _get_shell_config(self) -> Optional[str]:
        """Get shell configuration file path."""
        shell = os.environ.get("SHELL", "")
        home = Path.home()
        
        if "zsh" in shell:
            return str(home / ".zshrc")
        elif "bash" in shell:
            return str(home / ".bashrc")
        else:
            # Default to .bashrc
            bashrc = home / ".bashrc"
            if bashrc.exists():
                return str(bashrc)
            return str(home / ".profile")

