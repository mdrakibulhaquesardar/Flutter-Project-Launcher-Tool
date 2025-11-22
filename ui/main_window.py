"""Main window for Flutter Project Launcher Tool."""
from PyQt6.QtWidgets import (QMainWindow, QMenuBar, QStatusBar, QMessageBox, 
                             QDialog, QVBoxLayout, QTextEdit, QPushButton, QLabel, QHBoxLayout)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont
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
from ui.plugin_manager_dialog import PluginManagerDialog
from core.logger import Logger
from core.settings import Settings
from core.branding import Branding
from core.plugin_loader import PluginLoader
from pathlib import Path
import os


class MainWindow(QMainWindow):
    """Main application window."""
    
    def __init__(self):
        super().__init__()
        self.logger = Logger()
        self.settings = Settings()
        # Initialize plugin loader
        self.plugin_loader = PluginLoader(app_instance=self)
        self._init_ui()
        self._setup_menu()
        self._setup_statusbar()
        self._restore_window_state()
        # Load plugins after UI is ready
        QTimer.singleShot(100, self._load_plugins)
    
    def _init_ui(self):
        """Initialize UI components."""
        from core.theme import Theme
        from core.branding import Branding
        from PyQt6.QtGui import QIcon
        
        self.setWindowTitle(Branding.APP_NAME)
        self.setMinimumSize(900, 700)
        
        # Set window icon
        icon_path = Branding.get_app_icon_path()
        if icon_path and icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))
        
        # Set window background (use system default if BACKGROUND is empty)
        if Theme.BACKGROUND:
            self.setStyleSheet(f"QMainWindow {{ background-color: {Theme.BACKGROUND}; }}")
        
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
        
        # Plugins menu (separate from Tools)
        plugins_menu = menubar.addMenu("Plugins")
        plugins_action = plugins_menu.addAction("Plugin Manager")
        plugins_action.triggered.connect(self._show_plugin_manager)
        plugin_store_action = plugins_menu.addAction("Plugin Store")
        plugin_store_action.triggered.connect(self._show_plugin_store)
        
        # Store menu references for plugin integration
        self.menus = {
            "File": file_menu,
            "Tools": tools_menu,
            "Plugins": plugins_menu,
            "Help": None  # Will be set below
        }
        
        # Help menu
        help_menu = menubar.addMenu("Help")
        self.menus["Help"] = help_menu
        
        getting_started_action = help_menu.addAction("Getting Started")
        getting_started_action.triggered.connect(self._show_getting_started)
        
        documentation_action = help_menu.addAction("Documentation")
        documentation_action.triggered.connect(self._show_documentation)
        
        keyboard_shortcuts_action = help_menu.addAction("Keyboard Shortcuts")
        keyboard_shortcuts_action.triggered.connect(self._show_keyboard_shortcuts)
        
        help_menu.addSeparator()
        
        check_updates_action = help_menu.addAction("Check for Updates")
        check_updates_action.triggered.connect(self._check_for_updates)
        
        view_logs_action = help_menu.addAction("View Logs")
        view_logs_action.triggered.connect(self._show_logs)
        
        help_menu.addSeparator()
        
        contributors_action = help_menu.addAction("Contributors")
        contributors_action.triggered.connect(self._show_contributors)
        
        help_menu.addSeparator()
        
        license_action = help_menu.addAction("License")
        license_action.triggered.connect(self._show_license)
        
        help_menu.addSeparator()
        
        report_issue_action = help_menu.addAction("Report Issue")
        report_issue_action.triggered.connect(self._report_issue)
        
        feedback_action = help_menu.addAction("Send Feedback")
        feedback_action.triggered.connect(self._send_feedback)
        
        help_menu.addSeparator()
        
        about_action = help_menu.addAction("About")
        about_action.triggered.connect(self._show_about)
        
        # Load plugin menu items after menus are set up
        QTimer.singleShot(200, self._load_plugin_menu_items)
    
    def _setup_statusbar(self):
        """Setup status bar."""
        self.statusBar().showMessage("Ready")
    
    def _show_create_project(self):
        """Show project creation dialog."""
        dialog = ProjectCreator(self, plugin_loader=self.plugin_loader)
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
        
        from core.theme import Theme
        if doctor_info.get("exit_code") == 0:
            info_label.setText("Flutter Doctor completed successfully")
            info_label.setStyleSheet(f"color: {Theme.SUCCESS};")
        else:
            info_label.setText("Flutter Doctor found some issues")
            info_label.setStyleSheet(f"color: {Theme.WARNING};")
        
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
    
    def _show_plugin_manager(self):
        """Show plugin manager dialog."""
        dialog = PluginManagerDialog(self, plugin_loader=self.plugin_loader)
        dialog.exec()
    
    def _show_plugin_store(self):
        """Show plugin store dialog."""
        from ui.plugin_store_dialog import PluginStoreDialog
        
        dialog = PluginStoreDialog(self, plugin_loader=self.plugin_loader)
        dialog.exec()
    
    def _load_plugins(self):
        """Load all enabled plugins."""
        if self.plugin_loader:
            count = self.plugin_loader.load_plugins()
            self.logger.info(f"Loaded {count} plugin(s) on startup")
            # Load plugin menu items after plugins are loaded
            self._load_plugin_menu_items()
            self._load_plugin_tool_actions()
    
    def _load_plugin_menu_items(self):
        """Load and add plugin-registered menu items."""
        if not self.plugin_loader:
            return
        
        api = self.plugin_loader.get_api()
        menu_items = api.get_registered_menu_items()
        
        # Track added items to avoid duplicates
        added_items = set()
        
        for item_key, item_data in menu_items.items():
            menu_path = item_data.get("menu_path")
            label = item_data.get("label")
            callback = item_data.get("callback")
            
            # Skip if already added
            item_id = f"{menu_path}/{label}"
            if item_id in added_items:
                continue
            
            if menu_path in self.menus and self.menus[menu_path]:
                menu = self.menus[menu_path]
                # Check if action already exists
                existing_action = None
                for action in menu.actions():
                    if action.text() == label and action.isSeparator() == False:
                        existing_action = action
                        break
                
                if not existing_action:
                    action = menu.addAction(label)
                    action.triggered.connect(lambda checked, cb=callback: self._execute_plugin_callback(cb))
                    self.logger.info(f"Added plugin menu item: {menu_path}/{label}")
                    added_items.add(item_id)
    
    def _load_plugin_tool_actions(self):
        """Load and add plugin-registered tool actions to Tools menu."""
        if not self.plugin_loader:
            return
        
        api = self.plugin_loader.get_api()
        tool_actions = api.get_registered_tool_actions()
        
        tools_menu = self.menus.get("Tools")
        if not tools_menu:
            return
        
        # Remove existing Plugin Actions submenu if it exists
        for action in tools_menu.actions():
            if action.menu() and action.menu().title() == "Plugin Actions":
                tools_menu.removeAction(action)
                break
        
        if not tool_actions:
            return
        
        # Add separator and plugin actions submenu
        tools_menu.addSeparator()
        plugin_actions_menu = tools_menu.addMenu("Plugin Actions")
        
        for action_name, action_data in tool_actions.items():
            callback = action_data.get("callback")
            action = plugin_actions_menu.addAction(action_name)
            action.triggered.connect(lambda checked, cb=callback: self._execute_plugin_callback(cb))
            self.logger.info(f"Added plugin tool action: {action_name}")
    
    def _execute_plugin_callback(self, callback):
        """Execute a plugin callback safely."""
        try:
            if self.plugin_loader:
                api = self.plugin_loader.get_api()
                callback(api)
        except Exception as e:
            self.logger.error(f"Error executing plugin callback: {e}", exc_info=True)
            QMessageBox.critical(
                self,
                "Plugin Error",
                f"An error occurred while executing plugin action:\n{str(e)}"
            )
    
    def _show_getting_started(self):
        """Show getting started guide."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Getting Started")
        dialog.setMinimumSize(600, 500)
        
        layout = QVBoxLayout(dialog)
        
        text = QTextEdit(dialog)
        text.setReadOnly(True)
        text.setFont(QFont("Consolas", 9))
        
        content = """
