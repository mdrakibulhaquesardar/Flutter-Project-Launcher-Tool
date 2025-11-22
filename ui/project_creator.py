"""Project creation dialog for Flutter Project Launcher Tool."""
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QComboBox, QFileDialog,
                             QProgressBar, QMessageBox, QPlainTextEdit, QSplitter)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from services.project_service import ProjectService
from services.template_service import TemplateService
from services.flutter_service import FlutterService
from core.logger import Logger
from core.plugin_loader import PluginLoader
from core.commands import FlutterCommandThread
from utils.path_utils import get_flutter_executable
from pathlib import Path
from typing import Optional


class ProjectCreationThread(QThread):
    """Thread for async project creation with real-time output."""
    output = pyqtSignal(str)  # Real-time command output
    error = pyqtSignal(str)   # Error messages
    finished = pyqtSignal(bool, str)  # success, message
    
    def __init__(self, name: str, location: str, template: Optional[str], 
                 architecture: Optional[str] = None,
                 plugin_template: Optional[str] = None, plugin_loader: Optional[PluginLoader] = None):
        super().__init__()
        self.name = name
        self.location = location
        self.template = template
        self.architecture = architecture
        self.plugin_template = plugin_template
        self.plugin_loader = plugin_loader
        self.flutter_service = FlutterService()
        self.command_thread = None
        self.exit_code = 1
    
    def run(self):
        """Execute project creation with real-time output."""
        project_path = Path(self.location) / self.name
        
        if project_path.exists():
            self.error.emit(f"Directory already exists: {project_path}")
            self.finished.emit(False, f"Directory already exists: {project_path}")
            return
        
        # Build flutter create command
        sdk = self.flutter_service.get_default_sdk()
        flutter_exe = get_flutter_executable(sdk)
        
        if not flutter_exe:
            self.error.emit("Flutter SDK not found. Please configure Flutter SDK in settings.")
            self.finished.emit(False, "Flutter SDK not found. Please configure Flutter SDK in settings.")
            return
        
        args = [flutter_exe, "create", self.name]
        if self.template:
            args.extend(["--template", self.template])
            self.output.emit(f"Using Flutter template: {self.template}")
        else:
            self.output.emit("Using default Flutter template (app)")
        
        self.output.emit(f"Running: {' '.join(args)}")
        self.output.emit(f"Working directory: {self.location}")
        self.output.emit("=" * 70)
        
        # Use FlutterCommandThread for real-time output
        self.command_thread = FlutterCommandThread(args, cwd=str(self.location))
        self.command_thread.output.connect(self.output.emit)
        self.command_thread.error.connect(self.error.emit)
        
        # Connect finished signal to store exit code
        self.command_thread.finished.connect(lambda code: setattr(self, 'exit_code', code))
        
        # Wait for command to finish
        self.command_thread.start()
        self.command_thread.wait()
        
        exit_code = self.exit_code
        
        # Show exit code in output
        if exit_code != 0:
            self.output.emit("=" * 70)
            self.output.emit(f"Command exited with code: {exit_code}")
        
        # Check if project was actually created (even if exit code is not 0)
        # Sometimes Flutter returns non-zero but still creates the project
        from utils.file_utils import is_flutter_project
        project_created = is_flutter_project(str(project_path))
        
        if project_created:
            self.output.emit("=" * 70)
            self.output.emit(f"✓ Project created successfully at: {project_path}")
            
            # Add project to database
            from services.project_service import ProjectService
            project_service = ProjectService()
            project_service.add_project(str(project_path))
            
            # If plugin template is selected, apply it
            if self.plugin_template and self.plugin_loader:
                try:
                    self.output.emit(f"\nApplying {self.plugin_template} template...")
                    api = self.plugin_loader.get_api()
                    templates = api.get_registered_templates()
                    
                    if self.plugin_template in templates:
                        template_func = templates[self.plugin_template]
                        template_func(api, str(project_path))
                        self.output.emit(f"✓ Template {self.plugin_template} applied successfully")
                    else:
                        self.output.emit(f"⚠ Warning: Template {self.plugin_template} not found")
                except Exception as e:
                    self.output.emit(f"⚠ Warning: Failed to apply template: {e}")
            
            # If architecture is selected, apply it
            if self.architecture and self.plugin_loader:
                try:
                    self.output.emit("")
                    self.output.emit("=" * 70)
                    self.output.emit(f"Applying architecture: {self.architecture}")
                    self.output.emit("=" * 70)
                    
                    api = self.plugin_loader.get_api()
                    architectures = api.get_registered_architectures()
                    
                    if self.architecture in architectures:
                        arch_func = architectures[self.architecture]
                        self.output.emit(f"Running architecture generator...")
                        
                        # Call architecture generator function
                        arch_func(api, str(project_path))
                        
                        self.output.emit("=" * 70)
                        self.output.emit(f"✓ Architecture '{self.architecture}' applied successfully!")
                        self.output.emit("=" * 70)
                    else:
                        self.output.emit(f"⚠ Warning: Architecture '{self.architecture}' not found in registered architectures")
                        self.output.emit(f"Available architectures: {', '.join(architectures.keys())}")
                except Exception as e:
                    self.output.emit("=" * 70)
                    self.output.emit(f"✗ Error: Failed to apply architecture '{self.architecture}'")
                    self.output.emit(f"Error details: {str(e)}")
                    self.output.emit("=" * 70)
                    import traceback
                    self.output.emit(traceback.format_exc())
            
            # Project was created successfully, even if exit code was not 0
            self.finished.emit(True, str(project_path))
        elif exit_code == 0:
            # Exit code was 0 but project validation failed
            self.error.emit("Project created but validation failed")
            self.finished.emit(False, "Project created but validation failed")
        else:
            # Exit code was not 0 and project was not created
            error_msg = f"Failed to create project (exit code: {exit_code})"
            self.error.emit(error_msg)
            self.finished.emit(False, error_msg)


