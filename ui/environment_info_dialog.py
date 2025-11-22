"""Environment Info dialog for Flutter Project Launcher Tool."""
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QTextEdit, QTabWidget, QWidget, QLineEdit, QMessageBox)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont
from services.flutter_service import FlutterService
from utils.env_manager import EnvironmentManager
from core.logger import Logger
import os
import sys
import platform
from pathlib import Path


class EnvironmentInfoDialog(QDialog):
    """Dialog showing Flutter environment information."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.flutter_service = FlutterService()
        self.env_manager = EnvironmentManager()
        self.logger = Logger()
        self._init_ui()
        # Defer loading until dialog is shown
        QTimer.singleShot(0, self._load_environment_info)
    
    def _init_ui(self):
        """Initialize UI components."""
        self.setWindowTitle("Flutter Environment Info")
        self.setMinimumSize(700, 600)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        # Tabs for different info sections
        tabs = QTabWidget(self)
        
        # Flutter Info tab
        flutter_tab = QWidget()
        flutter_layout = QVBoxLayout(flutter_tab)
        self.flutter_info_text = QTextEdit(flutter_tab)
        self.flutter_info_text.setReadOnly(True)
        self.flutter_info_text.setFontFamily("Consolas")
        self.flutter_info_text.setFontPointSize(9)
        flutter_layout.addWidget(self.flutter_info_text)
        tabs.addTab(flutter_tab, "Flutter Info")
        
        # System Info tab
        system_tab = QWidget()
        system_layout = QVBoxLayout(system_tab)
        self.system_info_text = QTextEdit(system_tab)
        self.system_info_text.setReadOnly(True)
        self.system_info_text.setFontFamily("Consolas")
        self.system_info_text.setFontPointSize(9)
        system_layout.addWidget(self.system_info_text)
        tabs.addTab(system_tab, "System Info")
        
        # Environment Variables tab
        env_tab = QWidget()
        env_layout = QVBoxLayout(env_tab)
        
        # Environment Variables Management section
        env_mgmt_label = QLabel("Manage Environment Variables", env_tab)
        env_mgmt_label.setFont(QFont("", 10, QFont.Weight.Bold))
        env_layout.addWidget(env_mgmt_label)
        
        # Quick actions for common Flutter vars
        quick_actions_layout = QHBoxLayout()
        quick_actions_label = QLabel("Quick Actions:", env_tab)
        quick_actions_layout.addWidget(quick_actions_label)
        
        set_flutter_root_btn = QPushButton("Set FLUTTER_ROOT from SDK", env_tab)
        set_flutter_root_btn.clicked.connect(self._set_flutter_root_from_sdk)
        quick_actions_layout.addWidget(set_flutter_root_btn)
        
        quick_actions_layout.addStretch()
        env_layout.addLayout(quick_actions_layout)
        
        # Add/Edit section
        add_edit_layout = QHBoxLayout()
        
        name_label = QLabel("Variable Name:", env_tab)
        self.env_name_input = QLineEdit(env_tab)
        self.env_name_input.setPlaceholderText("e.g., FLUTTER_ROOT, PUB_CACHE")
        add_edit_layout.addWidget(name_label)
        add_edit_layout.addWidget(self.env_name_input)
        
        value_label = QLabel("Value:", env_tab)
        self.env_value_input = QLineEdit(env_tab)
        self.env_value_input.setPlaceholderText("e.g., C:\\flutter")
        add_edit_layout.addWidget(value_label)
        add_edit_layout.addWidget(self.env_value_input)
        
        set_btn = QPushButton("➕ Set", env_tab)
        set_btn.clicked.connect(self._set_env_var)
        add_edit_layout.addWidget(set_btn)
        
        remove_btn = QPushButton("➖ Remove", env_tab)
        remove_btn.clicked.connect(self._remove_env_var)
        add_edit_layout.addWidget(remove_btn)
        
        env_layout.addLayout(add_edit_layout)
        
        # Environment Variables display
        env_display_label = QLabel("Current Environment Variables:", env_tab)
        env_layout.addWidget(env_display_label)
        
        self.env_info_text = QTextEdit(env_tab)
        self.env_info_text.setReadOnly(True)
        self.env_info_text.setFontFamily("Consolas")
        self.env_info_text.setFontPointSize(9)
        env_layout.addWidget(self.env_info_text)
        
        tabs.addTab(env_tab, "Environment Variables")
        
        layout.addWidget(tabs)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        refresh_btn = QPushButton("🔄 Refresh", self)
        refresh_btn.clicked.connect(self._load_environment_info)
        button_layout.addWidget(refresh_btn)
        
        # Refresh env vars button
        refresh_env_btn = QPushButton("🔄 Refresh Env Vars", self)
        refresh_env_btn.clicked.connect(self._load_env_vars_display)
        button_layout.addWidget(refresh_env_btn)
        
        close_btn = QPushButton("Close", self)
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
    
    def _load_environment_info(self):
        """Load and display environment information."""
        # Flutter Info
        flutter_info = self.flutter_service.get_flutter_info()
        sdk = self.flutter_service.get_default_sdk()
        
        flutter_text = "Flutter Environment Information\n"
        flutter_text += "=" * 50 + "\n\n"
        
        if sdk:
            flutter_text += f"Flutter SDK Path: {sdk}\n"
            version = self.flutter_service.get_flutter_version(sdk)
            if version:
                flutter_text += f"Flutter Version: {version}\n"
            
            # Get Dart version
            dart_version = self._get_dart_version()
            if dart_version:
                flutter_text += f"Dart Version: {dart_version}\n"
        else:
            flutter_text += "Flutter SDK: Not Found\n"
        
        flutter_text += "\n" + "=" * 50 + "\n"
        flutter_text += "\nFlutter Doctor Output:\n"
        flutter_text += "-" * 50 + "\n"
        
        doctor_info = self.flutter_service.flutter_doctor()
        flutter_text += doctor_info.get("output", "Could not run flutter doctor")
        
        self.flutter_info_text.setPlainText(flutter_text)
        
        # System Info
        system_text = "System Information\n"
        system_text += "=" * 50 + "\n\n"
        system_text += f"Platform: {platform.system()}\n"
        system_text += f"Platform Version: {platform.version()}\n"
        system_text += f"Architecture: {platform.machine()}\n"
        system_text += f"Processor: {platform.processor()}\n"
        system_text += f"Python Version: {platform.python_version()}\n"
        system_text += f"Python Executable: {sys.executable}\n"
        
        self.system_info_text.setPlainText(system_text)
        
        # Environment Variables - show all Flutter-related
        self._load_env_vars_display()
    
    def _load_env_vars_display(self):
        """Load and display environment variables."""
        env_text = "Flutter Related Environment Variables\n"
        env_text += "=" * 50 + "\n\n"
        
        # Get Flutter-related environment variables
        flutter_vars = self.env_manager.list_env_vars("FLUTTER")
        dart_vars = self.env_manager.list_env_vars("DART")
        pub_vars = self.env_manager.list_env_vars("PUB")
        
        # Merge and deduplicate
        all_vars = {}
        all_vars.update(flutter_vars)
        all_vars.update(dart_vars)
        all_vars.update(pub_vars)
        
        # Always show these important ones
        important_vars = {
            "FLUTTER_ROOT": os.environ.get("FLUTTER_ROOT", "Not set"),
            "PUB_CACHE": os.environ.get("PUB_CACHE", "Not set"),
            "PATH": os.environ.get("PATH", "Not set")
        }
        
        # Add important vars if not already in all_vars
        for key, value in important_vars.items():
            if key not in all_vars:
                all_vars[key] = value
        
        # Sort by key
        sorted_vars = sorted(all_vars.items())
        
        for key, value in sorted_vars:
            env_text += f"{key}:\n"
            if key == "PATH":
                # Show PATH entries on separate lines
                path_entries = value.split(os.pathsep) if value != "Not set" else []
                flutter_paths = [p for p in path_entries if "flutter" in p.lower() or "dart" in p.lower()]
                if flutter_paths:
                    env_text += "  (Flutter/Dart related paths)\n"
                    for path in flutter_paths:
                        env_text += f"    {path}\n"
                else:
                    env_text += "  (No Flutter/Dart paths found in PATH)\n"
            else:
                # Truncate very long values
                display_value = value if len(value) < 200 else value[:200] + "..."
                env_text += f"  {display_value}\n"
            env_text += "\n"
        
        self.env_info_text.setPlainText(env_text)
    
    def _set_env_var(self):
        """Set environment variable."""
        name = self.env_name_input.text().strip()
        value = self.env_value_input.text().strip()
        
        if not name:
            QMessageBox.warning(self, "Invalid Input", "Please enter a variable name.")
            return
        
        if not value:
            reply = QMessageBox.question(
                self, "Confirm",
                f"Set {name} to empty value?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                return
        
        success = self.env_manager.set_env_var(name, value)
        
        if success:
            QMessageBox.information(
                self, "Success",
                f"Environment variable '{name}' set successfully!\n\n"
                f"Value: {value}\n\n"
                f"Please restart your terminal/IDE for changes to take effect."
            )
            # Clear inputs
            self.env_name_input.clear()
            self.env_value_input.clear()
            # Refresh display
            self._load_env_vars_display()
        else:
            QMessageBox.warning(
                self, "Error",
                f"Failed to set environment variable '{name}'.\n\n"
                f"Make sure you have the necessary permissions."
            )
    
    def _remove_env_var(self):
        """Remove environment variable."""
        name = self.env_name_input.text().strip()
        
        if not name:
            QMessageBox.warning(self, "Invalid Input", "Please enter a variable name to remove.")
            return
        
        reply = QMessageBox.question(
            self, "Confirm",
            f"Remove environment variable '{name}'?\n\n"
            f"This will permanently delete it from your system.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        success = self.env_manager.remove_env_var(name)
        
        if success:
            QMessageBox.information(
                self, "Success",
                f"Environment variable '{name}' removed successfully!\n\n"
                f"Please restart your terminal/IDE for changes to take effect."
            )
            # Clear inputs
            self.env_name_input.clear()
            self.env_value_input.clear()
            # Refresh display
            self._load_env_vars_display()
        else:
            QMessageBox.warning(
                self, "Error",
                f"Failed to remove environment variable '{name}'.\n\n"
                f"Variable may not exist or you may not have permissions."
            )
    
    def _set_flutter_root_from_sdk(self):
        """Set FLUTTER_ROOT from current default SDK."""
        sdk = self.flutter_service.get_default_sdk()
        
        if not sdk:
            QMessageBox.warning(
                self, "No SDK",
                "No default Flutter SDK found.\n\n"
                "Please set a default SDK in SDK Manager first."
            )
            return
        
        reply = QMessageBox.question(
            self, "Set FLUTTER_ROOT",
            f"Set FLUTTER_ROOT to:\n\n{sdk}\n\n"
            f"This will set the FLUTTER_ROOT environment variable.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        success = self.env_manager.set_env_var("FLUTTER_ROOT", sdk)
        
        if success:
            QMessageBox.information(
                self, "Success",
                f"FLUTTER_ROOT set successfully!\n\n"
                f"Value: {sdk}\n\n"
                f"Please restart your terminal/IDE for changes to take effect."
            )
            # Update inputs
            self.env_name_input.setText("FLUTTER_ROOT")
            self.env_value_input.setText(sdk)
            # Refresh display
            self._load_env_vars_display()
        else:
            QMessageBox.warning(
                self, "Error",
                f"Failed to set FLUTTER_ROOT.\n\n"
                f"Make sure you have the necessary permissions."
            )
    
    def _get_dart_version(self) -> str:
        """Get Dart version."""
        try:
            sdk = self.flutter_service.get_default_sdk()
            if not sdk:
                return None
            
            from utils.path_utils import get_flutter_executable
            from core.commands import CommandExecutor
            
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
        except Exception as e:
            self.logger.debug(f"Could not get Dart version: {e}")
        return None

