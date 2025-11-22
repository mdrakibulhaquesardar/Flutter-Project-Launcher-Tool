"""Environment variable management utilities for Flutter Project Launcher Tool."""
import os
import platform
from pathlib import Path
from typing import Dict, Optional
from core.logger import Logger


class EnvironmentManager:
    """Cross-platform environment variable management."""
    
    def __init__(self):
        self.logger = Logger()
        self.system = platform.system()
    
    def get_env_var(self, name: str) -> Optional[str]:
        """Get environment variable value."""
        return os.environ.get(name)
    
    def set_env_var(self, name: str, value: str, user_only: bool = True) -> bool:
        """
        Set environment variable in system.
        
        Args:
            name: Variable name
            value: Variable value
            user_only: If True, set for current user only (recommended)
        
        Returns:
            True if successful
        """
        try:
            if self.system == "Windows":
                return self._set_env_var_windows(name, value, user_only)
            elif self.system in ["Linux", "Darwin"]:
                return self._set_env_var_unix(name, value, user_only)
            return False
        except Exception as e:
            self.logger.error(f"Error setting environment variable: {e}")
            return False
    
    def remove_env_var(self, name: str) -> bool:
        """Remove environment variable from system."""
        try:
            if self.system == "Windows":
                return self._remove_env_var_windows(name)
            elif self.system in ["Linux", "Darwin"]:
                return self._remove_env_var_unix(name)
            return False
        except Exception as e:
            self.logger.error(f"Error removing environment variable: {e}")
            return False
    
    def list_env_vars(self, filter_pattern: Optional[str] = None) -> Dict[str, str]:
        """
        List environment variables.
        
        Args:
            filter_pattern: Optional pattern to filter (e.g., "FLUTTER", "DART")
        
        Returns:
            Dictionary of environment variables
        """
        env_vars = dict(os.environ)
        
        if filter_pattern:
            filtered = {}
            pattern_lower = filter_pattern.lower()
            for key, value in env_vars.items():
                if pattern_lower in key.lower():
                    filtered[key] = value
            return filtered
        
        return env_vars
    
    def _set_env_var_windows(self, name: str, value: str, user_only: bool) -> bool:
        """Set environment variable on Windows."""
        try:
            import winreg
            
            if user_only:
                key = winreg.OpenKey(
                    winreg.HKEY_CURRENT_USER, 
                    "Environment", 
                    0, 
                    winreg.KEY_READ | winreg.KEY_WRITE
                )
            else:
                key = winreg.OpenKey(
                    winreg.HKEY_LOCAL_MACHINE,
                    r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment",
                    0,
                    winreg.KEY_READ | winreg.KEY_WRITE
                )
            
            try:
                winreg.SetValueEx(key, name, 0, winreg.REG_EXPAND_SZ, value)
            finally:
                winreg.CloseKey(key)
            
            # Broadcast environment change
            import ctypes
            ctypes.windll.user32.SendMessageW(0xFFFF, 0x001A, 0, "Environment")
            
            self.logger.info(f"Set environment variable: {name}={value}")
            return True
            
        except Exception as e:
            self.logger.error(f"Windows environment variable update failed: {e}")
            return False
    
    def _remove_env_var_windows(self, name: str) -> bool:
        """Remove environment variable on Windows."""
        try:
            import winreg
            
            # Try user environment first
            try:
                key = winreg.OpenKey(
                    winreg.HKEY_CURRENT_USER,
                    "Environment",
                    0,
                    winreg.KEY_READ | winreg.KEY_WRITE
                )
                try:
                    winreg.DeleteValue(key, name)
                except FileNotFoundError:
                    pass
                finally:
                    winreg.CloseKey(key)
                
                # Broadcast environment change
                import ctypes
                ctypes.windll.user32.SendMessageW(0xFFFF, 0x001A, 0, "Environment")
                
                self.logger.info(f"Removed environment variable: {name}")
                return True
            except Exception:
                pass
            
            return False
            
        except Exception as e:
            self.logger.error(f"Windows environment variable removal failed: {e}")
            return False
    
    def _set_env_var_unix(self, name: str, value: str, user_only: bool) -> bool:
        """Set environment variable on Unix-like systems."""
        try:
            shell_config = self._get_shell_config()
            if not shell_config:
                return False
            
            # Read existing config
            lines = []
            var_found = False
            
            if Path(shell_config).exists():
                with open(shell_config, 'r') as f:
                    lines = f.readlines()
            
            # Check if variable already exists
            new_lines = []
            for line in lines:
                if line.strip().startswith(f'export {name}='):
                    new_lines.append(f'export {name}="{value}"\n')
                    var_found = True
                else:
                    new_lines.append(line)
            
            # Add if not found
            if not var_found:
                new_lines.append(f'export {name}="{value}"\n')
            
            # Write back
            with open(shell_config, 'w') as f:
                f.writelines(new_lines)
            
            self.logger.info(f"Set environment variable: {name}={value} in {shell_config}")
            return True
            
        except Exception as e:
            self.logger.error(f"Unix environment variable update failed: {e}")
            return False
    
    def _remove_env_var_unix(self, name: str) -> bool:
        """Remove environment variable on Unix-like systems."""
        try:
            shell_config = self._get_shell_config()
            if not shell_config or not Path(shell_config).exists():
                return False
            
            # Read config
            with open(shell_config, 'r') as f:
                lines = f.readlines()
            
            # Remove lines containing this variable
            new_lines = [line for line in lines if not line.strip().startswith(f'export {name}=')]
            
            # Write back
            with open(shell_config, 'w') as f:
                f.writelines(new_lines)
            
            self.logger.info(f"Removed environment variable: {name} from {shell_config}")
            return True
            
        except Exception as e:
            self.logger.error(f"Unix environment variable removal failed: {e}")
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