class ProjectCreator(QDialog):
    """Dialog for creating new Flutter projects."""
    
    project_created = pyqtSignal(str)  # project_path
    
    def __init__(self, parent=None, plugin_loader: Optional[PluginLoader] = None):
        super().__init__(parent)
        self.project_service = ProjectService()
        self.template_service = TemplateService()
        self.logger = Logger()
        self.plugin_loader = plugin_loader
        self._init_ui()
        self._load_templates()
        self._load_plugin_architectures()
    
    def _init_ui(self):
        """Initialize UI components."""
        from core.branding import Branding
        
        self.setWindowTitle("Create New Flutter Project")
        self.setMinimumWidth(600)
        self.setMinimumHeight(600)
        
        # Apply branding icon
        Branding.apply_window_icon(self)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Form section
        form_layout = QVBoxLayout()
        form_layout.setSpacing(15)
        
        # Project name
        name_layout = QVBoxLayout()
        name_layout.setSpacing(5)
        name_label = QLabel("Project Name:", self)
        name_label.setMinimumHeight(20)
        self.name_input = QLineEdit(self)
        self.name_input.setPlaceholderText("my_flutter_app")
        self.name_input.setMinimumHeight(30)
        name_layout.addWidget(name_label)
        name_layout.addWidget(self.name_input)
        form_layout.addLayout(name_layout)
        
        # Project location
        location_layout = QVBoxLayout()
        location_layout.setSpacing(5)
        location_label = QLabel("Project Location:", self)
        location_input_layout = QHBoxLayout()
        self.location_input = QLineEdit(self)
        default_location = str(Path.home() / "flutter_projects")
        self.location_input.setText(default_location)
        browse_btn = QPushButton("Browse...", self)
        browse_btn.clicked.connect(self._browse_location)
        location_input_layout.addWidget(self.location_input)
        location_input_layout.addWidget(browse_btn)
        location_layout.addWidget(location_label)
        location_layout.addLayout(location_input_layout)
        form_layout.addLayout(location_layout)
        
        # Template selection
        template_layout = QVBoxLayout()
        template_layout.setSpacing(5)
        template_label = QLabel("Template:", self)
        self.template_combo = QComboBox(self)
        template_layout.addWidget(template_label)
        template_layout.addWidget(self.template_combo)
        form_layout.addLayout(template_layout)
        
        # Architecture selection (from plugins)
        architecture_layout = QVBoxLayout()
        architecture_layout.setSpacing(5)
        architecture_label = QLabel("Architecture (Optional):", self)
        self.architecture_combo = QComboBox(self)
        self.architecture_combo.addItem("None", None)
        architecture_layout.addWidget(architecture_label)
        architecture_layout.addWidget(self.architecture_combo)
        form_layout.addLayout(architecture_layout)
        
        layout.addLayout(form_layout)
        
        # Output console (hidden initially)
        console_label = QLabel("Output:", self)
        self.output_console = QPlainTextEdit(self)
        self.output_console.setReadOnly(True)
        self.output_console.setMinimumHeight(200)
        self.output_console.setVisible(False)
        from PyQt6.QtGui import QFont
        font = QFont("Consolas", 9)
        self.output_console.setFont(font)
        from core.theme import Theme
        self.output_console.setStyleSheet(Theme.get_console_stylesheet())
        
        console_layout = QVBoxLayout()
        console_layout.setSpacing(5)
        console_layout.addWidget(console_label)
        console_layout.addWidget(self.output_console)
        layout.addLayout(console_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.cancel_btn = QPushButton("Cancel", self)
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)
        
        self.create_btn = QPushButton("Create Project", self)
        self.create_btn.setDefault(True)
        self.create_btn.clicked.connect(self._create_project)
        button_layout.addWidget(self.create_btn)
        
        layout.addLayout(button_layout)
    
    def _load_templates(self):
        """Load available templates."""
        self.template_combo.clear()
        
        # Flutter's built-in templates only
        flutter_builtin_templates = [
            {"id": "app", "name": "App (Default)"},
            {"id": "package", "name": "Package"},
            {"id": "plugin", "name": "Plugin"},
            {"id": "module", "name": "Module"},
            {"id": "skeleton", "name": "Skeleton"},
        ]
        
        # Add all Flutter built-in templates
        for template in flutter_builtin_templates:
            self.template_combo.addItem(template["name"], template["id"])
        
        # Add plugin-registered templates if any
        if self.plugin_loader:
            api = self.plugin_loader.get_api()
            plugin_templates = api.get_registered_templates()
            
            if plugin_templates:
                # Add separator
                self.template_combo.insertSeparator(len(flutter_builtin_templates))
                
                for template_name, template_func in plugin_templates.items():
                    display_name = f"[Plugin] {template_name.replace('_', ' ').title()}"
                    # Use special prefix to identify plugin templates
                    self.template_combo.addItem(display_name, f"plugin:{template_name}")
        
        # Set "App (Default)" as selected by default (index 0)
        self.template_combo.setCurrentIndex(0)
    
    def _load_plugin_architectures(self):
        """Load plugin-registered architectures."""
        # Always start with "None" option
        self.architecture_combo.clear()
        self.architecture_combo.addItem("None", None)
        
        if not self.plugin_loader:
            # Ensure "None" is selected by default
            self.architecture_combo.setCurrentIndex(0)
            return
        
        api = self.plugin_loader.get_api()
        architectures = api.get_registered_architectures()
        
        if architectures:
            # Add separator if there are architectures
            self.architecture_combo.insertSeparator(1)
            
            # Add architectures with better display names
            for arch_name, arch_func in architectures.items():
                # Convert snake_case to Title Case
                display_name = arch_name.replace("_", " ").title()
                self.architecture_combo.addItem(display_name, arch_name)
        
        # Ensure "None" is selected by default (index 0)
        self.architecture_combo.setCurrentIndex(0)
    
    def _browse_location(self):
        """Open folder dialog for project location."""
        location = QFileDialog.getExistingDirectory(
            self, "Select Project Location", self.location_input.text()
        )
        if location:
            self.location_input.setText(location)
    
    def _create_project(self):
        """Create the Flutter project."""
        name = self.name_input.text().strip()
        location = self.location_input.text().strip()
        template_id = self.template_combo.currentData()
        architecture_name = self.architecture_combo.currentData()
        
        # Handle different template types
        flutter_template = None  # Template to pass to Flutter create command
        plugin_template_name = None  # Plugin template to apply after creation
        
        if template_id:
            if isinstance(template_id, str):
                if template_id.startswith("plugin:"):
                    # Plugin template - create project first, then apply template
                    plugin_template_name = template_id.replace("plugin:", "")
                    flutter_template = "app"  # Use app template as base
                else:
                    # Flutter built-in template (app, package, plugin, module, skeleton)
                    flutter_template = template_id
            else:
                # Default case - use app template
                flutter_template = "app"
        else:
            # No template selected - use app (default)
            flutter_template = "app"
        
        # Validation
        if not name:
            QMessageBox.warning(self, "Validation Error", "Project name is required.")
            return
        
        if not location:
            QMessageBox.warning(self, "Validation Error", "Project location is required.")
            return
        
        location_path = Path(location)
        if not location_path.exists():
            try:
                location_path.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Cannot create directory: {e}")
                return
        
        # Disable UI during creation
        self.create_btn.setEnabled(False)
        self.cancel_btn.setEnabled(False)
        
        # Show output console
        self.output_console.clear()
        self.output_console.setVisible(True)
        
        # Create project in thread
        self.creation_thread = ProjectCreationThread(
            name, location, flutter_template, architecture_name, 
            plugin_template_name, self.plugin_loader
        )
        self.creation_thread.output.connect(self._on_output)
        self.creation_thread.error.connect(self._on_error)
        self.creation_thread.finished.connect(self._on_creation_finished)
        self.creation_thread.start()
    
    def _on_output(self, message: str):
        """Handle real-time output."""
        self.output_console.appendPlainText(message)
        # Auto-scroll to bottom
        scrollbar = self.output_console.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        self.logger.info(message)
    
    def _on_error(self, message: str):
        """Handle error messages."""
        self.output_console.appendPlainText(f"ERROR: {message}")
        # Auto-scroll to bottom
        scrollbar = self.output_console.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        self.logger.error(message)
    
    def _on_creation_finished(self, success: bool, message: str):
        """Handle project creation completion."""
        self.create_btn.setEnabled(True)
        self.cancel_btn.setEnabled(True)
        
        if success:
            self.output_console.appendPlainText("\n" + "=" * 70)
            self.output_console.appendPlainText("✓ Project creation completed successfully!")
            # Don't auto-close, let user see the output
            # QMessageBox.information(self, "Success", f"Project created successfully!\n{message}")
            self.project_created.emit(message)
            # Change button to "Close" after success
            self.create_btn.setText("Close")
            self.create_btn.clicked.disconnect()
            self.create_btn.clicked.connect(self.accept)
        else:
            self.output_console.appendPlainText("\n" + "=" * 70)
            self.output_console.appendPlainText(f"✗ Project creation failed!")
            QMessageBox.critical(self, "Error", f"Failed to create project:\n{message}")


