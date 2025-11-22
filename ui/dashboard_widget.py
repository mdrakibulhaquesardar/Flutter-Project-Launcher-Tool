"""Dashboard widget for Flutter Project Launcher Tool."""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QScrollArea, QLabel, QMessageBox, QMenu, QProgressBar)
from PyQt6.QtCore import Qt, pyqtSignal, QThread
from core.commands import FlutterCommandThread
from PyQt6.QtGui import QFont
from services.project_service import ProjectService
from services.device_service import DeviceService
from widgets.project_item import ProjectItem
from ui.console_widget import ConsoleWidget
from ui.device_selector import DeviceSelector
from ui.project_details_dialog import ProjectDetailsDialog
from ui.project_load_thread import ProjectLoadThread
from ui.project_refresh_thread import ProjectRefreshThread
from core.logger import Logger
from pathlib import Path
import subprocess
import os
from typing import Optional


class DashboardWidget(QWidget):
    """Main dashboard showing projects and quick actions."""
    
    # Signals
    create_project_requested = pyqtSignal()
    settings_requested = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.project_service = ProjectService()
        self.device_service = DeviceService()
        self.logger = Logger()
        self.current_project: Optional[str] = None
        self.load_thread: Optional[ProjectLoadThread] = None
        self.refresh_thread: Optional[ProjectRefreshThread] = None
        self._init_ui()
        self._load_projects()
    
    def _init_ui(self):
        """Initialize UI components."""
        from core.theme import Theme
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Set background color (use system default if BACKGROUND is empty)
        if Theme.BACKGROUND:
            self.setStyleSheet(f"background-color: {Theme.BACKGROUND};")
        
        # Header
        header_layout = QHBoxLayout()
        
        title = QLabel("Flutter Projects", self)
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title.setFont(title_font)
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Create project button
        self.create_btn = QPushButton("➕ Create Project", self)
        self.create_btn.clicked.connect(self.create_project_requested.emit)
        header_layout.addWidget(self.create_btn)
        
        # Refresh button
        self.refresh_btn = QPushButton("🔄 Refresh", self)
        self.refresh_btn.clicked.connect(lambda: self._load_projects(refresh_versions=True))
        header_layout.addWidget(self.refresh_btn)
        
        # Settings button
        self.settings_btn = QPushButton("⚙️ Settings", self)
        self.settings_btn.clicked.connect(self.settings_requested.emit)
        header_layout.addWidget(self.settings_btn)
        
        layout.addLayout(header_layout)
        
        # Projects list area
        self.projects_scroll = QScrollArea(self)
        self.projects_scroll.setWidgetResizable(True)
        self.projects_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        self.projects_widget = QWidget()
        self.projects_layout = QVBoxLayout(self.projects_widget)
        self.projects_layout.setSpacing(10)
        self.projects_layout.addStretch()
        
        self.projects_scroll.setWidget(self.projects_widget)
        layout.addWidget(self.projects_scroll, 1)
        
        # Quick actions (shown when project selected)
        self.actions_widget = QWidget(self)
        self.actions_widget.setVisible(False)
        actions_layout = QHBoxLayout(self.actions_widget)
        actions_layout.setSpacing(10)
        
        actions_label = QLabel("Quick Actions:", self.actions_widget)
        actions_label.setFont(QFont("", 10, QFont.Weight.Bold))
        actions_layout.addWidget(actions_label)
        
        self.run_btn = QPushButton("🏃 Run", self.actions_widget)
        self.run_btn.clicked.connect(self._run_project)
        actions_layout.addWidget(self.run_btn)
        
        self.build_apk_btn = QPushButton("📦 Build APK", self.actions_widget)
        self.build_apk_btn.clicked.connect(self._build_apk)
        actions_layout.addWidget(self.build_apk_btn)
        
        self.build_bundle_btn = QPushButton("🎁 Build Bundle", self.actions_widget)
        self.build_bundle_btn.clicked.connect(self._build_bundle)
        actions_layout.addWidget(self.build_bundle_btn)
        
        self.pub_get_btn = QPushButton("🔄 Pub Get", self.actions_widget)
        self.pub_get_btn.clicked.connect(self._pub_get)
        actions_layout.addWidget(self.pub_get_btn)
        
        self.clean_btn = QPushButton("♻ Clean", self.actions_widget)
        self.clean_btn.clicked.connect(self._clean_project)
        actions_layout.addWidget(self.clean_btn)
        
        self.details_btn = QPushButton("ℹ️ Details", self.actions_widget)
        self.details_btn.clicked.connect(self._show_project_details)
        actions_layout.addWidget(self.details_btn)
        
        actions_layout.addStretch()
        
        self.open_vscode_btn = QPushButton("📝 VS Code", self.actions_widget)
        self.open_vscode_btn.clicked.connect(self._open_vscode)
        actions_layout.addWidget(self.open_vscode_btn)
        
        self.open_android_studio_btn = QPushButton("🛠 Android Studio", self.actions_widget)
        self.open_android_studio_btn.clicked.connect(self._open_android_studio)
        actions_layout.addWidget(self.open_android_studio_btn)
        
        self.open_folder_btn = QPushButton("📂 Open Folder", self.actions_widget)
        self.open_folder_btn.clicked.connect(self._open_folder)
        actions_layout.addWidget(self.open_folder_btn)
        
        layout.addWidget(self.actions_widget)
        
        # Progress bar (for build commands and project loading)
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setVisible(False)
        self.progress_bar.setRange(0, 0)  # Indeterminate
        self.progress_bar.setFormat("Building... %p%")
        layout.addWidget(self.progress_bar)
        
        # Loading status label
        self.loading_label = QLabel("", self)
        self.loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        from core.theme import Theme
        self.loading_label.setStyleSheet(f"color: {Theme.PRIMARY}; font-size: 9pt;")
        self.loading_label.setVisible(False)
        layout.addWidget(self.loading_label)
        
        # Console (initially hidden, can be toggled)
        self.console = ConsoleWidget(self)
        self.console.setVisible(False)
        layout.addWidget(self.console)
    
    def _load_projects(self, refresh_versions: bool = False):
        """Load and display recent projects using background thread."""
        # Clear existing projects
        while self.projects_layout.count() > 1:  # Keep stretch
            item = self.projects_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Stop any existing threads
        if self.load_thread and self.load_thread.isRunning():
            self.load_thread.terminate()
            self.load_thread.wait()
        if self.refresh_thread and self.refresh_thread.isRunning():
            self.refresh_thread.terminate()
            self.refresh_thread.wait()
        
        # Show loading indicator
        self.progress_bar.setVisible(True)
        self.progress_bar.setFormat("Loading projects...")
        self.loading_label.setVisible(True)
        self.loading_label.setText("Loading projects...")
        self.refresh_btn.setEnabled(False)
        
        # If refresh_versions is True, first load projects, then refresh them in parallel
        if refresh_versions:
            # First load projects
            self.load_thread = ProjectLoadThread(refresh_versions=False)
            self.load_thread.progress.connect(self._on_load_progress)
            self.load_thread.project_loaded.connect(self._on_project_loaded)
            self.load_thread.finished.connect(self._on_projects_loaded_for_refresh)
            self.load_thread.error.connect(self._on_load_error)
            self.load_thread.start()
        else:
            # Just load projects normally
            self.load_thread = ProjectLoadThread(refresh_versions=False)
            self.load_thread.progress.connect(self._on_load_progress)
            self.load_thread.project_loaded.connect(self._on_project_loaded)
            self.load_thread.finished.connect(self._on_projects_loaded)
            self.load_thread.error.connect(self._on_load_error)
            self.load_thread.start()
    
    def _on_load_progress(self, message: str):
        """Handle loading progress updates."""
        self.loading_label.setText(message)
        self.logger.info(message)
    
    def _on_project_loaded(self, project_data: dict):
        """Handle single project loaded - add it to UI progressively."""
        project_item = ProjectItem(project_data, self)
        project_item.clicked.connect(self._on_project_selected)
        project_item.run_clicked.connect(self._on_project_run)
        project_item.open_clicked.connect(self._on_project_open)
        self.projects_layout.insertWidget(self.projects_layout.count() - 1, project_item)
    
    def _on_projects_loaded(self, projects: list):
        """Handle all projects loaded."""
        self.progress_bar.setVisible(False)
        self.loading_label.setVisible(False)
        self.refresh_btn.setEnabled(True)
        
        if not projects:
            no_projects = QLabel("No projects found. Create a new project to get started!", self)
            no_projects.setAlignment(Qt.AlignmentFlag.AlignCenter)
            from core.theme import Theme
            no_projects.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; padding: 20px;")
            self.projects_layout.insertWidget(0, no_projects)
        
        self.logger.info(f"Loaded {len(projects)} project(s)")
    
    def _on_projects_loaded_for_refresh(self, projects: list):
        """Handle projects loaded, now refresh versions in parallel."""
        if not projects:
            self._on_projects_loaded(projects)
            return
        
        # Clear existing projects before refreshing
        while self.projects_layout.count() > 1:  # Keep stretch
            item = self.projects_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Now refresh versions in parallel
        self.loading_label.setText(f"Refreshing versions for {len(projects)} projects...")
        self.progress_bar.setFormat("Refreshing versions... %p%")
        
        self.refresh_thread = ProjectRefreshThread(projects, max_workers=4)
        self.refresh_thread.progress.connect(self._on_load_progress)
        self.refresh_thread.project_updated.connect(self._on_project_refreshed)
        self.refresh_thread.finished.connect(self._on_refresh_finished)
        self.refresh_thread.error.connect(self._on_load_error)
        self.refresh_thread.start()
    
    def _on_project_refreshed(self, project_data: dict):
        """Handle single project refreshed - add to UI."""
        # Add refreshed project to UI
        project_item = ProjectItem(project_data, self)
        project_item.clicked.connect(self._on_project_selected)
        project_item.run_clicked.connect(self._on_project_run)
        project_item.open_clicked.connect(self._on_project_open)
        self.projects_layout.insertWidget(self.projects_layout.count() - 1, project_item)
    
    def _on_refresh_finished(self, projects: list):
        """Handle refresh finished."""
        self.progress_bar.setVisible(False)
        self.loading_label.setVisible(False)
        self.refresh_btn.setEnabled(True)
        self.logger.info(f"Refreshed {len(projects)} project(s)")
    
    def _on_load_error(self, error_message: str):
        """Handle loading error."""
        self.progress_bar.setVisible(False)
        self.loading_label.setVisible(False)
        self.refresh_btn.setEnabled(True)
        self.logger.error(error_message)
        QMessageBox.warning(self, "Error", f"Error loading projects:\n{error_message}")
    
    def _on_project_selected(self, project_path: str):
        """Handle project selection."""
        self.current_project = project_path
        self.actions_widget.setVisible(True)
        self.logger.info(f"Selected project: {project_path}")
    
    def _show_project_details(self):
        """Show project details dialog."""
        if not self.current_project:
            QMessageBox.warning(self, "No Project", "Please select a project first.")
            return
        
        dialog = ProjectDetailsDialog(self.current_project, self)
        dialog.exec()
    
    def _on_project_run(self, project_path: str):
        """Handle run project action."""
        self.current_project = project_path
        self._run_project()
    
    def _on_project_open(self, project_path: str):
        """Handle open project action."""
        self._open_folder(project_path)
    
    def _run_project(self):
        """Run Flutter project."""
        if not self.current_project:
            QMessageBox.warning(self, "No Project", "Please select a project first.")
            return
        
        # Get available devices
        devices = self.device_service.get_available_devices()
        
        # If no devices, try to get all devices
        if not devices:
            devices = self.device_service.get_connected_devices()
        
        device_id = None
        
        if len(devices) == 0:
            QMessageBox.warning(
                self, 
                "No Devices", 
                "No devices found. Please:\n"
                "• Connect a physical device via USB\n"
                "• Start an emulator\n"
                "• Verify with 'flutter devices' command"
            )
            return
        elif len(devices) == 1:
            # Only one device, use it directly
            device_id = devices[0].get("id")
            device_name = devices[0].get("name", "Unknown")
            self._execute_run(device_id, device_name)
        else:
            # Multiple devices, show selection dialog
            dialog = DeviceSelector(self)
            dialog.device_selected.connect(
                lambda dev_id: self._execute_run(dev_id, None)
            )
            dialog.exec()
    
    def _execute_run(self, device_id: str, device_name: Optional[str] = None):
        """Execute the run command with selected device."""
        # Show console
        self.console.setVisible(True)
        self.console.clear()
        self.console.append(f"Running project: {self.current_project}")
        
        if device_name:
            self.console.append(f"Using device: {device_name}")
        elif device_id:
            device = self.device_service.get_device_by_id(device_id)
            if device:
                self.console.append(f"Using device: {device.get('name', 'Unknown')}")
        
        # Run project asynchronously
        sdk = self.project_service.flutter_service.get_default_sdk()
        from utils.path_utils import get_flutter_executable
        flutter_exe = get_flutter_executable(sdk)
        
        if not flutter_exe:
            self.console.append_error("Flutter SDK not found. Please configure in Settings.")
            return
        
        args = [flutter_exe, "run"]
        if device_id:
            args.extend(["-d", device_id])
        
        self._run_command_async(args, self.current_project)
    
    def _build_apk(self):
        """Build APK."""
        if not self.current_project:
            QMessageBox.warning(self, "No Project", "Please select a project first.")
            return
        
        self.console.setVisible(True)
        self.console.clear()
        self.console.append("Building APK (this may take a few minutes)...")
        
        sdk = self.project_service.flutter_service.get_default_sdk()
        from utils.path_utils import get_flutter_executable
        flutter_exe = get_flutter_executable(sdk)
        
        if not flutter_exe:
            self.console.append_error("Flutter SDK not found. Please configure in Settings.")
            return
        
        args = [flutter_exe, "build", "apk", "--release"]
        self._run_command_async(args, self.current_project, show_progress=True)
    
    def _build_bundle(self):
        """Build App Bundle."""
        if not self.current_project:
            QMessageBox.warning(self, "No Project", "Please select a project first.")
            return
        
        self.console.setVisible(True)
        self.console.clear()
        self.console.append("Building App Bundle (this may take a few minutes)...")
        
        sdk = self.project_service.flutter_service.get_default_sdk()
        from utils.path_utils import get_flutter_executable
        flutter_exe = get_flutter_executable(sdk)
        
        if not flutter_exe:
            self.console.append_error("Flutter SDK not found. Please configure in Settings.")
            return
        
        args = [flutter_exe, "build", "appbundle", "--release"]
        self._run_command_async(args, self.current_project, show_progress=True)
    
    def _pub_get(self):
        """Run flutter pub get."""
        if not self.current_project:
            QMessageBox.warning(self, "No Project", "Please select a project first.")
            return
        
        self.console.setVisible(True)
        self.console.clear()
        self.console.append("Running flutter pub get...")
        
        sdk = self.project_service.flutter_service.get_default_sdk()
        from utils.path_utils import get_flutter_executable
        flutter_exe = get_flutter_executable(sdk)
        
        if not flutter_exe:
            self.console.append_error("Flutter SDK not found. Please configure in Settings.")
            return
        
        args = [flutter_exe, "pub", "get"]
        self._run_command_async(args, self.current_project)
    
    def _clean_project(self):
        """Clean Flutter project."""
        if not self.current_project:
            QMessageBox.warning(self, "No Project", "Please select a project first.")
            return
        
        reply = QMessageBox.question(
            self, "Confirm Clean",
            "This will clean the build files. Continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.console.setVisible(True)
            self.console.clear()
            self.console.append("Cleaning project...")
            
            sdk = self.project_service.flutter_service.get_default_sdk()
            from utils.path_utils import get_flutter_executable
            flutter_exe = get_flutter_executable(sdk)
            
            if not flutter_exe:
                self.console.append_error("Flutter SDK not found. Please configure in Settings.")
                return
            
            args = [flutter_exe, "clean"]
            self._run_command_async(args, self.current_project)
    
    def _open_vscode(self, project_path: Optional[str] = None):
        """Open project in VS Code."""
        path = project_path or self.current_project
        if not path:
            QMessageBox.warning(self, "No Project", "Please select a project first.")
            return
        
        try:
            if os.name == 'nt':
                subprocess.Popen(["code", path], shell=True)
            else:
                subprocess.Popen(["code", path])
            self.logger.info(f"Opened in VS Code: {path}")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not open VS Code: {e}")
    
    def _open_android_studio(self, project_path: Optional[str] = None):
        """Open project in Android Studio."""
        path = project_path or self.current_project
        if not path:
            QMessageBox.warning(self, "No Project", "Please select a project first.")
            return
        
        try:
            if os.name == 'nt':
                subprocess.Popen(["studio64", path], shell=True)
            else:
                subprocess.Popen(["studio", path])
            self.logger.info(f"Opened in Android Studio: {path}")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not open Android Studio: {e}")
    
    def _open_folder(self, project_path: Optional[str] = None):
        """Open project folder in file explorer."""
        path = project_path or self.current_project
        if not path:
            QMessageBox.warning(self, "No Project", "Please select a project first.")
            return
        
        try:
            if os.name == 'nt':
                os.startfile(path)
            elif os.name == 'posix':
                subprocess.Popen(["xdg-open", path])
            elif os.name == 'darwin':
                subprocess.Popen(["open", path])
            self.logger.info(f"Opened folder: {path}")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not open folder: {e}")
    
    def _run_command_async(self, args: list, cwd: Optional[str] = None, show_progress: bool = False):
        """Run command asynchronously and stream output to console."""
        # Show console
        self.console.setVisible(True)
        
        # Show/hide progress bar
        if show_progress:
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 0)  # Indeterminate
        
        # Create and start command thread
        thread = FlutterCommandThread(args, cwd=cwd)
        
        # Connect signals
        thread.output.connect(lambda text: self.console.append(text))
        thread.error.connect(lambda text: self.console.append_error(text))
        
        def on_finished(exit_code: int):
            if show_progress:
                self.progress_bar.setVisible(False)
            
            if exit_code == 0:
                self.console.append_success("✓ Command completed successfully")
            else:
                self.console.append_error(f"✗ Command failed with exit code {exit_code}")
        
        thread.finished.connect(on_finished)
        thread.start()
    
    def on_project_created(self, project_path: str):
        """Handle new project creation."""
        self._load_projects()
        self.current_project = project_path
        self.actions_widget.setVisible(True)


