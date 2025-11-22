"""Pub Cache management dialog for Flutter Project Launcher Tool."""
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QTextEdit, QMessageBox, QProgressBar)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont
from services.flutter_service import FlutterService
from core.logger import Logger
from utils.path_utils import get_flutter_executable
from core.commands import FlutterCommandThread
import os
from pathlib import Path


class CacheOperationThread(QThread):
    """Thread for cache operations."""
    output = pyqtSignal(str)
    finished = pyqtSignal(bool, str)  # success, message
    
    def __init__(self, flutter_exe: str, operation: str):
        super().__init__()
        self.flutter_exe = flutter_exe
        self.operation = operation  # 'repair' or 'clean'
    
    def run(self):
        """Execute cache operation."""
        try:
            if self.operation == 'repair':
                from core.commands import CommandExecutor
                output, exit_code = CommandExecutor.run_command(
                    [self.flutter_exe, "pub", "cache", "repair"]
                )
                if exit_code == 0:
                    self.finished.emit(True, "Cache repaired successfully!")
                else:
                    self.finished.emit(False, f"Error: {output}")
            elif self.operation == 'clean':
                # Clear pub cache directory
                pub_cache = os.environ.get("PUB_CACHE")
                if not pub_cache:
                    pub_cache = str(Path.home() / ".pub-cache")
                
                cache_path = Path(pub_cache)
                if cache_path.exists():
                    import shutil
                    try:
                        # Calculate size before deletion
                        total_size = sum(f.stat().st_size for f in cache_path.rglob('*') if f.is_file())
                        size_mb = total_size / (1024 * 1024)
                        
                        # Delete cache
                        shutil.rmtree(cache_path)
                        cache_path.mkdir(parents=True, exist_ok=True)
                        
                        self.finished.emit(True, f"Cache cleared successfully! (Freed {size_mb:.2f} MB)")
                    except Exception as e:
                        self.finished.emit(False, f"Error clearing cache: {e}")
                else:
                    self.finished.emit(False, "Pub cache directory not found")
        except Exception as e:
            self.finished.emit(False, str(e))


class PubCacheDialog(QDialog):
    """Dialog for managing Flutter pub cache."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.flutter_service = FlutterService()
        self.logger = Logger()
        self._init_ui()
        # Defer loading until dialog is shown
        QTimer.singleShot(0, self._load_cache_info)
    
    def _init_ui(self):
        """Initialize UI components."""
        self.setWindowTitle("Pub Cache Management")
        self.setMinimumSize(600, 500)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # Header
        header_label = QLabel("Flutter Pub Cache Management", self)
        header_font = QFont()
        header_font.setBold(True)
        header_font.setPointSize(12)
        header_label.setFont(header_font)
        layout.addWidget(header_label)
        
        # Cache info
        self.cache_info_text = QTextEdit(self)
        self.cache_info_text.setReadOnly(True)
        self.cache_info_text.setFontFamily("Consolas")
        self.cache_info_text.setFontPointSize(9)
        self.cache_info_text.setMaximumHeight(150)
        layout.addWidget(self.cache_info_text)
        
        # Progress bar
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setVisible(False)
        self.progress_bar.setRange(0, 0)
        layout.addWidget(self.progress_bar)
        
        # Operation buttons
        button_layout = QVBoxLayout()
        button_layout.setSpacing(10)
        
        repair_btn = QPushButton("🔧 Repair Cache", self)
        repair_btn.clicked.connect(self._repair_cache)
        button_layout.addWidget(repair_btn)
        
        clean_btn = QPushButton("🗑️ Clear Cache", self)
        clean_btn.clicked.connect(self._clear_cache)
        button_layout.addWidget(clean_btn)
        
        refresh_btn = QPushButton("🔄 Refresh Info", self)
        refresh_btn.clicked.connect(self._load_cache_info)
        button_layout.addWidget(refresh_btn)
        
        layout.addLayout(button_layout)
        layout.addStretch()
        
        # Close button
        close_layout = QHBoxLayout()
        close_layout.addStretch()
        
        close_btn = QPushButton("Close", self)
        close_btn.clicked.connect(self.accept)
        close_layout.addWidget(close_btn)
        
        layout.addLayout(close_layout)
    
    def _load_cache_info(self):
        """Load and display cache information."""
        pub_cache = os.environ.get("PUB_CACHE")
        if not pub_cache:
            pub_cache = str(Path.home() / ".pub-cache")
        
        cache_path = Path(pub_cache)
        
        info_text = "Pub Cache Information\n"
        info_text += "=" * 50 + "\n\n"
        info_text += f"Cache Location: {pub_cache}\n"
        
        if cache_path.exists():
            # Calculate cache size
            total_size = 0
            file_count = 0
            try:
                for file_path in cache_path.rglob('*'):
                    if file_path.is_file():
                        total_size += file_path.stat().st_size
                        file_count += 1
            except Exception:
                pass
            
            size_mb = total_size / (1024 * 1024)
            size_gb = size_mb / 1024
            
            info_text += f"Cache Exists: Yes\n"
            info_text += f"Total Files: {file_count:,}\n"
            if size_gb >= 1:
                info_text += f"Cache Size: {size_gb:.2f} GB ({size_mb:.2f} MB)\n"
            else:
                info_text += f"Cache Size: {size_mb:.2f} MB\n"
        else:
            info_text += f"Cache Exists: No\n"
        
        self.cache_info_text.setPlainText(info_text)
    
    def _repair_cache(self):
        """Repair pub cache."""
        reply = QMessageBox.question(
            self, "Repair Cache",
            "This will repair the Flutter pub cache. Continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        sdk = self.flutter_service.get_default_sdk()
        flutter_exe = get_flutter_executable(sdk)
        
        if not flutter_exe:
            QMessageBox.warning(self, "Error", "Flutter SDK not found!")
            return
        
        self.progress_bar.setVisible(True)
        self.cache_info_text.append("\nRepairing cache...")
        
        self.thread = CacheOperationThread(flutter_exe, 'repair')
        self.thread.output.connect(self.cache_info_text.append)
        self.thread.finished.connect(self._on_operation_finished)
        self.thread.start()
    
    def _clear_cache(self):
        """Clear pub cache."""
        reply = QMessageBox.question(
            self, "Clear Cache",
            "This will delete all cached packages. This cannot be undone!\n\n"
            "You will need to download packages again when building projects.\n\n"
            "Continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        sdk = self.flutter_service.get_default_sdk()
        flutter_exe = get_flutter_executable(sdk)
        
        if not flutter_exe:
            QMessageBox.warning(self, "Error", "Flutter SDK not found!")
            return
        
        self.progress_bar.setVisible(True)
        self.cache_info_text.append("\nClearing cache...")
        
        self.thread = CacheOperationThread(flutter_exe, 'clean')
        self.thread.output.connect(self.cache_info_text.append)
        self.thread.finished.connect(self._on_operation_finished)
        self.thread.start()
    
    def _on_operation_finished(self, success: bool, message: str):
        """Handle cache operation completion."""
        self.progress_bar.setVisible(False)
        
        if success:
            QMessageBox.information(self, "Success", message)
            self._load_cache_info()
        else:
            QMessageBox.warning(self, "Error", message)

