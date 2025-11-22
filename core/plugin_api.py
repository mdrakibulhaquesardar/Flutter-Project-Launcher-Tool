"""Plugin API for Flutter Project Launcher Tool plugins."""
from typing import Callable, Optional, Dict, Any
from core.logger import Logger
from services.project_service import ProjectService
from services.flutter_service import FlutterService
from core.settings import Settings
from PyQt6.QtWidgets import QMessageBox, QWidget


class PluginAPI:
    """API exposed to plugins for app integration."""
    
    def __init__(self, app_instance=None):
        self.logger = Logger()
        self.settings = Settings()
        self.project_service = ProjectService()
        self.flutter_service = FlutterService()
        self.app_instance = app_instance
        
        # Plugin registrations
        self._templates: Dict[str, Callable] = {}
        self._architectures: Dict[str, Callable] = {}
        self._tool_actions: Dict[str, Dict[str, Any]] = {}
        self._menu_items: Dict[str, Dict[str, Any]] = {}
    
    def register_template(self, name: str, handler_func: Callable):
        """Register a template generator."""
        self._templates[name] = handler_func
        self.logger.info(f"Plugin registered template: {name}")
    
    def register_architecture(self, name: str, generator_func: Callable):
        """Register an architecture generator."""
        self._architectures[name] = generator_func
        self.logger.info(f"Plugin registered architecture: {name}")
    
    def register_tool_action(self, name: str, icon: Optional[str], callback: Callable):
        """Register a tool action."""
        self._tool_actions[name] = {
            "name": name,
            "icon": icon,
            "callback": callback
        }
        self.logger.info(f"Plugin registered tool action: {name}")
    
    def add_menu_item(self, menu_path: str, label: str, callback: Callable):
        """Register a menu item."""
        self._menu_items[f"{menu_path}/{label}"] = {
            "menu_path": menu_path,
            "label": label,
            "callback": callback
        }
        self.logger.info(f"Plugin registered menu item: {menu_path}/{label}")
    
    def get_project_service(self) -> ProjectService:
        """Get ProjectService instance."""
        return self.project_service
    
    def get_flutter_service(self) -> FlutterService:
        """Get FlutterService instance."""
        return self.flutter_service
    
    def get_logger(self) -> Logger:
        """Get Logger instance."""
        return self.logger
    
    def show_message(self, title: str, message: str, msg_type: str = "info", parent: Optional[QWidget] = None):
        """Show a message box."""
        if parent is None and self.app_instance:
            parent = self.app_instance
        
        icon_map = {
            "info": QMessageBox.Icon.Information,
            "warning": QMessageBox.Icon.Warning,
            "error": QMessageBox.Icon.Critical,
            "question": QMessageBox.Icon.Question
        }
        
        msg_box = QMessageBox(parent)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setIcon(icon_map.get(msg_type, QMessageBox.Icon.Information))
        msg_box.exec()
    
    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a setting value."""
        return self.settings.get(key, default)
    
    def set_setting(self, key: str, value: Any):
        """Set a setting value."""
        self.settings.set(key, value)
    
    def get_registered_templates(self) -> Dict[str, Callable]:
        """Get all registered templates."""
        return self._templates.copy()
    
    def get_registered_architectures(self) -> Dict[str, Callable]:
        """Get all registered architectures."""
        return self._architectures.copy()
    
    def get_registered_tool_actions(self) -> Dict[str, Dict[str, Any]]:
        """Get all registered tool actions."""
        return self._tool_actions.copy()
    
    def get_registered_menu_items(self) -> Dict[str, Dict[str, Any]]:
        """Get all registered menu items."""
        return self._menu_items.copy()

