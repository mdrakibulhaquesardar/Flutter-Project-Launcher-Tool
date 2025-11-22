"""Project Details Dialog for Flutter Project Launcher Tool."""
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QTextEdit, QScrollArea, QWidget)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
from services.project_service import ProjectService
from core.logger import Logger


class ProjectDetailsDialog(QDialog):
    """Dialog showing detailed project information."""
    
    def __init__(self, project_path: str, parent=None):
        super().__init__(parent)
        self.project_path = project_path
        self.project_service = ProjectService()
        self.logger = Logger()
        self.setWindowTitle("Project Details")
        self.setMinimumSize(700, 600)
        self._init_ui()
        # Defer loading until dialog is shown
        QTimer.singleShot(0, self._load_project_details)
    
    def _init_ui(self):
        """Initialize UI components."""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        # Title
        title_label = QLabel("Project Details", self)
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # Scroll area for details
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        details_widget = QWidget()
        details_layout = QVBoxLayout(details_widget)
        details_layout.setSpacing(15)
        
        self.details_text = QTextEdit(details_widget)
        self.details_text.setReadOnly(True)
        self.details_text.setFont(QFont("Consolas", 9))
        from core.theme import Theme
        bg_color = Theme.BACKGROUND if Theme.BACKGROUND else "palette(window)"
        self.details_text.setStyleSheet(f"""
            QTextEdit {{
                background-color: {Theme.SURFACE};
                border: 1px solid {Theme.BORDER};
                border-radius: 2px;
                padding: 10px;
                color: {Theme.TEXT_PRIMARY};
            }}
        """)
        details_layout.addWidget(self.details_text)
        
        scroll.setWidget(details_widget)
        layout.addWidget(scroll, 1)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        close_btn = QPushButton("Close", self)
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
    
    def _load_project_details(self):
        """Load and display project details."""
        try:
            # Get project metadata
            metadata = self.project_service.get_project_metadata(self.project_path)
            project_path = Path(self.project_path)
            
            # Build details text
            details = []
            details.append("=" * 70)
            details.append("PROJECT INFORMATION")
            details.append("=" * 70)
            details.append("")
            
            # Basic Information
            details.append("📦 BASIC INFORMATION")
            details.append("-" * 70)
            details.append(f"Project Name:     {metadata.get('name', 'N/A')}")
            details.append(f"Package Name:     {metadata.get('package_name', metadata.get('name', 'N/A'))}")
            details.append(f"Project Path:     {project_path.resolve()}")
            details.append("")
            
            # Flutter SDK Information
            details.append("🔧 FLUTTER SDK INFORMATION")
            details.append("-" * 70)
            flutter_version = metadata.get("flutter_version")
            flutter_constraint = metadata.get("flutter_sdk_constraint")
            fvm_enabled = metadata.get("fvm_enabled", False)
            
            if flutter_version:
                details.append(f"SDK Version:      {flutter_version}")
            elif flutter_constraint:
                details.append(f"SDK Constraint:   {flutter_constraint}")
            else:
                details.append("SDK Version:      Unknown")
            
            if fvm_enabled:
                details.append("FVM Enabled:      Yes")
            else:
                details.append("FVM Enabled:      No")
            details.append("")
            
            # File System Information
            details.append("📁 FILE SYSTEM INFORMATION")
            details.append("-" * 70)
            if project_path.exists():
                stat = project_path.stat()
                details.append(f"Exists:           Yes")
                details.append(f"Size:             {self._format_size(self._get_dir_size(project_path))}")
                
                # Last modified
                if metadata.get("last_modified"):
                    try:
                        dt = datetime.fromisoformat(metadata["last_modified"])
                        details.append(f"Last Modified:    {dt.strftime('%Y-%m-%d %H:%M:%S')}")
                    except:
                        details.append(f"Last Modified:    {datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')}")
                else:
                    details.append(f"Last Modified:    {datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')}")
                
                # Created
                try:
                    details.append(f"Created:          {datetime.fromtimestamp(stat.st_ctime).strftime('%Y-%m-%d %H:%M:%S')}")
                except:
                    pass
            else:
                details.append("Exists:           No")
            details.append("")
            
            # Dependencies
            dependencies = metadata.get("dependencies", {})
            if dependencies:
                details.append("📚 DEPENDENCIES")
                details.append("-" * 70)
                # Show Flutter SDK dependency
                if "flutter" in dependencies:
                    flutter_dep = dependencies["flutter"]
                    if isinstance(flutter_dep, dict) and "sdk" in flutter_dep:
                        details.append(f"Flutter SDK:      {flutter_dep.get('sdk', 'N/A')}")
                
                # Count dependencies
                dep_count = len([k for k in dependencies.keys() if k != "flutter"])
                details.append(f"Total Dependencies: {dep_count}")
                details.append("")
                
                # List top 10 dependencies
                if dep_count > 0:
                    details.append("Top Dependencies:")
                    count = 0
                    for dep_name, dep_version in dependencies.items():
                        if dep_name != "flutter" and count < 10:
                            version_str = dep_version if isinstance(dep_version, str) else str(dep_version)
                            details.append(f"  • {dep_name}: {version_str}")
                            count += 1
                    if dep_count > 10:
                        details.append(f"  ... and {dep_count - 10} more")
                    details.append("")
            
            # Project Structure
            details.append("📂 PROJECT STRUCTURE")
            details.append("-" * 70)
            if project_path.exists():
                lib_dir = project_path / "lib"
                pubspec = project_path / "pubspec.yaml"
                readme = project_path / "README.md"
                
                details.append(f"lib/ directory:    {'✓ Exists' if lib_dir.exists() else '✗ Missing'}")
                details.append(f"pubspec.yaml:     {'✓ Exists' if pubspec.exists() else '✗ Missing'}")
                details.append(f"README.md:        {'✓ Exists' if readme.exists() else '✗ Missing'}")
                
                # Count Dart files
                dart_files = list(project_path.rglob("*.dart"))
                details.append(f"Dart Files:       {len(dart_files)}")
                
                # Count directories
                dirs = [d for d in project_path.iterdir() if d.is_dir() and not d.name.startswith('.')]
                details.append(f"Directories:      {len(dirs)}")
            details.append("")
            
            # Icon Information
            icon_path = metadata.get("icon_path")
            if icon_path:
                details.append("🖼️ ICON INFORMATION")
                details.append("-" * 70)
                details.append(f"Icon Path:        {icon_path}")
                details.append(f"Icon Exists:      {'✓ Yes' if Path(icon_path).exists() else '✗ No'}")
                details.append("")
            
            # Additional Metadata
            details.append("ℹ️ ADDITIONAL INFORMATION")
            details.append("-" * 70)
            details.append(f"Project Type:     Flutter Application")
            details.append(f"Platform:         Cross-platform")
            
            # Check for platform-specific folders
            android_dir = project_path / "android"
            ios_dir = project_path / "ios"
            web_dir = project_path / "web"
            windows_dir = project_path / "windows"
            linux_dir = project_path / "linux"
            macos_dir = project_path / "macos"
            
            platforms = []
            if android_dir.exists():
                platforms.append("Android")
            if ios_dir.exists():
                platforms.append("iOS")
            if web_dir.exists():
                platforms.append("Web")
            if windows_dir.exists():
                platforms.append("Windows")
            if linux_dir.exists():
                platforms.append("Linux")
            if macos_dir.exists():
                platforms.append("macOS")
            
            if platforms:
                details.append(f"Supported Platforms: {', '.join(platforms)}")
            else:
                details.append("Supported Platforms: Unknown")
            
            details.append("")
            details.append("=" * 70)
            
            # Set the text
            self.details_text.setPlainText("\n".join(details))
            
        except Exception as e:
            self.logger.error(f"Error loading project details: {e}", exc_info=True)
            self.details_text.setPlainText(f"Error loading project details:\n{str(e)}")
    
    def _get_dir_size(self, path: Path) -> int:
        """Get total size of directory."""
        total = 0
        try:
            for entry in path.rglob('*'):
                if entry.is_file():
                    try:
                        total += entry.stat().st_size
                    except:
                        pass
        except:
            pass
        return total
    
    def _format_size(self, size_bytes: int) -> str:
        """Format size in human-readable format."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} TB"

