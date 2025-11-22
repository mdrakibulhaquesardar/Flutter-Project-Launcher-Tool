"""Plugin Manager dialog for Flutter Project Launcher Tool."""
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QListWidget, QListWidgetItem, QMessageBox,
                             QTabWidget, QWidget, QTextEdit, QFileDialog, QCheckBox,
                             QGroupBox, QFormLayout, QLineEdit, QComboBox)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont
from core.plugin_registry import PluginRegistry
from core.plugin_loader import PluginLoader
from core.logger import Logger
from pathlib import Path
import zipfile
import shutil
import json
from typing import Optional


class PluginManagerDialog(QDialog):
    """Dialog for managing plugins."""
    
    def __init__(self, parent=None, plugin_loader: Optional[PluginLoader] = None):
        super().__init__(parent)
        self.setWindowTitle("Plugin Manager")
        self.setMinimumSize(800, 600)
        
        self.logger = Logger()
        self.registry = PluginRegistry()
        self.plugin_loader = plugin_loader
        
        self._init_ui()
        
        # Defer loading to avoid delay
        QTimer.singleShot(0, self._load_plugins)
    
    def _init_ui(self):
        """Initialize UI components."""
        layout = QVBoxLayout(self)
        
        # Create tab widget
        self.tabs = QTabWidget()
        
        # Tab 1: Installed Plugins
        self.installed_tab = QWidget()
        self._init_installed_tab()
        self.tabs.addTab(self.installed_tab, "Installed Plugins")
        
        # Tab 2: Add Plugin
        self.add_tab = QWidget()
        self._init_add_tab()
        self.tabs.addTab(self.add_tab, "Add Plugin")
        
        layout.addWidget(self.tabs)
        
        # Close button
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)
        layout.addLayout(button_layout)
    
    def _init_installed_tab(self):
        """Initialize Installed Plugins tab."""
        layout = QVBoxLayout(self.installed_tab)
        
        # Filter section
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Filter:"))
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["All", "Enabled", "Disabled"])
        self.filter_combo.currentTextChanged.connect(self._filter_plugins)
        filter_layout.addWidget(self.filter_combo)
        filter_layout.addStretch()
        
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self._load_plugins)
        filter_layout.addWidget(refresh_btn)
        layout.addLayout(filter_layout)
        
        # Plugin list
        self.plugin_list = QListWidget()
        self.plugin_list.setFont(QFont("Consolas", 9))
        layout.addWidget(self.plugin_list)
        
        # Actions
        action_layout = QHBoxLayout()
        self.enable_btn = QPushButton("Enable")
        self.enable_btn.clicked.connect(self._toggle_plugin)
        self.disable_btn = QPushButton("Disable")
        self.disable_btn.clicked.connect(self._toggle_plugin)
        self.uninstall_btn = QPushButton("Uninstall")
        self.uninstall_btn.clicked.connect(self._uninstall_plugin)
        self.reload_btn = QPushButton("Reload")
        self.reload_btn.clicked.connect(self._reload_plugin)
        self.details_btn = QPushButton("View Details")
        self.details_btn.clicked.connect(self._show_plugin_details)
        
        action_layout.addWidget(self.enable_btn)
        action_layout.addWidget(self.disable_btn)
        action_layout.addWidget(self.uninstall_btn)
        action_layout.addWidget(self.reload_btn)
        action_layout.addWidget(self.details_btn)
        action_layout.addStretch()
        layout.addLayout(action_layout)
    
    def _init_add_tab(self):
        """Initialize Add Plugin tab."""
        layout = QVBoxLayout(self.add_tab)
        
        # Instructions
        instructions = QLabel(
            "Import a plugin from a ZIP file or folder.\n"
            "Plugins must contain a plugin.json file with metadata."
        )
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        
        # Import from ZIP
        zip_group = QGroupBox("Import from ZIP File")
        zip_layout = QVBoxLayout()
        zip_btn = QPushButton("Browse ZIP File...")
        zip_btn.clicked.connect(self._import_from_zip)
        zip_layout.addWidget(zip_btn)
        zip_group.setLayout(zip_layout)
        layout.addWidget(zip_group)
        
        # Import from Folder
        folder_group = QGroupBox("Import from Folder")
        folder_layout = QVBoxLayout()
        folder_btn = QPushButton("Browse Folder...")
        folder_btn.clicked.connect(self._import_from_folder)
        folder_layout.addWidget(folder_btn)
        folder_group.setLayout(folder_layout)
        layout.addWidget(folder_group)
        
        layout.addStretch()
    
    def _load_plugins(self):
        """Load and display plugins."""
        self.plugin_list.clear()
        plugins = self.registry.get_all_plugins()
        
        filter_text = self.filter_combo.currentText()
        if filter_text == "Enabled":
            plugins = [p for p in plugins if p.get("enabled", False)]
        elif filter_text == "Disabled":
            plugins = [p for p in plugins if not p.get("enabled", False)]
        
        for plugin in plugins:
            item = QListWidgetItem()
            plugin_id = plugin.get("id", "unknown")
            name = plugin.get("name", plugin_id)
            version = plugin.get("version", "N/A")
            author = plugin.get("author", "Unknown")
            enabled = plugin.get("enabled", False)
            status = "✓ Enabled" if enabled else "✗ Disabled"
            
            item.setText(f"• {name} v{version} by {author} - {status}")
            item.setData(Qt.ItemDataRole.UserRole, plugin_id)
            self.plugin_list.addItem(item)
    
    def _filter_plugins(self):
        """Filter plugins by status."""
        self._load_plugins()
    
    def _toggle_plugin(self):
        """Enable or disable selected plugin."""
        current_item = self.plugin_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "No Selection", "Please select a plugin.")
            return
        
        plugin_id = current_item.data(Qt.ItemDataRole.UserRole)
        plugin = self.registry.get_plugin(plugin_id)
        
        if not plugin:
            return
        
        current_enabled = plugin.get("enabled", False)
        new_enabled = not current_enabled
        
        if self.registry.set_plugin_enabled(plugin_id, new_enabled):
            if self.plugin_loader:
                if new_enabled:
                    self.plugin_loader.load_plugin(plugin_id)
                else:
                    self.plugin_loader.unload_plugin(plugin_id)
            
            # Notify parent window to reload plugin menu items
            if hasattr(self.parent(), '_load_plugin_menu_items'):
                self.parent()._load_plugin_menu_items()
            if hasattr(self.parent(), '_load_plugin_tool_actions'):
                self.parent()._load_plugin_tool_actions()
            
            self._load_plugins()
            QMessageBox.information(
                self, "Success",
                f"Plugin {'enabled' if new_enabled else 'disabled'} successfully."
            )
    
    def _uninstall_plugin(self):
        """Uninstall selected plugin."""
        current_item = self.plugin_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "No Selection", "Please select a plugin.")
            return
        
        plugin_id = current_item.data(Qt.ItemDataRole.UserRole)
        plugin = self.registry.get_plugin(plugin_id)
        
        if not plugin:
            return
        
        reply = QMessageBox.question(
            self, "Confirm Uninstall",
            f"Are you sure you want to uninstall '{plugin.get('name')}'?\n\n"
            "This will remove the plugin files and cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Unload plugin if loaded
            if self.plugin_loader:
                self.plugin_loader.unload_plugin(plugin_id)
            
            # Remove plugin directory
            plugin_path = Path(plugin.get("path"))
            if plugin_path.exists():
                try:
                    shutil.rmtree(plugin_path)
                except Exception as e:
                    self.logger.error(f"Error removing plugin directory: {e}")
                    QMessageBox.warning(
                        self, "Error",
                        f"Error removing plugin files: {e}\n"
                        "You may need to remove it manually."
                    )
            
            # Unregister plugin
            if self.registry.unregister_plugin(plugin_id):
                self._load_plugins()
                QMessageBox.information(self, "Success", "Plugin uninstalled successfully.")
    
    def _reload_plugin(self):
        """Reload selected plugin."""
        current_item = self.plugin_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "No Selection", "Please select a plugin.")
            return
        
        plugin_id = current_item.data(Qt.ItemDataRole.UserRole)
        
        if self.plugin_loader:
            if self.plugin_loader.reload_plugin(plugin_id):
                # Notify parent window to reload plugin menu items
                if hasattr(self.parent(), '_load_plugin_menu_items'):
                    self.parent()._load_plugin_menu_items()
                if hasattr(self.parent(), '_load_plugin_tool_actions'):
                    self.parent()._load_plugin_tool_actions()
                
                self._load_plugins()
                QMessageBox.information(self, "Success", "Plugin reloaded successfully.")
            else:
                QMessageBox.warning(self, "Error", "Failed to reload plugin.")
    
    def _show_plugin_details(self):
        """Show details of selected plugin."""
        current_item = self.plugin_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "No Selection", "Please select a plugin.")
            return
        
        plugin_id = current_item.data(Qt.ItemDataRole.UserRole)
        plugin = self.registry.get_plugin(plugin_id)
        
        if not plugin:
            return
        
        details_text = f"""
Plugin Details:

Name: {plugin.get('name', 'N/A')}
ID: {plugin.get('id', 'N/A')}
Version: {plugin.get('version', 'N/A')}
Author: {plugin.get('author', 'N/A')}
Type: {plugin.get('plugin_type', 'N/A')}
Description: {plugin.get('description', 'N/A')}
Path: {plugin.get('path', 'N/A')}
Enabled: {plugin.get('enabled', False)}
Installed: {plugin.get('installed_at', 'N/A')}
        """
        
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Plugin Details")
        msg_box.setText(details_text.strip())
        msg_box.exec()
    
    def _import_from_zip(self):
        """Import plugin from ZIP file."""
        zip_path, _ = QFileDialog.getOpenFileName(
            self, "Select Plugin ZIP File", "",
            "ZIP Files (*.zip);;All Files (*)"
        )
        
        if not zip_path:
            return
        
        self._install_plugin_from_zip(zip_path)
    
    def _import_from_folder(self):
        """Import plugin from folder."""
        folder_path = QFileDialog.getExistingDirectory(
            self, "Select Plugin Folder"
        )
        
        if not folder_path:
            return
        
        self._install_plugin_from_folder(folder_path)
    
    def _install_plugin_from_zip(self, zip_path: str):
        """Install plugin from ZIP file."""
        try:
            zip_file = Path(zip_path)
            if not zip_file.exists():
                QMessageBox.warning(self, "Error", "ZIP file not found.")
                return
            
            # Extract to temp location first
            temp_dir = Path("plugins") / ".temp_install"
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
            temp_dir.mkdir(parents=True, exist_ok=True)
            
            with zipfile.ZipFile(zip_path, 'r') as zipf:
                zipf.extractall(temp_dir)
            
            # Find plugin.json
            plugin_json = None
            for json_file in temp_dir.rglob("plugin.json"):
                plugin_json = json_file
                break
            
            if not plugin_json:
                shutil.rmtree(temp_dir)
                QMessageBox.warning(
                    self, "Error",
                    "plugin.json not found in ZIP file."
                )
                return
            
            # Load plugin metadata
            with open(plugin_json, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            plugin_id = metadata.get("id")
            if not plugin_id:
                shutil.rmtree(temp_dir)
                QMessageBox.warning(
                    self, "Error",
                    "plugin.json missing required 'id' field."
                )
                return
            
            # Move to final location
            plugin_dir = Path("plugins") / plugin_id
            if plugin_dir.exists():
                reply = QMessageBox.question(
                    self, "Plugin Exists",
                    f"Plugin '{plugin_id}' already exists. Overwrite?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply == QMessageBox.StandardButton.No:
                    shutil.rmtree(temp_dir)
                    return
                shutil.rmtree(plugin_dir)
            
            # Move parent directory of plugin.json to plugins folder
            plugin_json_parent = plugin_json.parent
            if plugin_json_parent == temp_dir:
                # plugin.json is at root, move everything
                shutil.move(str(temp_dir), str(plugin_dir))
            else:
                # plugin.json is in subdirectory, move that subdirectory
                plugin_dir.mkdir(parents=True, exist_ok=True)
                for item in plugin_json_parent.iterdir():
                    shutil.move(str(item), str(plugin_dir / item.name))
                shutil.rmtree(temp_dir)
            
            # Register plugin
            self.registry.register_plugin(
                plugin_id=plugin_id,
                name=metadata.get("name", plugin_id),
                version=metadata.get("version", "1.0.0"),
                author=metadata.get("author", "Unknown"),
                description=metadata.get("description", ""),
                plugin_type=metadata.get("plugin_type", "general"),
                path=str(plugin_dir),
                enabled=metadata.get("enabled", True)
            )
            
            # Load plugin if enabled
            if self.plugin_loader and metadata.get("enabled", True):
                self.plugin_loader.load_plugin(plugin_id)
            
            self._load_plugins()
            QMessageBox.information(self, "Success", f"Plugin '{plugin_id}' installed successfully.")
        
        except Exception as e:
            self.logger.error(f"Error installing plugin from ZIP: {e}", exc_info=True)
            QMessageBox.critical(
                self, "Error",
                f"Failed to install plugin:\n{str(e)}"
            )
    
    def _install_plugin_from_folder(self, folder_path: str):
        """Install plugin from folder."""
        try:
            source_dir = Path(folder_path)
            if not source_dir.exists():
                QMessageBox.warning(self, "Error", "Folder not found.")
                return
            
            # Find plugin.json
            plugin_json = source_dir / "plugin.json"
            if not plugin_json.exists():
                QMessageBox.warning(
                    self, "Error",
                    "plugin.json not found in folder."
                )
                return
            
            # Load plugin metadata
            with open(plugin_json, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            plugin_id = metadata.get("id")
            if not plugin_id:
                QMessageBox.warning(
                    self, "Error",
                    "plugin.json missing required 'id' field."
                )
                return
            
            # Copy to plugins directory
            plugin_dir = Path("plugins") / plugin_id
            if plugin_dir.exists():
                reply = QMessageBox.question(
                    self, "Plugin Exists",
                    f"Plugin '{plugin_id}' already exists. Overwrite?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply == QMessageBox.StandardButton.No:
                    return
                shutil.rmtree(plugin_dir)
            
            shutil.copytree(source_dir, plugin_dir)
            
            # Register plugin
            self.registry.register_plugin(
                plugin_id=plugin_id,
                name=metadata.get("name", plugin_id),
                version=metadata.get("version", "1.0.0"),
                author=metadata.get("author", "Unknown"),
                description=metadata.get("description", ""),
                plugin_type=metadata.get("plugin_type", "general"),
                path=str(plugin_dir),
                enabled=metadata.get("enabled", True)
            )
            
            # Load plugin if enabled
            if self.plugin_loader and metadata.get("enabled", True):
                self.plugin_loader.load_plugin(plugin_id)
            
            self._load_plugins()
            QMessageBox.information(self, "Success", f"Plugin '{plugin_id}' installed successfully.")
        
        except Exception as e:
            self.logger.error(f"Error installing plugin from folder: {e}", exc_info=True)
            QMessageBox.critical(
                self, "Error",
                f"Failed to install plugin:\n{str(e)}"
            )

