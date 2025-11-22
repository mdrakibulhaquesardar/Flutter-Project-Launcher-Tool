"""Project creation dialog for Flutter Project Launcher Tool."""
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QComboBox, QFileDialog,
                             QProgressBar, QMessageBox)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from services.project_service import ProjectService
from services.template_service import TemplateService
from core.logger import Logger
from core.plugin_loader import PluginLoader
from pathlib import Path
from typing import Optional


class ProjectCreationThread(QThread):
    """Thread for async project creation."""
    progress = pyqtSignal(str)
    finished = pyqtSignal(bool, str)  # success, message
    
    def __init__(self, project_service: ProjectService, name: str, 
                 location: str, template: Optional[str], architecture: Optional[str] = None,
                 plugin_template: Optional[str] = None, plugin_loader: Optional[PluginLoader] = None):
        super().__init__()
        self.project_service = project_service
        self.name = name
        self.location = location
        self.template = template
        self.architecture = architecture
        self.plugin_template = plugin_template
        self.plugin_loader = plugin_loader
    
    def run(self):
        """Execute project creation."""
        self.progress.emit("Creating project...")
        
        # If plugin template is selected, create project first, then apply template
        if self.plugin_template and self.plugin_loader:
            # Create basic Flutter project first
            success, message = self.project_service.create_project(
                self.name, self.location, None  # No template, create basic project
            )
            
            if success:
                try:
                    self.progress.emit(f"Applying {self.plugin_template} template...")
                    api = self.plugin_loader.get_api()
                    templates = api.get_registered_templates()
                    
                    if self.plugin_template in templates:
                        template_func = templates[self.plugin_template]
                        project_path = Path(self.location) / self.name
                        template_func(api, str(project_path))
                        self.progress.emit(f"Template {self.plugin_template} applied successfully")
                    else:
                        self.progress.emit(f"Warning: Template {self.plugin_template} not found")
                except Exception as e:
                    self.progress.emit(f"Warning: Failed to apply template: {e}")
        else:
            # Use regular template or create basic project
            success, message = self.project_service.create_project(
                self.name, self.location, self.template
            )
        
        # If project created successfully and architecture is selected, apply it
        if success and self.architecture and self.plugin_loader:
            try:
                self.progress.emit(f"Applying {self.architecture} architecture...")
                api = self.plugin_loader.get_api()
                architectures = api.get_registered_architectures()
                
                if self.architecture in architectures:
                    arch_func = architectures[self.architecture]
                    project_path = Path(self.location) / self.name
                    arch_func(api, str(project_path))
                    self.progress.emit(f"Architecture {self.architecture} applied successfully")
            except Exception as e:
                self.progress.emit(f"Warning: Failed to apply architecture: {e}")
        
        self.finished.emit(success, message)


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
        self.setWindowTitle("Create New Flutter Project")
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
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
        layout.addLayout(name_layout)
        
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
        layout.addLayout(location_layout)
        
        # Template selection
        template_layout = QVBoxLayout()
        template_layout.setSpacing(5)
        template_label = QLabel("Template:", self)
        self.template_combo = QComboBox(self)
        template_layout.addWidget(template_label)
        template_layout.addWidget(self.template_combo)
        layout.addLayout(template_layout)
        
        # Architecture selection (from plugins)
        architecture_layout = QVBoxLayout()
        architecture_layout.setSpacing(5)
        architecture_label = QLabel("Architecture (Optional):", self)
        self.architecture_combo = QComboBox(self)
        self.architecture_combo.addItem("None", None)
        architecture_layout.addWidget(architecture_label)
        architecture_layout.addWidget(self.architecture_combo)
        layout.addLayout(architecture_layout)
        
        # Progress bar (hidden initially)
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setVisible(False)
        self.progress_bar.setRange(0, 0)  # Indeterminate
        layout.addWidget(self.progress_bar)
        
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
        templates = self.template_service.get_templates()
        self.template_combo.clear()
        
        # Add built-in templates
        for template in templates:
            self.template_combo.addItem(template.get("name", ""), template.get("id"))
        
        # Add plugin-registered templates
        if self.plugin_loader:
            api = self.plugin_loader.get_api()
            plugin_templates = api.get_registered_templates()
            
            if plugin_templates:
                # Add separator if there are plugin templates
                self.template_combo.insertSeparator(len(templates))
                
                for template_name, template_func in plugin_templates.items():
                    display_name = f"[Plugin] {template_name.replace('_', ' ').title()}"
                    # Use special prefix to identify plugin templates
                    self.template_combo.addItem(display_name, f"plugin:{template_name}")
    
    def _load_plugin_architectures(self):
        """Load plugin-registered architectures."""
        if not self.plugin_loader:
            return
        
        api = self.plugin_loader.get_api()
        architectures = api.get_registered_architectures()
        
        for arch_name, arch_func in architectures.items():
            display_name = arch_name.replace("_", " ").title()
            self.architecture_combo.addItem(display_name, arch_name)
    
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
        
        # Check if template is a plugin template
        plugin_template_name = None
        if isinstance(template_id, str) and template_id.startswith("plugin:"):
            plugin_template_name = template_id.replace("plugin:", "")
            template_id = None  # Don't pass to Flutter create command
        
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
        self.progress_bar.setVisible(True)
        
        # Create project in thread
        self.creation_thread = ProjectCreationThread(
            self.project_service, name, location, template_id, architecture_name, 
            plugin_template_name, self.plugin_loader
        )
        self.creation_thread.progress.connect(self._on_progress)
        self.creation_thread.finished.connect(self._on_creation_finished)
        self.creation_thread.start()
    
    def _on_progress(self, message: str):
        """Handle progress updates."""
        self.logger.info(message)
    
    def _on_creation_finished(self, success: bool, message: str):
        """Handle project creation completion."""
        self.progress_bar.setVisible(False)
        self.create_btn.setEnabled(True)
        self.cancel_btn.setEnabled(True)
        
        if success:
            QMessageBox.information(self, "Success", f"Project created successfully!\n{message}")
            self.project_created.emit(message)
            self.accept()
        else:
            QMessageBox.critical(self, "Error", f"Failed to create project:\n{message}")


