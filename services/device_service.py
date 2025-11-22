"""Device management service for Flutter Project Launcher Tool."""
import re
from typing import List, Dict, Optional
from core.logger import Logger
from services.flutter_service import FlutterService
from core.commands import CommandExecutor


class DeviceService:
    """Service for device and emulator management."""
    
    def __init__(self):
        self.logger = Logger()
        self.flutter_service = FlutterService()
    
    def get_connected_devices(self) -> List[Dict[str, str]]:
        """
        Get list of connected devices and emulators.
        
        Returns:
            List of device dictionaries with keys: id, name, type, status
        """
        output, exit_code = self.flutter_service.run_flutter_command(["devices"])
        
        if exit_code != 0:
            return []
        
        devices = []
        lines = output.split('\n')
        
        # Skip header lines
        device_lines = []
        in_device_section = False
        
        for line in lines:
            if '•' in line or 'Connected devices' in line or 'No devices' in line:
                in_device_section = True
                if '•' in line:
                    device_lines.append(line)
            elif in_device_section and line.strip():
                device_lines.append(line)
        
        for line in device_lines:
            if '•' in line:
                # Parse device line
                # Format: "• device_name • device_id • device_type • status"
                parts = [p.strip() for p in line.split('•') if p.strip()]
                
                if len(parts) >= 3:
                    device = {
                        "name": parts[0] if len(parts) > 0 else "Unknown",
                        "id": parts[1] if len(parts) > 1 else "",
                        "type": parts[2] if len(parts) > 2 else "unknown",
                        "status": "available"
                    }
                    
                    # Try to determine device type
                    name_lower = device["name"].lower()
                    if "emulator" in name_lower or "simulator" in name_lower:
                        device["type"] = "emulator"
                    elif "android" in name_lower:
                        device["type"] = "android"
                    elif "ios" in name_lower or "iphone" in name_lower:
                        device["type"] = "ios"
                    elif "chrome" in name_lower or "web" in name_lower:
                        device["type"] = "web"
                    elif "windows" in name_lower or "linux" in name_lower or "macos" in name_lower:
                        device["type"] = "desktop"
                    
                    devices.append(device)
        
        return devices
    
    def get_available_devices(self) -> List[Dict[str, str]]:
        """Get only available (not busy) devices."""
        all_devices = self.get_connected_devices()
        return [d for d in all_devices if d.get("status") == "available"]
    
    def get_device_by_id(self, device_id: str) -> Optional[Dict[str, str]]:
        """Get device information by ID."""
        devices = self.get_connected_devices()
        for device in devices:
            if device.get("id") == device_id:
                return device
        return None
    
    def get_emulators(self) -> List[Dict[str, str]]:
        """Get list of emulators only."""
        devices = self.get_connected_devices()
        return [d for d in devices if d.get("type") == "emulator"]
    
    def get_physical_devices(self) -> List[Dict[str, str]]:
        """Get list of physical devices only."""
        devices = self.get_connected_devices()
        return [d for d in devices if d.get("type") != "emulator"]
    
    def launch_emulator(self, emulator_id: str) -> tuple[str, int]:
        """Launch an Android emulator (if available)."""
        # This would require Android SDK tools
        # For now, return a placeholder
        self.logger.info(f"Attempting to launch emulator: {emulator_id}")
        return "Emulator launch not yet implemented", 1
    
    def get_emulators_detailed(self) -> List[Dict[str, str]]:
        """Get detailed emulator information."""
        return self.get_emulators()
    
    def launch_emulator_by_name(self, emulator_name: str) -> bool:
        """Launch emulator by name."""
        emulators = self.get_emulators()
        for emulator in emulators:
            if emulator.get("name") == emulator_name:
                result = self.launch_emulator(emulator.get("id", ""))
                return result[1] == 0
        return False
    
    def refresh_devices(self) -> List[Dict[str, str]]:
        """Refresh device list."""
        return self.get_connected_devices()


