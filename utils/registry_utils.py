"""Windows Registry utilities for FluStudio."""
import sys
from typing import Optional
from pathlib import Path
from core.logger import Logger


class RegistryUtils:
    """Windows Registry helper utilities."""
    
    _logger = None
    
    @classmethod
    def _get_logger(cls):
        """Get logger instance."""
        if cls._logger is None:
            cls._logger = Logger()
        return cls._logger
    
    @classmethod
    def is_windows(cls) -> bool:
        """Check if running on Windows."""
        return sys.platform == "win32"
    
    @classmethod
    def read_registry_value(cls, key_path: str, value_name: str) -> Optional[str]:
        """
        Read a value from Windows Registry.
        
        Args:
            key_path: Registry key path (e.g., "Software\\NextCode Studio\\FluStudio\\License")
            value_name: Value name to read
            
        Returns:
            Value as string, or None if not found or error
        """
        if not cls.is_windows():
            cls._get_logger().warning("Registry access only available on Windows")
            return None
        
        try:
            import winreg
            
            # Open registry key (HKEY_CURRENT_USER)
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                key_path,
                0,
                winreg.KEY_READ
            )
            
            try:
                value, _ = winreg.QueryValueEx(key, value_name)
                winreg.CloseKey(key)
                return str(value) if value is not None else None
            except FileNotFoundError:
                winreg.CloseKey(key)
                return None
            except Exception as e:
                winreg.CloseKey(key)
                cls._get_logger().warning(f"Error reading registry value {value_name}: {e}")
                return None
                
        except FileNotFoundError:
            # Key doesn't exist
            return None
        except Exception as e:
            cls._get_logger().error(f"Error accessing registry: {e}")
            return None
    
    @classmethod
    def write_registry_value(cls, key_path: str, value_name: str, value: str) -> bool:
        """
        Write a value to Windows Registry.
        
        Args:
            key_path: Registry key path
            value_name: Value name to write
            value: Value to write
            
        Returns:
            True if successful, False otherwise
        """
        if not cls.is_windows():
            cls._get_logger().warning("Registry access only available on Windows")
            return False
        
        try:
            import winreg
            
            # Create key if it doesn't exist
            key = winreg.CreateKey(
                winreg.HKEY_CURRENT_USER,
                key_path
            )
            
            try:
                winreg.SetValueEx(key, value_name, 0, winreg.REG_SZ, str(value))
                winreg.CloseKey(key)
                return True
            except Exception as e:
                winreg.CloseKey(key)
                cls._get_logger().error(f"Error writing registry value {value_name}: {e}")
                return False
                
        except Exception as e:
            cls._get_logger().error(f"Error creating registry key: {e}")
            return False
    
    @classmethod
    def delete_registry_value(cls, key_path: str, value_name: str) -> bool:
        """
        Delete a value from Windows Registry.
        
        Args:
            key_path: Registry key path
            value_name: Value name to delete
            
        Returns:
            True if successful, False otherwise
        """
        if not cls.is_windows():
            cls._get_logger().warning("Registry access only available on Windows")
            return False
        
        try:
            import winreg
            
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                key_path,
                0,
                winreg.KEY_WRITE
            )
            
            try:
                winreg.DeleteValue(key, value_name)
                winreg.CloseKey(key)
                return True
            except FileNotFoundError:
                winreg.CloseKey(key)
                return True  # Value doesn't exist, consider it deleted
            except Exception as e:
                winreg.CloseKey(key)
                cls._get_logger().error(f"Error deleting registry value {value_name}: {e}")
                return False
                
        except FileNotFoundError:
            # Key doesn't exist
            return True
        except Exception as e:
            cls._get_logger().error(f"Error accessing registry: {e}")
            return False
    
    @classmethod
    def registry_key_exists(cls, key_path: str) -> bool:
        """
        Check if a registry key exists.
        
        Args:
            key_path: Registry key path
            
        Returns:
            True if key exists, False otherwise
        """
        if not cls.is_windows():
            return False
        
        try:
            import winreg
            
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                key_path,
                0,
                winreg.KEY_READ
            )
            winreg.CloseKey(key)
            return True
        except FileNotFoundError:
            return False
        except Exception:
            return False