═══════════════════════════════════════════════════════════════
                    FLUTTER PROJECT LAUNCHER TOOL
                         Getting Started Guide
═══════════════════════════════════════════════════════════════

📦 CREATING A NEW PROJECT
───────────────────────────────────────────────────────────────
1. Click "File" → "New Project" or press Ctrl+N
2. Enter project name and location
3. Select template (optional)
4. Choose architecture (optional)
5. Click "Create"

🔍 SCANNING FOR PROJECTS
───────────────────────────────────────────────────────────────
1. Click "Tools" → "Scan for Projects"
2. Select directory to scan
3. Projects will be automatically added to the list

🏃 RUNNING A PROJECT
───────────────────────────────────────────────────────────────
1. Select a project from the list
2. Click "▶ Run" button or use Quick Actions → "🏃 Run"
3. Select device if multiple devices are available
4. Project will run on selected device

📦 BUILDING APK/BUNDLE
───────────────────────────────────────────────────────────────
1. Select a project
2. Click "📦 Build APK" or "🎁 Build Bundle"
3. Wait for build to complete
4. Output will be in build/app/outputs/

🔧 MANAGING FLUTTER SDKs
───────────────────────────────────────────────────────────────
1. Click "Tools" → "SDK Manager"
2. Browse available SDK versions
3. Download and install SDKs
4. Switch between SDKs
5. Manage PATH settings

