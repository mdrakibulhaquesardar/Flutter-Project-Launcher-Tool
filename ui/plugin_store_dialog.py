"""Plugin Store dialog for browsing and installing plugins."""
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QListWidget, QListWidgetItem, QMessageBox,
                             QTextEdit, QSplitter, QWidget, QLineEdit, QComboBox)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont
from core.plugin_registry import PluginRegistry
from core.plugin_loader import PluginLoader
from core.logger import Logger
from pathlib import Path
import json
from typing import Optional, Dict, List, Any
from utils.file_utils import read_json, write_json


class PluginStoreDialog(QDialog):
    """Dialog for browsing and installing plugins from the store."""
    
    def __init__(self, parent=None, plugin_loader: Optional[PluginLoader] = None):
        super().__init__(parent)
        self.setWindowTitle("Plugin Store")
        self.setMinimumSize(900, 600)
        
        self.logger = Logger()
        self.registry = PluginRegistry()
        self.plugin_loader = plugin_loader
        
        # Plugin store data
        self.store_data: Dict[str, Any] = {}
        self.available_plugins: List[Dict[str, Any]] = []
        
        self._init_ui()
        
        # Defer loading to avoid delay
        QTimer.singleShot(0, self._load_store_data)
    
    def _init_ui(self):
        """Initialize UI components."""
        layout = QVBoxLayout(self)
        
        # Header
        header_layout = QHBoxLayout()
        header_label = QLabel("Plugin Store")
        header_font = QFont()
        header_font.setBold(True)
        header_font.setPointSize(14)
        header_label.setFont(header_font)
        header_layout.addWidget(header_label)
        header_layout.addStretch()
        
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self._load_store_data)
        header_layout.addWidget(refresh_btn)
        layout.addLayout(header_layout)
        
        # Search and filter
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Search:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search plugins...")
        self.search_input.textChanged.connect(self._filter_plugins)
        filter_layout.addWidget(self.search_input)
        
        filter_layout.addWidget(QLabel("Category:"))
        self.category_combo = QComboBox()
        self.category_combo.addItems(["All", "Architecture", "Template", "Tool", "General"])
        self.category_combo.currentTextChanged.connect(self._filter_plugins)
        filter_layout.addWidget(self.category_combo)
        layout.addLayout(filter_layout)
        
        # Splitter for plugin list and details
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Plugin list (left)
        list_widget = QWidget()
        list_layout = QVBoxLayout(list_widget)
        list_layout.setContentsMargins(0, 0, 0, 0)
        
        list_label = QLabel("Available Plugins:")
        list_layout.addWidget(list_label)
        
        self.plugin_list = QListWidget()
        self.plugin_list.setFont(QFont("Consolas", 9))
        self.plugin_list.itemSelectionChanged.connect(self._show_plugin_details)
        list_layout.addWidget(self.plugin_list)
        
        splitter.addWidget(list_widget)
        
        # Plugin details (right)
        details_widget = QWidget()
        details_layout = QVBoxLayout(details_widget)
        details_layout.setContentsMargins(0, 0, 0, 0)
        
        details_label = QLabel("Plugin Details:")
        details_layout.addWidget(details_label)
        
        self.details_text = QTextEdit()
        self.details_text.setReadOnly(True)
        self.details_text.setFont(QFont("Consolas", 9))
        details_layout.addWidget(self.details_text)
        
        # Install button
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        self.install_btn = QPushButton("Install Plugin")
        self.install_btn.clicked.connect(self._install_selected_plugin)
        self.install_btn.setEnabled(False)
        button_layout.addWidget(self.install_btn)
        details_layout.addLayout(button_layout)
        
        splitter.addWidget(details_widget)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        
        layout.addWidget(splitter)
        
        # Close button
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)
        layout.addLayout(button_layout)
    
    def _load_store_data(self):
        """Load plugin store data."""
        self.plugin_list.clear()
        self.details_text.clear()
        self.available_plugins = []
        
        # Try to load from local store file
        store_file = Path("data/plugin_store.json")
        
        if store_file.exists():
            try:
                self.store_data = read_json(str(store_file))
                self.available_plugins = self.store_data.get("plugins", [])
            except Exception as e:
                self.logger.error(f"Error loading plugin store: {e}")
                self._show_default_store()
        else:
            # Create default store file with example plugins
            self._create_default_store()
            self.available_plugins = self.store_data.get("plugins", [])
        
        self._display_plugins()
    
    def _create_default_store(self):
        """Create default plugin store file."""
        store_file = Path("data/plugin_store.json")
        store_file.parent.mkdir(parents=True, exist_ok=True)
        
        default_store = {
            "plugins": [
                {
                    "id": "clean_arch",
                    "name": "Clean Architecture Generator",
                    "version": "1.0.0",
                    "author": "Flutter Launcher",
                    "description": "Generate Clean Architecture boilerplate for Flutter projects",
                    "plugin_type": "architecture",
                    "download_url": "local",
                    "repository": "builtin"
                },
                {
                    "id": "getx_generator",
                    "name": "GetX Architecture Generator",
                    "version": "1.0.0",
                    "author": "Flutter Launcher",
                    "description": "Generate GetX-based architecture for Flutter projects",
                    "plugin_type": "architecture",
                    "download_url": "local",
                    "repository": "builtin"
                },
                {
                    "id": "build_apk",
                    "name": "Build APK Shortcut",
                    "version": "1.0.0",
                    "author": "Flutter Launcher",
                    "description": "Quick APK build command tool",
                    "plugin_type": "tool",
                    "download_url": "local",
                    "repository": "builtin"
                },
                {
                    "id": "flutter_fire",
                    "name": "Flutter Fire Setup",
                    "version": "1.0.0",
                    "author": "Flutter Launcher",
                    "description": "Setup Firebase configuration for Flutter projects",
                    "plugin_type": "template",
                    "download_url": "local",
                    "repository": "builtin"
                }
            ]
        }
        
        write_json(str(store_file), default_store)
        self.store_data = default_store
    
    def _show_default_store(self):
        """Show default store message."""
        self.details_text.setText(
            "Plugin Store\n\n"
            "No plugin store data available.\n"
            "Plugins can be installed manually from:\n"
            "1. Plugin Manager → Add Plugin\n"
            "2. Import from ZIP file or folder"
        )
    
    def _display_plugins(self):
        """Display available plugins in list."""
        self.plugin_list.clear()
        
        for plugin in self.available_plugins:
            name = plugin.get("name", "Unknown")
            version = plugin.get("version", "N/A")
            author = plugin.get("author", "Unknown")
            plugin_id = plugin.get("id", "")
            
            # Check if plugin is installed
            is_installed = self.registry.get_plugin(plugin_id) is not None
            
            item = QListWidgetItem(f"• {name} v{version} by {author}")
            item.setData(Qt.ItemDataRole.UserRole, plugin)
            
            # Set green color for installed plugins
            if is_installed:
                item.setForeground(Qt.GlobalColor.green)
            
            self.plugin_list.addItem(item)
    
    def _filter_plugins(self):
        """Filter plugins by search and category."""
        search_text = self.search_input.text().lower()
        category = self.category_combo.currentText()
        
        self.plugin_list.clear()
        
        for plugin in self.available_plugins:
            # Filter by category
            plugin_type = plugin.get("plugin_type", "general").title()
            if category != "All" and plugin_type != category:
                continue
            
            # Filter by search
            if search_text:
                searchable_text = (
                    plugin.get("name", "") + " " +
                    plugin.get("description", "") + " " +
                    plugin.get("author", "")
                ).lower()
                if search_text not in searchable_text:
                    continue
            
            name = plugin.get("name", "Unknown")
            version = plugin.get("version", "N/A")
            author = plugin.get("author", "Unknown")
            plugin_id = plugin.get("id", "")
            
            # Check if plugin is installed
            is_installed = self.registry.get_plugin(plugin_id) is not None
            
            item = QListWidgetItem(f"• {name} v{version} by {author}")
            item.setData(Qt.ItemDataRole.UserRole, plugin)
            
            # Set green color for installed plugins
            if is_installed:
                item.setForeground(Qt.GlobalColor.green)
            
            self.plugin_list.addItem(item)
    
    def _show_plugin_details(self):
        """Show details of selected plugin."""
        current_item = self.plugin_list.currentItem()
        
        if not current_item:
            self.details_text.clear()
            self.install_btn.setEnabled(False)
            return
        
        plugin = current_item.data(Qt.ItemDataRole.UserRole)
        
        if not plugin:
            return
        
        # Check if already installed
        plugin_id = plugin.get("id")
        is_installed = self.registry.get_plugin(plugin_id) is not None
        
        details = f"""
Plugin Details:

Name: {plugin.get('name', 'N/A')}
ID: {plugin.get('id', 'N/A')}
Version: {plugin.get('version', 'N/A')}
Author: {plugin.get('author', 'N/A')}
Type: {plugin.get('plugin_type', 'N/A').title()}
Description: {plugin.get('description', 'N/A')}
Repository: {plugin.get('repository', 'N/A')}

Status: {'✓ Installed' if is_installed else '✗ Not Installed'}
        """
        
        self.details_text.setText(details.strip())
        self.install_btn.setEnabled(not is_installed)
        self.install_btn.setText("Already Installed" if is_installed else "Install Plugin")
    
    def _install_selected_plugin(self):
        """Install selected plugin."""
        current_item = self.plugin_list.currentItem()
        
        if not current_item:
            return
        
        plugin = current_item.data(Qt.ItemDataRole.UserRole)
        plugin_id = plugin.get("id")
        
        # Check if already installed
        if self.registry.get_plugin(plugin_id):
            QMessageBox.information(
                self, "Already Installed",
                f"Plugin '{plugin.get('name')}' is already installed."
            )
            return
        
        # Check if it's a builtin plugin (already in plugins folder)
        if plugin.get("download_url") == "local":
            # Check if plugin exists locally
            plugin_path = Path("plugins") / plugin_id
            if plugin_path.exists():
                # Register the existing plugin
                plugin_json = plugin_path / "plugin.json"
                if plugin_json.exists():
                    try:
                        metadata = read_json(str(plugin_json))
                        self.registry.register_plugin(
                            plugin_id=plugin_id,
                            name=metadata.get("name", plugin.get("name")),
                            version=metadata.get("version", plugin.get("version")),
                            author=metadata.get("author", plugin.get("author")),
                            description=metadata.get("description", plugin.get("description")),
                            plugin_type=metadata.get("plugin_type", plugin.get("plugin_type")),
                            path=str(plugin_path),
                            enabled=True
                        )
                        
                        # Load plugin
                        if self.plugin_loader:
                            self.plugin_loader.load_plugin(plugin_id)
                        
                        QMessageBox.information(
                            self, "Success",
                            f"Plugin '{plugin.get('name')}' installed successfully!"
                        )
                        self._show_plugin_details()  # Refresh details
                        return
                    except Exception as e:
                        self.logger.error(f"Error installing plugin: {e}")
                        QMessageBox.warning(
                            self, "Error",
                            f"Failed to install plugin: {e}"
                        )
                        return
        
        # For remote plugins (future implementation)
        QMessageBox.information(
            self, "Coming Soon",
            "Remote plugin installation is not yet implemented.\n\n"
            "For now, you can install plugins manually:\n"
            "1. Go to Plugin Manager\n"
            "2. Use 'Add Plugin' tab\n"
            "3. Import from ZIP or folder"
        )

