"""Settings dialog for Flutter Project Launcher Tool."""
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QListWidget, QListWidgetItem,
                             QMessageBox, QFileDialog, QTabWidget, QWidget, QCheckBox, QTextEdit,
                             QComboBox, QSpinBox, QGroupBox)
from PyQt6.QtCore import Qt
from services.flutter_service import FlutterService
from core.settings import Settings
from core.logger import Logger
from core.database import Database
from utils.path_utils import validate_flutter_sdk
from pathlib import Path
import os
import shutil


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
        from core.branding import Branding
        
        self.setWindowTitle("Settings")
        self.setMinimumSize(600, 500)
        
        # Apply branding icon
        Branding.apply_window_icon(self)
        
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
        
        # Editor Preferences tab
        editor_tab = QWidget()
        editor_layout = QVBoxLayout(editor_tab)
        editor_layout.setSpacing(15)
        
        # VS Code section
        vscode_group = QGroupBox("VS Code", self)
        vscode_layout = QVBoxLayout(vscode_group)
        vscode_layout.setSpacing(10)
        
        vscode_info = QLabel("Path to VS Code executable:", self)
        vscode_layout.addWidget(vscode_info)
        
        vscode_input_layout = QHBoxLayout()
        self.vscode_input = QLineEdit(self)
        vscode_browse_btn = QPushButton("Browse...", self)
        vscode_browse_btn.clicked.connect(self._browse_vscode_path)
        vscode_detect_btn = QPushButton("Auto-detect", self)
        vscode_detect_btn.clicked.connect(self._detect_vscode)
        vscode_test_btn = QPushButton("Test", self)
        vscode_test_btn.clicked.connect(self._test_vscode)
        vscode_input_layout.addWidget(self.vscode_input)
        vscode_input_layout.addWidget(vscode_browse_btn)
        vscode_input_layout.addWidget(vscode_detect_btn)
        vscode_input_layout.addWidget(vscode_test_btn)
        vscode_layout.addLayout(vscode_input_layout)
        
        editor_layout.addWidget(vscode_group)
        
        # Android Studio section
        as_group = QGroupBox("Android Studio", self)
        as_layout = QVBoxLayout(as_group)
        as_layout.setSpacing(10)
        
        as_info = QLabel("Path to Android Studio executable:", self)
        as_layout.addWidget(as_info)
        
        as_input_layout = QHBoxLayout()
        self.as_input = QLineEdit(self)
        as_browse_btn = QPushButton("Browse...", self)
        as_browse_btn.clicked.connect(self._browse_as_path)
        as_detect_btn = QPushButton("Auto-detect", self)
        as_detect_btn.clicked.connect(self._detect_android_studio)
        as_test_btn = QPushButton("Test", self)
        as_test_btn.clicked.connect(self._test_android_studio)
        as_input_layout.addWidget(self.as_input)
        as_input_layout.addWidget(as_browse_btn)
        as_input_layout.addWidget(as_detect_btn)
        as_input_layout.addWidget(as_test_btn)
        as_layout.addLayout(as_input_layout)
        
        editor_layout.addWidget(as_group)
        editor_layout.addStretch()
        tabs.addTab(editor_tab, "Editor Preferences")
        
        # Advanced Settings tab
        advanced_tab = QWidget()
        advanced_layout = QVBoxLayout(advanced_tab)
        advanced_layout.setSpacing(15)
        
        # Debug mode
        self.debug_mode_checkbox = QCheckBox("Enable Debug Mode", self)
        advanced_layout.addWidget(self.debug_mode_checkbox)
        
        # Log level
        log_level_layout = QHBoxLayout()
        log_level_label = QLabel("Log Level:", self)
        self.log_level_combo = QComboBox(self)
        self.log_level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR"])
        log_level_layout.addWidget(log_level_label)
        log_level_layout.addWidget(self.log_level_combo)
        log_level_layout.addStretch()
        advanced_layout.addLayout(log_level_layout)
        
        # Console settings group
        console_group = QGroupBox("Console Settings", self)
        console_layout = QVBoxLayout(console_group)
        console_layout.setSpacing(10)
        
        # Font size
        font_size_layout = QHBoxLayout()
        font_size_label = QLabel("Font Size:", self)
        self.font_size_spinbox = QSpinBox(self)
        self.font_size_spinbox.setRange(6, 24)
        self.font_size_spinbox.setValue(9)
        font_size_layout.addWidget(font_size_label)
        font_size_layout.addWidget(self.font_size_spinbox)
        font_size_layout.addStretch()
        console_layout.addLayout(font_size_layout)
        
        # Max lines
        max_lines_layout = QHBoxLayout()
        max_lines_label = QLabel("Max Lines:", self)
        self.max_lines_spinbox = QSpinBox(self)
        self.max_lines_spinbox.setRange(100, 10000)
        self.max_lines_spinbox.setValue(1000)
        max_lines_layout.addWidget(max_lines_label)
        max_lines_layout.addWidget(self.max_lines_spinbox)
        max_lines_layout.addStretch()
        console_layout.addLayout(max_lines_layout)
        
        advanced_layout.addWidget(console_group)
        
        # Database management group
        db_group = QGroupBox("Database Management", self)
        db_layout = QVBoxLayout(db_group)
        db_layout.setSpacing(10)
        
        db_info = QLabel("Backup or restore application database:", self)
        db_layout.addWidget(db_info)
        
        db_btn_layout = QHBoxLayout()
        self.db_backup_btn = QPushButton("Backup Database", self)
        self.db_backup_btn.clicked.connect(self._backup_database)
        self.db_restore_btn = QPushButton("Restore Database", self)
        self.db_restore_btn.clicked.connect(self._restore_database)
        db_btn_layout.addWidget(self.db_backup_btn)
        db_btn_layout.addWidget(self.db_restore_btn)
        db_btn_layout.addStretch()
        db_layout.addLayout(db_btn_layout)
        
        advanced_layout.addWidget(db_group)
        advanced_layout.addStretch()
        tabs.addTab(advanced_tab, "Advanced")
        
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
        
        # Load editor preferences
        vscode_path = self.settings.get_vscode_path()
        if vscode_path:
            self.vscode_input.setText(vscode_path)
        as_path = self.settings.get_android_studio_path()
        if as_path:
            self.as_input.setText(as_path)
        
        # Load advanced settings
        self.debug_mode_checkbox.setChecked(self.settings.get_debug_mode())
        log_level = self.settings.get_log_level()
        index = self.log_level_combo.findText(log_level)
        if index >= 0:
            self.log_level_combo.setCurrentIndex(index)
        self.font_size_spinbox.setValue(self.settings.get_console_font_size())
        self.max_lines_spinbox.setValue(self.settings.get_console_max_lines())
    
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
    
    def _browse_vscode_path(self):
        """Browse for VS Code executable."""
        if os.name == 'nt':  # Windows
            file_path, _ = QFileDialog.getOpenFileName(
                self, "Select VS Code Executable", "",
                "Executable Files (*.exe);;All Files (*.*)"
            )
        else:
            file_path, _ = QFileDialog.getOpenFileName(
                self, "Select VS Code Executable", "",
                "All Files (*.*)"
            )
        if file_path:
            self.vscode_input.setText(file_path)
    
    def _browse_as_path(self):
        """Browse for Android Studio executable."""
        if os.name == 'nt':  # Windows
            file_path, _ = QFileDialog.getOpenFileName(
                self, "Select Android Studio Executable", "",
                "Executable Files (*.exe);;All Files (*.*)"
            )
        else:
            file_path, _ = QFileDialog.getOpenFileName(
                self, "Select Android Studio Executable", "",
                "All Files (*.*)"
            )
        if file_path:
            self.as_input.setText(file_path)
    
    def _detect_vscode(self):
        """Auto-detect VS Code installation."""
        detected_paths = []
        
        if os.name == 'nt':  # Windows
            # Common VS Code paths on Windows
            user_home = Path.home()
            common_paths = [
                user_home / "AppData" / "Local" / "Programs" / "Microsoft VS Code" / "Code.exe",
                Path("C:/Program Files/Microsoft VS Code/Code.exe"),
                Path("C:/Program Files (x86)/Microsoft VS Code/Code.exe"),
            ]
        else:  # Linux/macOS
            common_paths = [
                Path("/usr/bin/code"),
                Path("/usr/local/bin/code"),
                Path.home() / ".local" / "bin" / "code",
            ]
        
        for path in common_paths:
            if path.exists():
                detected_paths.append(str(path))
                break
        
        if detected_paths:
            self.vscode_input.setText(detected_paths[0])
            QMessageBox.information(self, "Success", f"VS Code detected at:\n{detected_paths[0]}")
        else:
            QMessageBox.warning(self, "Not Found", "VS Code not found in common installation paths.")
    
    def _detect_android_studio(self):
        """Auto-detect Android Studio installation."""
        detected_paths = []
        
        if os.name == 'nt':  # Windows
            # Common Android Studio paths on Windows
            user_home = Path.home()
            common_paths = [
                Path("C:/Program Files/Android/Android Studio/bin/studio64.exe"),
                user_home / "AppData" / "Local" / "Programs" / "Android Studio" / "bin" / "studio64.exe",
                Path("C:/Program Files (x86)/Android/Android Studio/bin/studio64.exe"),
            ]
        else:  # Linux/macOS
            common_paths = [
                Path("/usr/local/android-studio/bin/studio.sh"),
                Path("/opt/android-studio/bin/studio.sh"),
                Path.home() / "android-studio" / "bin" / "studio.sh",
            ]
        
        for path in common_paths:
            if path.exists():
                detected_paths.append(str(path))
                break
        
        if detected_paths:
            self.as_input.setText(detected_paths[0])
            QMessageBox.information(self, "Success", f"Android Studio detected at:\n{detected_paths[0]}")
        else:
            QMessageBox.warning(self, "Not Found", "Android Studio not found in common installation paths.")
    
    def _test_vscode(self):
        """Test VS Code path."""
        path = self.vscode_input.text().strip()
        if not path:
            QMessageBox.warning(self, "No Path", "Please enter a VS Code path.")
            return
        
        if Path(path).exists():
            QMessageBox.information(self, "Success", f"VS Code executable found:\n{path}")
        else:
            QMessageBox.warning(self, "Not Found", f"VS Code executable not found at:\n{path}")
    
    def _test_android_studio(self):
        """Test Android Studio path."""
        path = self.as_input.text().strip()
        if not path:
            QMessageBox.warning(self, "No Path", "Please enter an Android Studio path.")
            return
        
        if Path(path).exists():
            QMessageBox.information(self, "Success", f"Android Studio executable found:\n{path}")
        else:
            QMessageBox.warning(self, "Not Found", f"Android Studio executable not found at:\n{path}")
    
    def _backup_database(self):
        """Backup database to file."""
        db = Database()
        backup_path, _ = QFileDialog.getSaveFileName(
            self, "Backup Database", "flutter_launcher_backup.db",
            "Database Files (*.db);;All Files (*.*)"
        )
        if backup_path:
            try:
                backup_file = db.backup_database(Path(backup_path))
                QMessageBox.information(self, "Success", f"Database backed up to:\n{backup_file}")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to backup database:\n{str(e)}")
    
    def _restore_database(self):
        """Restore database from file."""
        reply = QMessageBox.warning(
            self, "Confirm Restore",
            "Restoring database will replace all current data.\n"
            "Make sure you have a backup!\n\n"
            "Continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        backup_path, _ = QFileDialog.getOpenFileName(
            self, "Restore Database", "",
            "Database Files (*.db);;All Files (*.*)"
        )
        if backup_path:
            try:
                db = Database()
                # Backup current database first
                current_backup = db.backup_database()
                
                # Copy backup file to database location
                shutil.copy2(backup_path, db.db_file)
                
                QMessageBox.information(
                    self, "Success",
                    f"Database restored from:\n{backup_path}\n\n"
                    f"Previous database backed up to:\n{current_backup}"
                )
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to restore database:\n{str(e)}")
    
    def _save_and_close(self):
        """Save settings and close dialog."""
        # Save general settings
        self.settings.set("default_project_location", self.location_input.text())
        self.settings.set("auto_scan", self.auto_scan_checkbox.isChecked())
        
        # Save scan paths
        scan_paths_text = self.scan_paths_text.toPlainText().strip()
        scan_paths = [p.strip() for p in scan_paths_text.split("\n") if p.strip()]
        self.settings.set("scan_paths", scan_paths)
        
        # Save editor preferences
        vscode_path = self.vscode_input.text().strip()
        self.settings.set_vscode_path(vscode_path if vscode_path else None)
        as_path = self.as_input.text().strip()
        self.settings.set_android_studio_path(as_path if as_path else None)
        
        # Save advanced settings
        self.settings.set_debug_mode(self.debug_mode_checkbox.isChecked())
        self.settings.set_log_level(self.log_level_combo.currentText())
        self.settings.set_console_font_size(self.font_size_spinbox.value())
        self.settings.set_console_max_lines(self.max_lines_spinbox.value())
        
        # Update logger level if changed
        logger = Logger()
        logger.set_log_level(self.log_level_combo.currentText())
        
        self.accept()