🔌 USING PLUGINS
───────────────────────────────────────────────────────────────
1. Click "Plugins" → "Plugin Store"
2. Browse available plugins
3. Install plugins from GitHub
4. Enable/disable plugins in Plugin Manager

⚙️ CONFIGURATION
───────────────────────────────────────────────────────────────
1. Click "Tools" → "Settings" or press Ctrl+,
2. Configure Flutter SDK paths
3. Set scan directories
4. Adjust other preferences

💡 TIPS
───────────────────────────────────────────────────────────────
• Use Refresh button to update SDK versions
• Check Flutter Doctor for environment issues
• Use Environment Info to verify setup
• View project details for full information

═══════════════════════════════════════════════════════════════
        """
        
        text.setPlainText(content)
        layout.addWidget(text)
        
        close_btn = QPushButton("Close", dialog)
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)
        
        dialog.exec()
    
    def _show_documentation(self):
        """Show documentation."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Documentation")
        dialog.setMinimumSize(700, 600)
        
        layout = QVBoxLayout(dialog)
        
        text = QTextEdit(dialog)
        text.setReadOnly(True)
        text.setFont(QFont("Consolas", 9))
        
        content = """
═══════════════════════════════════════════════════════════════
                         DOCUMENTATION
═══════════════════════════════════════════════════════════════

📚 FEATURES OVERVIEW
───────────────────────────────────────────────────────────────

• Project Management
  - Create new Flutter projects
  - Scan and discover existing projects
  - Quick access to recent projects
  - Project details and metadata

• SDK Management
  - Download Flutter SDKs from GitHub
  - Install and manage multiple SDK versions
  - Switch between SDK versions
  - Automatic PATH management

• Build & Run
  - Run projects on connected devices
  - Build APK and App Bundle
  - Device selection dialog
  - Real-time console output

• Tools & Utilities
  - Flutter Doctor integration
  - Environment information
  - Version checker
  - Dependency analyzer
  - Emulator manager
  - Pub cache management

• Plugin System
  - Extensible plugin architecture
  - Plugin store (GitHub integration)
  - Architecture generators
  - Template plugins
  - Custom tool actions

🔧 KEYBOARD SHORTCUTS
───────────────────────────────────────────────────────────────

Ctrl+N          New Project
Ctrl+,          Settings
Ctrl+Q          Exit
F5              Refresh Projects

📖 PLUGIN DEVELOPMENT
───────────────────────────────────────────────────────────────

See PLUGIN_DEVELOPMENT.md for:
• Plugin structure
• Plugin API reference
• Creating custom plugins
• Plugin examples

🌐 RESOURCES
───────────────────────────────────────────────────────────────

GitHub Repository:
https://github.com/mdrakibulhaquesardar/Flutter-Project-Launcher-Tool

Flutter Official:
https://flutter.dev

═══════════════════════════════════════════════════════════════
        """
        
        text.setPlainText(content)
        layout.addWidget(text)
        
        close_btn = QPushButton("Close", dialog)
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)
        
        dialog.exec()
    
    def _show_keyboard_shortcuts(self):
        """Show keyboard shortcuts."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Keyboard Shortcuts")
        dialog.setMinimumSize(500, 400)
        
        layout = QVBoxLayout(dialog)
        
        text = QTextEdit(dialog)
        text.setReadOnly(True)
        text.setFont(QFont("Consolas", 10))
        
        content = """
═══════════════════════════════════════════════════════════════
                      KEYBOARD SHORTCUTS
═══════════════════════════════════════════════════════════════

FILE MENU
───────────────────────────────────────────────────────────────
Ctrl+N          New Project
Ctrl+Q          Exit

TOOLS MENU
───────────────────────────────────────────────────────────────
Ctrl+,          Settings

