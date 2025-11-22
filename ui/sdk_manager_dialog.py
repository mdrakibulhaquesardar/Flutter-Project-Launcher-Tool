"""Flutter SDK Manager dialog for downloading and managing SDK versions."""
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QListWidget, QListWidgetItem, QMessageBox,
                             QTabWidget, QWidget, QTextEdit, QCheckBox, QComboBox)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont
from services.sdk_manager_service import SDKManagerService
from services.flutter_service import FlutterService
from core.logger import Logger
from typing import Optional
import os


class VersionFetchThread(QThread):
    """Thread for fetching available versions."""
    versions_fetched = pyqtSignal(list)
    error = pyqtSignal(str)
    
    def __init__(self, sdk_manager: SDKManagerService):
        super().__init__()
        self.sdk_manager = sdk_manager
    
    def run(self):
        """Fetch versions."""
        try:
            versions = self.sdk_manager.get_available_versions()
            self.versions_fetched.emit(versions)
        except Exception as e:
            self.error.emit(str(e))


class SDKManagerDialog(QDialog):
    """Main SDK Manager dialog."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.sdk_manager = SDKManagerService()
        self.flutter_service = FlutterService()
        self.logger = Logger()
        self._init_ui()
        # Defer loading until dialog is shown
        QTimer.singleShot(0, self._load_installed_sdks)
        QTimer.singleShot(50, self._fetch_available_versions)  # Slight delay for versions fetch
    
    def _init_ui(self):
        """Initialize UI components."""
        self.setWindowTitle("Flutter SDK Manager")
        self.setMinimumSize(900, 600)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        # Header
        header_label = QLabel("Flutter SDK Manager", self)
        header_font = QFont()
        header_font.setBold(True)
        header_font.setPointSize(14)
        header_label.setFont(header_font)
        layout.addWidget(header_label)
        
        # Tabs
        tabs = QTabWidget(self)
        
        # Available Versions tab
        available_tab = QWidget()
        available_layout = QVBoxLayout(available_tab)
        
        filter_layout = QHBoxLayout()
        filter_label = QLabel("Filter:", available_tab)
        self.version_filter = QComboBox(available_tab)
        self.version_filter.addItems(["All", "Stable", "Beta", "Dev"])
        self.version_filter.currentTextChanged.connect(self._filter_versions)
        filter_layout.addWidget(filter_label)
        filter_layout.addWidget(self.version_filter)
        filter_layout.addStretch()
        
        refresh_btn = QPushButton("🔄 Refresh", available_tab)
        refresh_btn.clicked.connect(self._fetch_available_versions)
        filter_layout.addWidget(refresh_btn)
        
        available_layout.addLayout(filter_layout)
        
        self.available_list = QListWidget(available_tab)
        self.available_list.itemDoubleClicked.connect(self._on_version_double_clicked)
        available_layout.addWidget(self.available_list)
        
        download_btn = QPushButton("⬇️ Download & Install", available_tab)
        download_btn.clicked.connect(self._download_version)
        available_layout.addWidget(download_btn)
        
        tabs.addTab(available_tab, "Available Versions")
        
        # Installed SDKs tab
        installed_tab = QWidget()
        installed_layout = QVBoxLayout(installed_tab)
        
        self.installed_list = QListWidget(installed_tab)
        self.installed_list.itemDoubleClicked.connect(self._on_sdk_double_clicked)
        installed_layout.addWidget(self.installed_list)
        
        installed_btn_layout = QHBoxLayout()
        
        switch_btn = QPushButton("🔄 Switch to This SDK", installed_tab)
        switch_btn.clicked.connect(self._switch_sdk)
        installed_btn_layout.addWidget(switch_btn)
        
        remove_btn = QPushButton("🗑️ Remove", installed_tab)
        remove_btn.clicked.connect(self._remove_sdk)
        installed_btn_layout.addWidget(remove_btn)
        
        refresh_installed_btn = QPushButton("🔄 Refresh", installed_tab)
        refresh_installed_btn.clicked.connect(self._load_installed_sdks)
        installed_btn_layout.addWidget(refresh_installed_btn)
        
        installed_btn_layout.addStretch()
        installed_layout.addLayout(installed_btn_layout)
        
        tabs.addTab(installed_tab, "Installed SDKs")
        
        # PATH Management tab
        path_tab = QWidget()
        path_layout = QVBoxLayout(path_tab)
        
        path_info = QLabel("Environment PATH Management", path_tab)
        path_info.setFont(QFont("", 10, QFont.Weight.Bold))
        path_layout.addWidget(path_info)
        
        self.path_status = QTextEdit(path_tab)
        self.path_status.setReadOnly(True)
        self.path_status.setMaximumHeight(200)
        self.path_status.setFontFamily("Consolas")
        path_layout.addWidget(self.path_status)
        
        self.auto_path_checkbox = QCheckBox("Automatically manage PATH when switching SDKs", path_tab)
        self.auto_path_checkbox.setChecked(True)
        path_layout.addWidget(self.auto_path_checkbox)
        
        path_btn_layout = QHBoxLayout()
        
        add_path_btn = QPushButton("➕ Add Current SDK to PATH", path_tab)
        add_path_btn.clicked.connect(self._add_to_path)
        path_btn_layout.addWidget(add_path_btn)
        
        remove_path_btn = QPushButton("➖ Remove Flutter from PATH", path_tab)
        remove_path_btn.clicked.connect(self._remove_from_path)
        path_btn_layout.addWidget(remove_path_btn)
        
        refresh_path_btn = QPushButton("🔄 Refresh", path_tab)
        refresh_path_btn.clicked.connect(self._refresh_path_status)
        path_btn_layout.addWidget(refresh_path_btn)
        
        path_btn_layout.addStretch()
        path_layout.addLayout(path_btn_layout)
        
        path_layout.addStretch()
        tabs.addTab(path_tab, "PATH Management")
        
        layout.addWidget(tabs)
        
        # Close button
        close_layout = QHBoxLayout()
        close_layout.addStretch()
        
        close_btn = QPushButton("Close", self)
        close_btn.clicked.connect(self.accept)
        close_layout.addWidget(close_btn)
        
        layout.addLayout(close_layout)
        
        # Store versions
        self.available_versions = []
    
    def _fetch_available_versions(self):
        """Fetch available Flutter versions."""
        self.available_list.clear()
        self.available_list.addItem("Fetching versions from GitHub...")
        
        self.thread = VersionFetchThread(self.sdk_manager)
        self.thread.versions_fetched.connect(self._on_versions_fetched)
        self.thread.error.connect(self._on_fetch_error)
        self.thread.start()
    
    def _on_versions_fetched(self, versions: list):
        """Handle versions fetched."""
        self.available_versions = versions
        self._filter_versions()
    
    def _on_fetch_error(self, error: str):
        """Handle fetch error."""
        self.available_list.clear()
        self.available_list.addItem(f"Error: {error}")
        QMessageBox.warning(self, "Error", f"Could not fetch versions:\n{error}")
    
    def _filter_versions(self):
        """Filter versions by channel (like FVM)."""
        self.available_list.clear()
        
        filter_type = self.version_filter.currentText()
        filtered = self.available_versions
        
        # Filter by channel (same as FVM)
        if filter_type == "Stable":
            filtered = [v for v in filtered if v.get("channel", "").lower() == "stable"]
        elif filter_type == "Beta":
            filtered = [v for v in filtered if v.get("channel", "").lower() == "beta"]
        elif filter_type == "Dev":
            filtered = [v for v in filtered if v.get("channel", "").lower() == "dev"]
        # "All" shows everything
        
        # Show all versions (not just first 50)
        for version_info in filtered:
            version = version_info.get("version", "Unknown")
            channel = version_info.get("channel", "unknown")
            release_date = version_info.get("release_date", version_info.get("published_at", ""))
            
            # Format date
            date_display = ""
            if release_date:
                try:
                    # Parse ISO date and format
                    from datetime import datetime
                    dt = datetime.fromisoformat(release_date.replace('Z', '+00:00'))
                    date_display = dt.strftime("%Y-%m-%d")
                except:
                    date_display = release_date[:10] if len(release_date) >= 10 else release_date
            
            # Display format: Flutter 3.24.0 (stable) - 2024-01-15
            display_text = f"Flutter {version} ({channel})"
            if date_display:
                display_text += f" - {date_display}"
            
            item = QListWidgetItem(display_text)
            item.setData(Qt.ItemDataRole.UserRole, version_info)
            
            # Color code by channel
            if channel.lower() == "stable":
                item.setForeground(Qt.GlobalColor.green)
            elif channel.lower() == "beta":
                item.setForeground(Qt.GlobalColor.blue)
            elif channel.lower() == "dev":
                item.setForeground(Qt.GlobalColor.magenta)
            
            self.available_list.addItem(item)
    
    def _on_version_double_clicked(self, item: QListWidgetItem):
        """Handle double-click on version."""
        self._download_version()
    
    def _download_version(self):
        """Download selected version."""
        current_item = self.available_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "No Selection", "Please select a version to download.")
            return
        
        version_info = current_item.data(Qt.ItemDataRole.UserRole)
        version = version_info.get("version")
        
        reply = QMessageBox.question(
            self, "Download SDK",
            f"Download and install Flutter {version}?\n\n"
            f"This will download approximately 1-2 GB and may take several minutes.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        # Show download dialog with version info
        from ui.sdk_download_dialog import SDKDownloadDialog
        channel = version_info.get("channel", "stable")
        download_url = version_info.get("download_url") or version_info.get("archive")
        download_dialog = SDKDownloadDialog(version, channel=channel, download_url=download_url, parent=self)
        download_dialog.download_complete.connect(self._on_download_complete)
        download_dialog.exec()
    
    def _on_download_complete(self, version: str, zip_path: str):
        """Handle download completion and install."""
        reply = QMessageBox.question(
            self, "Install SDK",
            f"Download completed. Install Flutter {version} now?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self._install_sdk(zip_path, version)
    
    def _install_sdk(self, zip_path: str, version: str):
        """Install SDK from ZIP using background thread."""
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QProgressBar, QPushButton
        from pathlib import Path
        
        # Create installation dialog
        install_dialog = QDialog(self)
        install_dialog.setWindowTitle(f"Installing Flutter {version}")
        install_dialog.setMinimumSize(500, 200)
        install_dialog.setModal(True)
        
        layout = QVBoxLayout(install_dialog)
        
        status_label = QLabel(f"Preparing to install Flutter {version}...", install_dialog)
        layout.addWidget(status_label)
        
        progress_bar = QProgressBar(install_dialog)
        progress_bar.setRange(0, 0)  # Indeterminate
        layout.addWidget(progress_bar)
        
        cancel_btn = QPushButton("Cancel", install_dialog)
        cancel_btn.setEnabled(False)  # Don't allow cancel during installation
        layout.addWidget(cancel_btn)
        
        install_dialog.show()
        
        # Get install directory
        install_dir = self.sdk_manager.sdk_base_dir / f"flutter_{version}"
        
        # Create and start installation thread
        from ui.sdk_install_thread import SDKInstallThread
        self.install_thread = SDKInstallThread(zip_path, version, install_dir)
        
        def on_progress(message: str):
            status_label.setText(message)
            install_dialog.update()  # Force UI update
        
        def on_finished(success: bool, message: str):
            install_dialog.close()
            
            if success:
                # Automatically set as default and add to PATH if auto-manage is enabled
                auto_manage = self.auto_path_checkbox.isChecked()
                if auto_manage:
                    # Set as default SDK
                    self.sdk_manager.switch_sdk(message, update_path=True)
                    path_message = "\n\n✅ SDK has been set as default and added to PATH automatically.\nPlease restart your terminal/IDE for PATH changes to take effect."
                else:
                    path_message = "\n\nYou can now switch to this SDK from the 'Installed SDKs' tab."
                
                QMessageBox.information(
                    self, "Success",
                    f"Flutter {version} installed successfully!\n\n"
                    f"Location: {message}{path_message}"
                )
                self._load_installed_sdks()
                self._refresh_path_status()
            else:
                QMessageBox.warning(self, "Error", f"Installation failed:\n{message}")
        
        self.install_thread.progress.connect(on_progress)
        self.install_thread.finished.connect(on_finished)
        self.install_thread.start()
    
    def _load_installed_sdks(self):
        """Load installed SDKs."""
        self.installed_list.clear()
        
        installed = self.sdk_manager.get_installed_sdks()
        default_sdk = self.flutter_service.get_default_sdk()
        
        if not installed:
            self.installed_list.addItem("No SDKs installed")
            return
        
        for sdk_info in installed:
            path = sdk_info.get("path", "")
            version = sdk_info.get("version", "Unknown")
            managed = sdk_info.get("managed", False)
            
            display_text = f"Flutter {version}"
            if managed:
                display_text += " (Managed)"
            else:
                display_text += " (Manual)"
            
            if path == default_sdk:
                display_text += " [Default]"
            
            item = QListWidgetItem(display_text)
            item.setData(Qt.ItemDataRole.UserRole, path)
            item.setData(Qt.ItemDataRole.UserRole + 1, version)
            
            if path == default_sdk:
                item.setForeground(Qt.GlobalColor.green)
            
            self.installed_list.addItem(item)
    
    def _on_sdk_double_clicked(self, item: QListWidgetItem):
        """Handle double-click on SDK."""
        self._switch_sdk()
    
    def _switch_sdk(self):
        """Switch to selected SDK."""
        current_item = self.installed_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "No Selection", "Please select an SDK to switch to.")
            return
        
        sdk_path = current_item.data(Qt.ItemDataRole.UserRole)
        version = current_item.data(Qt.ItemDataRole.UserRole + 1)
        
        update_path = self.auto_path_checkbox.isChecked()
        
        success = self.sdk_manager.switch_sdk(sdk_path, update_path=update_path)
        
        if success:
            path_message = ""
            if update_path:
                path_message = "\n\n✅ Flutter has been added to PATH automatically.\nPlease restart your terminal/IDE for PATH changes to take effect."
            else:
                path_message = "\n\n⚠️ PATH was not updated. Enable 'Automatically manage PATH' to add Flutter to PATH."
            
            QMessageBox.information(
                self, "Success",
                f"Switched to Flutter {version}!{path_message}"
            )
            self._load_installed_sdks()
            self._refresh_path_status()
        else:
            QMessageBox.warning(self, "Error", "Failed to switch SDK.")
    
    def _remove_sdk(self):
        """Remove selected SDK."""
        current_item = self.installed_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "No Selection", "Please select an SDK to remove.")
            return
        
        sdk_path = current_item.data(Qt.ItemDataRole.UserRole)
        version = current_item.data(Qt.ItemDataRole.UserRole + 1)
        
        reply = QMessageBox.question(
            self, "Remove SDK",
            f"Remove Flutter {version}?\n\n"
            f"Path: {sdk_path}\n\n"
            f"This will delete the SDK files. Continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            success = self.sdk_manager.remove_sdk(sdk_path)
            if success:
                QMessageBox.information(self, "Success", "SDK removed successfully!")
                self._load_installed_sdks()
            else:
                QMessageBox.warning(self, "Error", "Failed to remove SDK.")
    
    def _add_to_path(self):
        """Add current SDK to PATH."""
        default_sdk = self.flutter_service.get_default_sdk()
        if not default_sdk:
            QMessageBox.warning(self, "No SDK", "No default SDK set.")
            return
        
        from pathlib import Path
        from utils.path_manager import PathManager
        
        path_manager = PathManager()
        bin_path = Path(default_sdk) / "bin"
        bin_path_str = str(bin_path.resolve())
        
        # Remove old Flutter paths first
        self.sdk_manager._remove_flutter_from_path()
        
        if path_manager.add_to_path(bin_path_str):
            QMessageBox.information(
                self, "Success",
                f"Added Flutter to PATH!\n\n"
                f"Path: {bin_path_str}\n\n"
                f"Please restart your terminal/IDE for changes to take effect."
            )
            self._refresh_path_status()
        else:
            QMessageBox.warning(self, "Error", f"Failed to add to PATH.\n\nPath: {bin_path_str}")
    
    def _remove_from_path(self):
        """Remove Flutter from PATH."""
        from utils.path_manager import PathManager
        
        path_manager = PathManager()
        
        # Get all SDK bin paths
        installed = self.sdk_manager.get_installed_sdks()
        removed_count = 0
        
        for sdk_info in installed:
            from pathlib import Path
            bin_path = Path(sdk_info["path"]) / "bin"
            if path_manager.remove_from_path(str(bin_path)):
                removed_count += 1
        
        if removed_count > 0:
            QMessageBox.information(
                self, "Success",
                f"Removed Flutter from PATH!\n\n"
                f"Please restart your terminal for changes to take effect."
            )
        else:
            QMessageBox.information(self, "Info", "Flutter not found in PATH.")
        
        self._refresh_path_status()
    
    def _refresh_path_status(self):
        """Refresh PATH status display."""
        from utils.path_manager import PathManager
        
        path_manager = PathManager()
        default_sdk = self.flutter_service.get_default_sdk()
        
        status_text = "PATH Status\n"
        status_text += "=" * 50 + "\n\n"
        
        if default_sdk:
            from pathlib import Path
            bin_path = Path(default_sdk) / "bin"
            in_path = path_manager.is_in_path(str(bin_path))
            
            status_text += f"Default SDK: {default_sdk}\n"
            status_text += f"Bin Path: {bin_path}\n"
            status_text += f"In PATH: {'✅ Yes' if in_path else '❌ No'}\n"
        else:
            status_text += "No default SDK set.\n"
        
        status_text += "\nCurrent PATH (Flutter related):\n"
        status_text += "-" * 50 + "\n"
        
        current_path = os.environ.get("PATH", "")
        flutter_paths = [p for p in current_path.split(os.pathsep) if "flutter" in p.lower() or "dart" in p.lower()]
        
        if flutter_paths:
            for path in flutter_paths:
                status_text += f"  {path}\n"
        else:
            status_text += "  (No Flutter/Dart paths found)\n"
        
        self.path_status.setPlainText(status_text)

