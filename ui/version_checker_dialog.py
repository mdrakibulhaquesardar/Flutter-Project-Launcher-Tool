"""Version Checker dialog for Flutter Project Launcher Tool."""
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QTextEdit)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont
from services.flutter_service import FlutterService
from core.logger import Logger
from utils.path_utils import get_flutter_executable
from core.commands import CommandExecutor


class VersionCheckerDialog(QDialog):
    """Dialog for checking Flutter and Dart versions."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.flutter_service = FlutterService()
        self.logger = Logger()
        self._init_ui()
        # Defer loading until dialog is shown
        QTimer.singleShot(0, self._check_versions)
    
    def _init_ui(self):
        """Initialize UI components."""
        self.setWindowTitle("Version Checker")
        self.setMinimumSize(600, 500)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        # Header
        header_label = QLabel("Flutter & Dart Version Information", self)
        header_font = QFont()
        header_font.setBold(True)
        header_font.setPointSize(12)
        header_label.setFont(header_font)
        layout.addWidget(header_label)
        
        # Version display
        self.version_text = QTextEdit(self)
        self.version_text.setReadOnly(True)
        self.version_text.setFontFamily("Consolas")
        self.version_text.setFontPointSize(10)
        layout.addWidget(self.version_text)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        refresh_btn = QPushButton("🔄 Refresh", self)
        refresh_btn.clicked.connect(self._check_versions)
        button_layout.addWidget(refresh_btn)
        
        close_btn = QPushButton("Close", self)
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
    
    def _check_versions(self):
        """Check and display Flutter and Dart versions."""
        self.version_text.clear()
        self.version_text.append("Checking versions...\n")
        
        sdk = self.flutter_service.get_default_sdk()
        if not sdk:
            self.version_text.append("❌ Flutter SDK not found!")
            self.version_text.append("\nPlease configure Flutter SDK in Settings.")
            return
        
        flutter_exe = get_flutter_executable(sdk)
        if not flutter_exe:
            self.version_text.append("❌ Flutter executable not found!")
            return
        
        # Get Flutter version
        output, exit_code = CommandExecutor.run_command([flutter_exe, "--version"])
        
        if exit_code == 0:
            version_info = output.strip()
            self.version_text.append("✅ Flutter Version Information:\n")
            self.version_text.append("=" * 60 + "\n")
            self.version_text.append(version_info)
            self.version_text.append("\n" + "=" * 60 + "\n\n")
            
            # Parse versions
            lines = version_info.split('\n')
            flutter_version = "Unknown"
            dart_version = "Unknown"
            engine_version = "Unknown"
            
            for line in lines:
                if 'Flutter' in line and 'version' in line.lower():
                    # Extract Flutter version
                    import re
                    match = re.search(r'Flutter\s+([\d.]+)', line)
                    if match:
                        flutter_version = match.group(1)
                elif 'Dart' in line and 'version' in line.lower():
                    # Extract Dart version
                    import re
                    match = re.search(r'Dart\s+([\d.]+)', line)
                    if match:
                        dart_version = match.group(1)
                elif 'Engine' in line:
                    # Extract Engine version
                    import re
                    match = re.search(r'Engine\s+([a-f0-9]+)', line)
                    if match:
                        engine_version = match.group(1)
            
            # Display parsed versions
            self.version_text.append("\n📊 Parsed Information:\n")
            self.version_text.append("-" * 60 + "\n")
            self.version_text.append(f"Flutter Version: {flutter_version}\n")
            self.version_text.append(f"Dart Version: {dart_version}\n")
            if engine_version != "Unknown":
                self.version_text.append(f"Engine Version: {engine_version}\n")
            
            # SDK Path
            self.version_text.append("\n📁 SDK Information:\n")
            self.version_text.append("-" * 60 + "\n")
            self.version_text.append(f"Flutter SDK Path: {sdk}\n")
            
        else:
            self.version_text.append("❌ Error checking Flutter version:\n")
            self.version_text.append(output)

