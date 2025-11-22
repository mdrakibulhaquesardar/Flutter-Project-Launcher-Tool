"""Dashboard widget for Flutter Project Launcher Tool."""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QScrollArea, QLabel, QMessageBox, QMenu, QProgressBar, QComboBox)
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
from core.settings import Settings
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
        self.settings = Settings()
        self.current_project: Optional[str] = None
        self.load_thread: Optional[ProjectLoadThread] = None
        self.refresh_thread: Optional[ProjectRefreshThread] = None
        self.project_items = []  # Store project items
        self.current_tag_filter: Optional[str] = None  # Current tag filter
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
        
        # Tag filter dropdown
        tag_filter_label = QLabel("Filter by Tag:", self)
        header_layout.addWidget(tag_filter_label)
        
        self.tag_filter_combo = QComboBox(self)
        self.tag_filter_combo.setMinimumWidth(150)
        self.tag_filter_combo.addItem("All Projects", None)
        self.tag_filter_combo.currentIndexChanged.connect(self._on_tag_filter_changed)
        header_layout.addWidget(self.tag_filter_combo)
        
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
        self.projects_scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
        """)
        
        self.projects_widget = QWidget()
        self.projects_layout = QVBoxLayout(self.projects_widget)
        self.projects_layout.setSpacing(12)
        self.projects_layout.setContentsMargins(5, 5, 5, 5)
        self.projects_layout.addStretch()
        
        self.projects_scroll.setWidget(self.projects_widget)
        layout.addWidget(self.projects_scroll, 1)
        
        # Load available tags for filter
        self._load_tag_filter_options()
        
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
        # Ensure UI is initialized
        if not hasattr(self, 'progress_bar') or not hasattr(self, 'loading_label'):
            return
        
        # Clear existing projects
        self._clear_projects_layout()
        
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
        if hasattr(self, 'refresh_btn'):
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
        project_item.build_apk_clicked.connect(self._on_build_apk_from_context)
        project_item.build_bundle_clicked.connect(self._on_build_bundle_from_context)
        project_item.view_details_clicked.connect(self._on_view_details_from_context)
        project_item.open_vscode_clicked.connect(self._on_open_vscode_from_context)
        project_item.open_android_studio_clicked.connect(self._on_open_android_studio_from_context)
        project_item.copy_path_clicked.connect(self._on_copy_path_from_context)
        project_item.manage_tags_clicked.connect(self._on_manage_tags_from_context)
        project_item.remove_from_list_clicked.connect(self._on_remove_from_list_from_context)
        
        self.project_items.append(project_item)
        self._add_project_item_to_layout(project_item)
    
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
    
    def _clear_projects_layout(self):
        """Clear all project items from layout."""
        self.project_items.clear()
        # Clear layout
        while self.projects_layout.count():
            item = self.projects_layout.takeAt(0)
            if item.widget():
                item.widget().setParent(None)
        # Add stretch back
        self.projects_layout.addStretch()
    
    def _add_project_item_to_layout(self, project_item: ProjectItem):
        """Add project item to layout."""
        # Insert before the stretch item (which is at the end)
        self.projects_layout.insertWidget(self.projects_layout.count() - 1, project_item)
    
    def _load_tag_filter_options(self):
        """Load available tags into filter dropdown."""
        self.tag_filter_combo.clear()
        self.tag_filter_combo.addItem("All Projects", None)
        
        tags = self.project_service.get_all_tags()
        if tags:
            self.tag_filter_combo.insertSeparator(1)
            for tag in tags:
                self.tag_filter_combo.addItem(f"#{tag}", tag)
    
    def _on_tag_filter_changed(self, index: int):
        """Handle tag filter selection change."""
        # Prevent triggering during initialization
        if not hasattr(self, 'project_service'):
            return
        
        tag = self.tag_filter_combo.currentData()
        self.current_tag_filter = tag
        
        if tag:
            # Filter projects by tag
            projects = self.project_service.get_projects_by_tag(tag)
            self._display_filtered_projects(projects)
        else:
            # Show all projects - only if UI is fully initialized
            if hasattr(self, 'progress_bar'):
                self._load_projects()
            else:
                # UI not ready yet, just store the filter
                pass
    
    def _display_filtered_projects(self, projects: list):
        """Display filtered projects."""
        self._clear_projects_layout()
        if hasattr(self, 'progress_bar'):
            self.progress_bar.setVisible(False)
        if hasattr(self, 'loading_label'):
            self.loading_label.setVisible(False)
        if hasattr(self, 'refresh_btn'):
            self.refresh_btn.setEnabled(True)
        
        if not projects:
            no_projects = QLabel(f"No projects found with tag '{self.current_tag_filter}'", self)
            no_projects.setAlignment(Qt.AlignmentFlag.AlignCenter)
            from core.theme import Theme
            no_projects.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; padding: 20px;")
            self.projects_layout.insertWidget(0, no_projects)
        else:
            # Add filtered projects
            for project_data in projects:
                project_item = ProjectItem(project_data, self)
                project_item.clicked.connect(self._on_project_selected)
                project_item.run_clicked.connect(self._on_project_run)
                project_item.open_clicked.connect(self._on_project_open)
                project_item.build_apk_clicked.connect(self._on_build_apk_from_context)
                project_item.build_bundle_clicked.connect(self._on_build_bundle_from_context)
                project_item.view_details_clicked.connect(self._on_view_details_from_context)
                project_item.open_vscode_clicked.connect(self._on_open_vscode_from_context)
                project_item.open_android_studio_clicked.connect(self._on_open_android_studio_from_context)
                project_item.copy_path_clicked.connect(self._on_copy_path_from_context)
                project_item.manage_tags_clicked.connect(self._on_manage_tags_from_context)
                project_item.remove_from_list_clicked.connect(self._on_remove_from_list_from_context)
                
                self.project_items.append(project_item)
                self._add_project_item_to_layout(project_item)
        
        self.logger.info(f"Displayed {len(projects)} filtered project(s)")
    
    def _on_projects_loaded_for_refresh(self, projects: list):
        """Handle projects loaded, now refresh versions in parallel."""
        if not projects:
            self._on_projects_loaded(projects)
            return
        
        # Clear existing projects before refreshing
        self._clear_projects_layout()
        
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
        project_item.build_apk_clicked.connect(self._on_build_apk_from_context)
        project_item.build_bundle_clicked.connect(self._on_build_bundle_from_context)
        project_item.view_details_clicked.connect(self._on_view_details_from_context)
        project_item.open_vscode_clicked.connect(self._on_open_vscode_from_context)
        project_item.open_android_studio_clicked.connect(self._on_open_android_studio_from_context)
        project_item.copy_path_clicked.connect(self._on_copy_path_from_context)
        project_item.manage_tags_clicked.connect(self._on_manage_tags_from_context)
        project_item.remove_from_list_clicked.connect(self._on_remove_from_list_from_context)
        
        self.project_items.append(project_item)
        self._add_project_item_to_layout(project_item)
    
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
        self.logger.info(f"Selected project: {project_path}")
    
    def _show_project_details(self):
        """Show project details dialog."""
        if not self.current_project:
            QMessageBox.warning(self, "No Project", "Please select a project first.")
            return
        
        dialog = ProjectDetailsDialog(self.current_project, self)
        dialog.tags_updated.connect(self._on_tags_updated)
        dialog.exec()
    
    def _on_tags_updated(self, project_path: str):
        """Handle tags updated signal from project details dialog."""
        self._load_tag_filter_options()
        # Reload projects based on current filter
        if self.current_tag_filter:
            projects = self.project_service.get_projects_by_tag(self.current_tag_filter)
            self._display_filtered_projects(projects)
        else:
            self._load_projects()
    
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
        
        # Use settings-based editor opening
        self._open_in_editor(path, "code")
    
    def _open_android_studio(self, project_path: Optional[str] = None):
        """Open project in Android Studio."""
        path = project_path or self.current_project
        if not path:
            QMessageBox.warning(self, "No Project", "Please select a project first.")
            return
        
        # Use settings-based editor opening
        self._open_in_editor(path, "studio")
    
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
        self._load_tag_filter_options()  # Refresh tag filter options
        self._load_projects()
        self.current_project = project_path
    
    def _on_build_apk_from_context(self, project_path: str):
        """Handle build APK from context menu."""
        self.current_project = project_path
        self._build_apk()
    
    def _on_build_bundle_from_context(self, project_path: str):
        """Handle build bundle from context menu."""
        self.current_project = project_path
        self._build_bundle()
    
    def _on_view_details_from_context(self, project_path: str):
        """Handle view details from context menu."""
        dialog = ProjectDetailsDialog(project_path, self)
        dialog.tags_updated.connect(self._on_tags_updated)
        dialog.exec()
    
    def _on_open_vscode_from_context(self, project_path: str):
        """Handle open in VS Code from context menu."""
        self._open_in_editor(project_path, "code")
    
    def _on_open_android_studio_from_context(self, project_path: str):
        """Handle open in Android Studio from context menu."""
        self._open_in_editor(project_path, "studio")
    
    def _on_copy_path_from_context(self, project_path: str):
        """Handle copy path from context menu."""
        from PyQt6.QtWidgets import QApplication
        clipboard = QApplication.clipboard()
        clipboard.setText(project_path)
        self.logger.info(f"Copied path to clipboard: {project_path}")
    
    def _on_manage_tags_from_context(self, project_path: str):
        """Handle manage tags from context menu."""
        from ui.project_details_dialog import ProjectDetailsDialog
        dialog = ProjectDetailsDialog(project_path, self)
        dialog.tags_updated.connect(self._on_tags_updated)
        dialog.exec()
    
    def _on_remove_from_list_from_context(self, project_path: str):
        """Handle remove from list from context menu."""
        reply = QMessageBox.question(
            self, "Remove Project",
            f"Remove '{Path(project_path).name}' from the project list?\n\n"
            "This will not delete the project files.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.project_service.remove_project(project_path)
            if self.current_project == project_path:
                self.current_project = None
            self._load_tag_filter_options()  # Refresh tag filter options
            # Reload projects based on current filter
            if self.current_tag_filter:
                projects = self.project_service.get_projects_by_tag(self.current_tag_filter)
                self._display_filtered_projects(projects)
            else:
                self._load_projects()
    
    def _open_in_editor(self, project_path: str, editor: str):
        """Open project in editor (VS Code or Android Studio)."""
        import subprocess
        import os
        
        try:
            if editor == "code":
                # Try VS Code from settings first
                vscode_path = self.settings.get_vscode_path()
                if vscode_path and Path(vscode_path).exists():
                    subprocess.Popen([vscode_path, project_path], shell=False)
                else:
                    # Fallback to command line
                    if os.name == 'nt':  # Windows
                        subprocess.Popen(["code", project_path], shell=False)
                    else:  # Linux/macOS
                        subprocess.Popen(["code", project_path])
            elif editor == "studio":
                # Try Android Studio from settings first
                as_path = self.settings.get_android_studio_path()
                if as_path and Path(as_path).exists():
                    subprocess.Popen([as_path, project_path], shell=False)
                else:
                    # Fallback to common paths
                    if os.name == 'nt':  # Windows
                        studio_paths = [
                            r"C:\Program Files\Android\Android Studio\bin\studio64.exe",
                            os.path.expanduser(r"~\AppData\Local\Programs\Android Studio\bin\studio64.exe")
                        ]
                        found = False
                        for path in studio_paths:
                            if os.path.exists(path):
                                subprocess.Popen([path, project_path])
                                found = True
                                break
                        if not found:
                            QMessageBox.warning(self, "Android Studio Not Found", 
                                              "Android Studio not found. Please configure it in Settings.")
                    else:  # Linux/macOS
                        subprocess.Popen(["studio", project_path])
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not open in {editor}: {e}")


