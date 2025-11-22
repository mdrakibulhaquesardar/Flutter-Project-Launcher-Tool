"""Flutter Upgrade Checker dialog for Flutter Project Launcher Tool."""
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QTextEdit, QMessageBox, QProgressBar)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont
from services.flutter_service import FlutterService
from core.logger import Logger
from utils.path_utils import get_flutter_executable
from core.commands import FlutterCommandThread
import re


class UpgradeCheckThread(QThread):
    """Thread for checking Flutter upgrades."""
    output = pyqtSignal(str)
    finished = pyqtSignal(dict)  # version info
    
    def __init__(self, flutter_exe: str):
        super().__init__()
        self.flutter_exe = flutter_exe
    
    def run(self):
        """Check for Flutter upgrades."""
        try:
            from core.commands import CommandExecutor
            
            # Get current version
            output, exit_code = CommandExecutor.run_command([self.flutter_exe, "--version"])
            current_version = None
            if exit_code == 0:
                match = re.search(r'Flutter\s+([\d.]+)', output)
                if match:
                    current_version = match.group(1)
            
            # Check for upgrades (this is a simplified check)
            # In reality, you'd need to check Flutter's release page or API
            upgrade_output, _ = CommandExecutor.run_command([self.flutter_exe, "upgrade", "--dry-run"])
            
            result = {
                "current_version": current_version,
                "upgrade_available": "upgrade available" in upgrade_output.lower() or "new version" in upgrade_output.lower(),
                "upgrade_output": upgrade_output,
                "version_output": output
            }
            
            self.finished.emit(result)
        except Exception as e:
            self.finished.emit({"error": str(e)})


class UpgradeCheckerDialog(QDialog):
    """Dialog for checking Flutter upgrades."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.flutter_service = FlutterService()
        self.logger = Logger()
        self._init_ui()
        # Defer loading until dialog is shown
        QTimer.singleShot(0, self._check_upgrade)
    
    def _init_ui(self):
        """Initialize UI components."""
        self.setWindowTitle("Flutter Upgrade Checker")
        self.setMinimumSize(700, 500)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # Header
        header_label = QLabel("Flutter Upgrade Checker", self)
        header_font = QFont()
        header_font.setBold(True)
        header_font.setPointSize(12)
        header_label.setFont(header_font)
        layout.addWidget(header_label)
        
        # Version info
        self.version_info_text = QTextEdit(self)
        self.version_info_text.setReadOnly(True)
        self.version_info_text.setFontFamily("Consolas")
        self.version_info_text.setFontPointSize(9)
        layout.addWidget(self.version_info_text)
        
        # Progress bar
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setVisible(False)
        self.progress_bar.setRange(0, 0)
        layout.addWidget(self.progress_bar)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        upgrade_btn = QPushButton("⬆️ Upgrade Flutter", self)
        upgrade_btn.clicked.connect(self._upgrade_flutter)
        button_layout.addWidget(upgrade_btn)
        
        refresh_btn = QPushButton("🔄 Check Again", self)
        refresh_btn.clicked.connect(self._check_upgrade)
        button_layout.addWidget(refresh_btn)
        
        close_btn = QPushButton("Close", self)
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
    
    def _check_upgrade(self):
        """Check for Flutter upgrades."""
        sdk = self.flutter_service.get_default_sdk()
        flutter_exe = get_flutter_executable(sdk)
        
        if not flutter_exe:
            QMessageBox.warning(self, "Error", "Flutter SDK not found!")
            return
        
        self.progress_bar.setVisible(True)
        self.version_info_text.clear()
        self.version_info_text.append("Checking for Flutter upgrades...\n")
        
        self.thread = UpgradeCheckThread(flutter_exe)
        self.thread.output.connect(self.version_info_text.append)
        self.thread.finished.connect(self._on_check_finished)
        self.thread.start()
    
    def _on_check_finished(self, result: dict):
        """Handle upgrade check completion."""
        self.progress_bar.setVisible(False)
        
        if "error" in result:
            self.version_info_text.append(f"\n❌ Error: {result['error']}")
            return
        
        text = "Flutter Version Information\n"
        text += "=" * 60 + "\n\n"
        
        if result.get("current_version"):
            text += f"Current Flutter Version: {result['current_version']}\n\n"
        
        text += "Upgrade Check Results:\n"
        text += "-" * 60 + "\n"
        
        if result.get("upgrade_available"):
            text += "✅ Upgrade Available!\n\n"
            text += "You can upgrade Flutter using the 'Upgrade Flutter' button below.\n"
        else:
            text += "✅ You are using the latest version (or check manually)\n\n"
        
        text += "\nDetailed Output:\n"
        text += "-" * 60 + "\n"
        text += result.get("upgrade_output", "No upgrade information available")
        
        text += "\n\nVersion Details:\n"
        text += "-" * 60 + "\n"
        text += result.get("version_output", "")
        
        self.version_info_text.setPlainText(text)
    
    def _upgrade_flutter(self):
        """Upgrade Flutter SDK."""
        reply = QMessageBox.question(
            self, "Upgrade Flutter",
            "This will run 'flutter upgrade' to update your Flutter SDK.\n\n"
            "This may take several minutes. Continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        sdk = self.flutter_service.get_default_sdk()
        flutter_exe = get_flutter_executable(sdk)
        
        if not flutter_exe:
            QMessageBox.warning(self, "Error", "Flutter SDK not found!")
            return
        
        # Show upgrade dialog with console
        from ui.console_widget import ConsoleWidget
        from PyQt6.QtWidgets import QDialog, QVBoxLayout
        
        upgrade_dialog = QDialog(self)
        upgrade_dialog.setWindowTitle("Upgrading Flutter...")
        upgrade_dialog.setMinimumSize(600, 400)
        
        layout = QVBoxLayout(upgrade_dialog)
        
        info_label = QLabel("Upgrading Flutter SDK. This may take a few minutes...", upgrade_dialog)
        layout.addWidget(info_label)
        
        console = ConsoleWidget(upgrade_dialog)
        console.setVisible(True)
        layout.addWidget(console)
        
        close_btn = QPushButton("Close", upgrade_dialog)
        close_btn.clicked.connect(upgrade_dialog.accept)
        layout.addWidget(close_btn)
        
        # Run upgrade command
        args = [flutter_exe, "upgrade"]
        thread = FlutterCommandThread(args)
        thread.output.connect(console.append)
        thread.error.connect(console.append_error)
        thread.finished.connect(lambda code: console.append_success("Upgrade completed!") if code == 0 else None)
        thread.start()
        
        upgrade_dialog.exec()