GENERAL
───────────────────────────────────────────────────────────────
F5              Refresh Projects
Esc             Close Dialog/Window

═══════════════════════════════════════════════════════════════
        """
        
        text.setPlainText(content)
        layout.addWidget(text)
        
        close_btn = QPushButton("Close", dialog)
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)
        
        dialog.exec()
    
    def _check_for_updates(self):
        """Check for application updates."""
        QMessageBox.information(
            self, "Check for Updates",
            "Update checking feature coming soon!\n\n"
            "For now, please check:\n"
            "https://github.com/mdrakibulhaquesardar/Flutter-Project-Launcher-Tool/releases"
        )
    
    def _show_logs(self):
        """Show application logs."""
        from pathlib import Path
        import os
        
        log_file = Path.home() / ".flutter_launcher" / "logs" / "app.log"
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Application Logs")
        dialog.setMinimumSize(800, 600)
        
        layout = QVBoxLayout(dialog)
        
        text = QTextEdit(dialog)
        text.setReadOnly(True)
        text.setFont(QFont("Consolas", 9))
        
        if log_file.exists():
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Show last 1000 lines
                    lines = content.split('\n')
                    if len(lines) > 1000:
                        content = '\n'.join(lines[-1000:])
                    text.setPlainText(content)
            except Exception as e:
                text.setPlainText(f"Error reading log file: {e}")
        else:
            text.setPlainText("No log file found.\n\nLog file location:\n" + str(log_file))
        
        layout.addWidget(text)
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        open_folder_btn = QPushButton("Open Log Folder", dialog)
        open_folder_btn.clicked.connect(lambda: self._open_log_folder())
        button_layout.addWidget(open_folder_btn)
        
        close_btn = QPushButton("Close", dialog)
        close_btn.clicked.connect(dialog.accept)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        
        dialog.exec()
    
    def _open_log_folder(self):
        """Open log folder in file explorer."""
        from pathlib import Path
        import os
        
        log_folder = Path.home() / ".flutter_launcher" / "logs"
        log_folder.mkdir(parents=True, exist_ok=True)
        
        try:
            if os.name == 'nt':
                os.startfile(str(log_folder))
            elif os.name == 'posix':
                import subprocess
                subprocess.Popen(["xdg-open", str(log_folder)])
            elif os.name == 'darwin':
                import subprocess
                subprocess.Popen(["open", str(log_folder)])
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not open log folder: {e}")
    
    def _report_issue(self):
        """Open GitHub issues page."""
        import webbrowser
        try:
            webbrowser.open("https://github.com/mdrakibulhaquesardar/Flutter-Project-Launcher-Tool/issues/new")
        except Exception as e:
            QMessageBox.information(
                self, "Report Issue",
                "Please visit:\n\n"
                "https://github.com/mdrakibulhaquesardar/Flutter-Project-Launcher-Tool/issues/new\n\n"
                f"Error opening browser: {e}"
            )
    
    def _show_contributors(self):
        """Show contributors dialog."""
        from ui.contributors_dialog import ContributorsDialog
        dialog = ContributorsDialog(self)
        dialog.exec()
    
    def _show_license(self):
        """Show license dialog."""
        from ui.license_dialog import LicenseDialog
        dialog = LicenseDialog(self)
        dialog.exec()
    
    def _send_feedback(self):
        """Send feedback."""
        QMessageBox.information(
            self, "Send Feedback",
            "Thank you for your interest!\n\n"
            "You can provide feedback by:\n"
            "• Opening an issue on GitHub\n"
            "• Creating a discussion\n"
            "• Contributing to the project\n\n"
            "GitHub: https://github.com/mdrakibulhaquesardar/Flutter-Project-Launcher-Tool"
        )
    
    def _show_about(self):
        """Show about dialog."""
        from core.branding import Branding
        from PyQt6.QtGui import QPixmap
        
        about_msg = QMessageBox(self)
        about_msg.setWindowTitle(f"About {Branding.APP_NAME}")
        about_msg.setTextFormat(Qt.TextFormat.RichText)
        about_msg.setText(Branding.get_about_text())
        
        # Set icon if available
        icon_path = Branding.get_app_icon_path()
        if icon_path and icon_path.exists():
            pixmap = QPixmap(str(icon_path))
            if not pixmap.isNull():
                about_msg.setIconPixmap(pixmap.scaled(64, 64, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        
        about_msg.exec()
    
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


