"""Settings dialog for Flutter Project Launcher Tool."""
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QListWidget, QListWidgetItem,
                             QMessageBox, QFileDialog, QTabWidget, QWidget, QCheckBox, QTextEdit)
from PyQt6.QtCore import Qt
from services.flutter_service import FlutterService
from core.settings import Settings
from core.logger import Logger
from utils.path_utils import validate_flutter_sdk
from pathlib import Path


class SettingsDialog(QDialog):
    """Dialog for application settings."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.settings = Settings()
        self.flutter_service = FlutterService()
        self.logger = Logger()
        self._init_ui()
        # Defer loading until dialog is shown
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(0, self._load_settings)
    
    def _init_ui(self):
        """Initialize UI components."""
        self.setWindowTitle("Settings")
        self.setMinimumSize(600, 500)
        
        layout = QVBoxLayout(self)
        
        # Tabs
        tabs = QTabWidget(self)
        
        # Flutter SDK tab
        sdk_tab = QWidget()
        sdk_layout = QVBoxLayout(sdk_tab)
        sdk_layout.setSpacing(10)
        
        sdk_info = QLabel("Manage Flutter SDK installations:")
        sdk_layout.addWidget(sdk_info)
        
        # SDK list
        self.sdk_list = QListWidget(self)
        sdk_layout.addWidget(self.sdk_list)
        
        # SDK buttons
        sdk_btn_layout = QHBoxLayout()
        self.add_sdk_btn = QPushButton("Add SDK", self)
        self.add_sdk_btn.clicked.connect(self._add_sdk)
        sdk_btn_layout.addWidget(self.add_sdk_btn)
        
        self.remove_sdk_btn = QPushButton("Remove SDK", self)
        self.remove_sdk_btn.clicked.connect(self._remove_sdk)
        sdk_btn_layout.addWidget(self.remove_sdk_btn)
        
        self.set_default_btn = QPushButton("Set as Default", self)
        self.set_default_btn.clicked.connect(self._set_default_sdk)
        sdk_btn_layout.addWidget(self.set_default_btn)
        
        self.scan_btn = QPushButton("Auto-detect SDKs", self)
        self.scan_btn.clicked.connect(self._scan_sdks)
        sdk_btn_layout.addWidget(self.scan_btn)
        
        sdk_btn_layout.addStretch()
        sdk_layout.addLayout(sdk_btn_layout)
        
        tabs.addTab(sdk_tab, "Flutter SDK")
        
        # General tab
        general_tab = QWidget()
        general_layout = QVBoxLayout(general_tab)
        general_layout.setSpacing(10)
        
        # Default project location
        location_layout = QVBoxLayout()
        location_label = QLabel("Default Project Location:")
        self.location_input = QLineEdit(self)
        location_browse_btn = QPushButton("Browse...", self)
        location_browse_btn.clicked.connect(self._browse_project_location)
        location_input_layout = QHBoxLayout()
        location_input_layout.addWidget(self.location_input)
        location_input_layout.addWidget(location_browse_btn)
        location_layout.addWidget(location_label)
        location_layout.addLayout(location_input_layout)
        general_layout.addLayout(location_layout)
        
        # Auto-scan
        self.auto_scan_checkbox = QCheckBox("Auto-scan for Flutter projects on startup", self)
        general_layout.addWidget(self.auto_scan_checkbox)
        
        # Scan paths
        scan_paths_layout = QVBoxLayout()
        scan_paths_label = QLabel("Scan Paths (one per line):", self)
        self.scan_paths_text = QTextEdit(self)
        self.scan_paths_text.setMaximumHeight(100)
        self.scan_paths_text.setPlaceholderText("C:\\Users\\YourName\\Projects\nD:\\Development")
        scan_paths_btn_layout = QHBoxLayout()
        scan_paths_add_btn = QPushButton("Add Path...", self)
        scan_paths_add_btn.clicked.connect(self._add_scan_path)
        scan_paths_btn_layout.addWidget(scan_paths_add_btn)
        scan_paths_btn_layout.addStretch()
        scan_paths_layout.addWidget(scan_paths_label)
        scan_paths_layout.addWidget(self.scan_paths_text)
        scan_paths_layout.addLayout(scan_paths_btn_layout)
        general_layout.addLayout(scan_paths_layout)
        
        general_layout.addStretch()
        tabs.addTab(general_tab, "General")
        
        layout.addWidget(tabs)
        
        # Dialog buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.ok_btn = QPushButton("OK", self)
        self.ok_btn.clicked.connect(self._save_and_close)
        button_layout.addWidget(self.ok_btn)
        
        self.cancel_btn = QPushButton("Cancel", self)
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(button_layout)
    
    def _load_settings(self):
        """Load current settings into UI."""
        # Load SDKs
        self._refresh_sdk_list()
        
        # Load general settings
        self.location_input.setText(self.settings.get("default_project_location", ""))
        self.auto_scan_checkbox.setChecked(self.settings.get("auto_scan", True))
        
        # Load scan paths
        scan_paths = self.settings.get("scan_paths", [])
        self.scan_paths_text.setPlainText("\n".join(scan_paths))
    
    def _refresh_sdk_list(self):
        """Refresh SDK list widget."""
        self.sdk_list.clear()
        sdks = self.settings.get_flutter_sdks()
        default_sdk = self.settings.get_default_sdk()
        
        for sdk in sdks:
            item = QListWidgetItem(sdk)
            if sdk == default_sdk:
                item.setText(f"{sdk} (Default)")
                item.setForeground(Qt.GlobalColor.blue)
            self.sdk_list.addItem(item)
    
    def _add_sdk(self):
        """Add new Flutter SDK."""
        sdk_path = QFileDialog.getExistingDirectory(
            self, "Select Flutter SDK Directory"
        )
        if sdk_path:
            if validate_flutter_sdk(sdk_path):
                if self.settings.add_flutter_sdk(sdk_path):
                    self._refresh_sdk_list()
                    QMessageBox.information(self, "Success", "Flutter SDK added successfully!")
                else:
                    QMessageBox.warning(self, "Warning", "SDK already exists in list.")
            else:
                QMessageBox.warning(self, "Invalid SDK", 
                                 "Selected directory does not contain a valid Flutter SDK.")
    
    def _remove_sdk(self):
        """Remove selected SDK."""
        current_item = self.sdk_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "No Selection", "Please select an SDK to remove.")
            return
        
        sdk_path = current_item.text().replace(" (Default)", "")
        
        reply = QMessageBox.question(
            self, "Confirm Removal",
            f"Remove SDK: {sdk_path}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.settings.remove_flutter_sdk(sdk_path)
            self._refresh_sdk_list()
    
    def _set_default_sdk(self):
        """Set selected SDK as default."""
        current_item = self.sdk_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "No Selection", "Please select an SDK to set as default.")
            return
        
        sdk_path = current_item.text().replace(" (Default)", "")
        self.settings.set_default_sdk(sdk_path)
        self._refresh_sdk_list()
        QMessageBox.information(self, "Success", "Default SDK updated!")
    
    def _scan_sdks(self):
        """Auto-detect Flutter SDKs."""
        detected = self.flutter_service.detect_flutter_sdks()
        added_count = 0
        
        for sdk in detected:
            if self.settings.add_flutter_sdk(sdk):
                added_count += 1
        
        self._refresh_sdk_list()
        QMessageBox.information(
            self, "Scan Complete",
            f"Found {len(detected)} SDK(s), {added_count} new SDK(s) added."
        )
    
    def _browse_project_location(self):
        """Browse for default project location."""
        location = QFileDialog.getExistingDirectory(
            self, "Select Default Project Location", self.location_input.text()
        )
        if location:
            self.location_input.setText(location)
    
    def _add_scan_path(self):
        """Add a scan path via file dialog."""
        path = QFileDialog.getExistingDirectory(self, "Select Directory to Scan")
        if path:
            current_text = self.scan_paths_text.toPlainText()
            if current_text and not current_text.endswith("\n"):
                current_text += "\n"
            self.scan_paths_text.setPlainText(current_text + path)
    
    def _save_and_close(self):
        """Save settings and close dialog."""
        # Save general settings
        self.settings.set("default_project_location", self.location_input.text())
        self.settings.set("auto_scan", self.auto_scan_checkbox.isChecked())
        
        # Save scan paths
        scan_paths_text = self.scan_paths_text.toPlainText().strip()
        scan_paths = [p.strip() for p in scan_paths_text.split("\n") if p.strip()]
        self.settings.set("scan_paths", scan_paths)
        
        self.accept()


