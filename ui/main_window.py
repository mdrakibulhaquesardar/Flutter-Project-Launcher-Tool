"""Main window for Flutter Project Launcher Tool."""
from PyQt6.QtWidgets import (QMainWindow, QMenuBar, QStatusBar, QMessageBox, 
                             QDialog, QVBoxLayout, QTextEdit, QPushButton, QLabel, QHBoxLayout)
from PyQt6.QtCore import Qt, QTimer
from ui.dashboard_widget import DashboardWidget
from ui.project_creator import ProjectCreator
from ui.settings_dialog import SettingsDialog
from ui.scan_thread import ScanProjectsThread
# Import dialogs at top for faster access
from ui.environment_info_dialog import EnvironmentInfoDialog
from ui.version_checker_dialog import VersionCheckerDialog
from ui.pub_cache_dialog import PubCacheDialog
from ui.upgrade_checker_dialog import UpgradeCheckerDialog
from ui.dependency_analyzer_dialog import DependencyAnalyzerDialog
from ui.emulator_manager_dialog import EmulatorManagerDialog
from ui.sdk_manager_dialog import SDKManagerDialog
from core.logger import Logger
from core.settings import Settings
from pathlib import Path
import os


class MainWindow(QMainWindow):
    """Main application window."""
    
    def __init__(self):
        super().__init__()
        self.logger = Logger()
        self.settings = Settings()
        self._init_ui()
        self._setup_menu()
        self._setup_statusbar()
        self._restore_window_state()
    
    def _init_ui(self):
        """Initialize UI components."""
        self.setWindowTitle("Flutter Project Launcher Tool")
        self.setMinimumSize(900, 700)
        
        # Create dashboard
        self.dashboard = DashboardWidget(self)
        self.dashboard.create_project_requested.connect(self._show_create_project)
        self.dashboard.settings_requested.connect(self._show_settings)
        
        self.setCentralWidget(self.dashboard)
        
        # Auto-scan on startup if enabled
        QTimer.singleShot(500, self._auto_scan_on_startup)
    
    def _setup_menu(self):
        """Setup menu bar."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("File")
        
        create_action = file_menu.addAction("New Project...")
        create_action.setShortcut("Ctrl+N")
        create_action.triggered.connect(self._show_create_project)
        
        file_menu.addSeparator()
        
        exit_action = file_menu.addAction("Exit")
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        
        # Tools menu
        tools_menu = menubar.addMenu("Tools")
        
        settings_action = tools_menu.addAction("Settings...")
        settings_action.setShortcut("Ctrl+,")
        settings_action.triggered.connect(self._show_settings)
        
        tools_menu.addSeparator()
        
        scan_action = tools_menu.addAction("Scan for Projects...")
        scan_action.triggered.connect(self._scan_projects)
        
        tools_menu.addSeparator()
        
        doctor_action = tools_menu.addAction("Flutter Doctor")
        doctor_action.triggered.connect(self._show_flutter_doctor)
        
        env_info_action = tools_menu.addAction("Environment Info")
        env_info_action.triggered.connect(self._show_environment_info)
        
        version_checker_action = tools_menu.addAction("Version Checker")
        version_checker_action.triggered.connect(self._show_version_checker)
        
        pub_cache_action = tools_menu.addAction("Pub Cache Manager")
        pub_cache_action.triggered.connect(self._show_pub_cache)
        
        upgrade_checker_action = tools_menu.addAction("Flutter Upgrade Checker")
        upgrade_checker_action.triggered.connect(self._show_upgrade_checker)
        
        tools_menu.addSeparator()
        
        dependency_analyzer_action = tools_menu.addAction("Dependency Analyzer")
        dependency_analyzer_action.triggered.connect(self._show_dependency_analyzer)
        
        emulator_manager_action = tools_menu.addAction("Emulator Manager")
        emulator_manager_action.triggered.connect(self._show_emulator_manager)
        
        tools_menu.addSeparator()
        
        sdk_manager_action = tools_menu.addAction("SDK Manager")
        sdk_manager_action.triggered.connect(self._show_sdk_manager)
        
        # Help menu
        help_menu = menubar.addMenu("Help")
        
        about_action = help_menu.addAction("About")
        about_action.triggered.connect(self._show_about)
    
    def _setup_statusbar(self):
        """Setup status bar."""
        self.statusBar().showMessage("Ready")
    
    def _show_create_project(self):
        """Show project creation dialog."""
        dialog = ProjectCreator(self)
        dialog.project_created.connect(self.dashboard.on_project_created)
        dialog.exec()
    
    def _show_settings(self):
        """Show settings dialog."""
        dialog = SettingsDialog(self)
        if dialog.exec() == dialog.DialogCode.Accepted:
            self.logger.info("Settings saved")
            # Refresh dashboard if needed
            self.dashboard._load_projects()
    
    def _get_common_scan_paths(self) -> list:
        """Get common paths to scan for Flutter projects."""
        paths = []
        home = Path.home()
        
        # Common project locations
        common_locations = [
            home / "Documents",
            home / "Projects",
            home / "Development",
            home / "Desktop",
            home / "flutter_projects",
            Path("C:/Users") if os.name == 'nt' else Path("/home"),
            Path("D:/Projects") if os.name == 'nt' and Path("D:/").exists() else None,
        ]
        
        # Add user's scan paths from settings
        scan_paths = self.settings.get("scan_paths", [])
        for path_str in scan_paths:
            path = Path(path_str)
            if path.exists() and path not in paths:
                paths.append(str(path))
        
        # Add common locations that exist
        for loc in common_locations:
            if loc and loc.exists() and str(loc) not in paths:
                paths.append(str(loc))
        
        return paths
    
    def _auto_scan_on_startup(self):
        """Auto-scan for projects on startup if enabled."""
        if not self.settings.get("auto_scan", True):
            return
        
        scan_paths = self._get_common_scan_paths()
        if not scan_paths:
            return
        
        self.logger.info(f"Auto-scanning {len(scan_paths)} path(s) on startup...")
        self._start_scan(scan_paths, show_dialog=False)
    
    def _scan_projects(self):
        """Scan for Flutter projects (manual scan)."""
        from PyQt6.QtWidgets import QFileDialog
        
        search_path = QFileDialog.getExistingDirectory(
            self, "Select Directory to Scan"
        )
        
        if search_path:
            self._start_scan([search_path], show_dialog=True)
    
    def _start_scan(self, search_paths: list, show_dialog: bool = True):
        """Start scanning projects in background thread."""
        if not search_paths:
            return
        
        self.statusBar().showMessage("Scanning for projects...")
        
        # Create and start scan thread
        self.scan_thread = ScanProjectsThread(search_paths, max_depth=3)
        self.scan_thread.progress.connect(self._on_scan_progress)
        self.scan_thread.found_project.connect(self._on_project_found)
        self.scan_thread.finished.connect(lambda count: self._on_scan_finished(count, show_dialog))
        self.scan_thread.start()
    
    def _on_scan_progress(self, message: str):
        """Handle scan progress updates."""
        self.statusBar().showMessage(message)
        self.logger.info(message)
    
    def _on_project_found(self, project: dict):
        """Handle found project."""
        self.logger.info(f"Found project: {project.get('name', 'Unknown')}")
    
    def _on_scan_finished(self, count: int, show_dialog: bool):
        """Handle scan completion."""
        self.dashboard._load_projects()
        message = f"Found {count} project(s)"
        self.statusBar().showMessage(message, 3000)
        
        if show_dialog and count > 0:
            QMessageBox.information(
                self, 
                "Scan Complete", 
                f"Found {count} Flutter project(s) and added to dashboard."
            )
    
    def _show_flutter_doctor(self):
        """Show Flutter Doctor output."""
        from services.flutter_service import FlutterService
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Flutter Doctor")
        dialog.setMinimumSize(700, 500)
        
        layout = QVBoxLayout(dialog)
        
        info_label = QLabel("Running Flutter Doctor...", dialog)
        layout.addWidget(info_label)
        
        output_text = QTextEdit(dialog)
        output_text.setReadOnly(True)
        output_text.setFontFamily("Consolas")
        output_text.setFontPointSize(9)
        layout.addWidget(output_text)
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        close_btn = QPushButton("Close", dialog)
        close_btn.clicked.connect(dialog.accept)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        
        # Run flutter doctor
        flutter_service = FlutterService()
        output_text.append("Running 'flutter doctor -v'...\n")
        output_text.append("=" * 70 + "\n")
        
        doctor_info = flutter_service.flutter_doctor()
        output_text.append(doctor_info.get("output", "No output"))
        
        if doctor_info.get("exit_code") == 0:
            info_label.setText("Flutter Doctor completed successfully")
            info_label.setStyleSheet("color: green;")
        else:
            info_label.setText("Flutter Doctor found some issues")
            info_label.setStyleSheet("color: orange;")
        
        dialog.exec()
    
    def _show_environment_info(self):
        """Show environment info dialog."""
        dialog = EnvironmentInfoDialog(self)
        dialog.exec()
    
    def _show_version_checker(self):
        """Show version checker dialog."""
        dialog = VersionCheckerDialog(self)
        dialog.exec()
    
    def _show_pub_cache(self):
        """Show pub cache management dialog."""
        dialog = PubCacheDialog(self)
        dialog.exec()
    
    def _show_upgrade_checker(self):
        """Show Flutter upgrade checker dialog."""
        dialog = UpgradeCheckerDialog(self)
        dialog.exec()
    
    def _show_dependency_analyzer(self):
        """Show dependency analyzer dialog."""
        # Get current project from dashboard
        current_project = self.dashboard.current_project if hasattr(self.dashboard, 'current_project') else None
        
        if not current_project:
            QMessageBox.information(
                self,
                "No Project Selected",
                "Please select a project from the dashboard first."
            )
            return
        
        dialog = DependencyAnalyzerDialog(current_project, self)
        dialog.exec()
    
    def _show_emulator_manager(self):
        """Show emulator manager dialog."""
        dialog = EmulatorManagerDialog(self)
        dialog.exec()
    
    def _show_sdk_manager(self):
        """Show SDK manager dialog."""
        dialog = SDKManagerDialog(self)
        if dialog.exec() == dialog.DialogCode.Accepted:
            # Refresh settings if SDK was changed
            self.dashboard._load_projects()
    
    def _show_about(self):
        """Show about dialog."""
        QMessageBox.about(
            self,
            "About Flutter Project Launcher Tool",
            """
            <h2>Flutter Project Launcher Tool</h2>
            <p>Version 1.0.0</p>
            <p>A desktop application for managing Flutter projects.</p>
            <p>Built with Python and PyQt6</p>
            """
        )
    
    def _restore_window_state(self):
        """Restore window geometry and state."""
        from PyQt6.QtCore import QByteArray
        import base64
        
        geometry_data = self.settings.get("window_geometry")
        state_data = self.settings.get("window_state")
        
        if geometry_data:
            # Convert from base64 string to QByteArray
            try:
                if isinstance(geometry_data, str):
                    # Try base64 decode
                    try:
                        geometry_bytes = base64.b64decode(geometry_data, validate=True)
                        geometry = QByteArray(geometry_bytes)
                        self.restoreGeometry(geometry)
                    except Exception:
                        # If base64 decode fails, might be old format - skip
                        self.logger.debug("Skipping invalid geometry data")
                elif isinstance(geometry_data, (bytes, bytearray)):
                    self.restoreGeometry(QByteArray(geometry_data))
                elif isinstance(geometry_data, QByteArray):
                    self.restoreGeometry(geometry_data)
            except Exception as e:
                self.logger.warning(f"Could not restore window geometry: {e}")
        
        if state_data:
            # Convert from base64 string to QByteArray
            try:
                if isinstance(state_data, str):
                    # Try base64 decode
                    try:
                        state_bytes = base64.b64decode(state_data, validate=True)
                        state = QByteArray(state_bytes)
                        self.restoreState(state)
                    except Exception:
                        # If base64 decode fails, might be old format - skip
                        self.logger.debug("Skipping invalid state data")
                elif isinstance(state_data, (bytes, bytearray)):
                    self.restoreState(QByteArray(state_data))
                elif isinstance(state_data, QByteArray):
                    self.restoreState(state_data)
            except Exception as e:
                self.logger.warning(f"Could not restore window state: {e}")
    
    def closeEvent(self, event):
        """Handle window close event."""
        import base64
        
        # Save window state as base64 strings
        geometry = self.saveGeometry()
        state = self.saveState()
        
        # Convert QByteArray to base64 string for database storage
        geometry_str = base64.b64encode(geometry.data()).decode('utf-8')
        state_str = base64.b64encode(state.data()).decode('utf-8')
        
        self.settings.set("window_geometry", geometry_str)
        self.settings.set("window_state", state_str)
        self.settings.save()
        
        event.accept()


