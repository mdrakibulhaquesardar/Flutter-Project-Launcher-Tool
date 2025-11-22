"""SDK Download dialog with progress for Flutter Project Launcher Tool."""
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QProgressBar, QTextEdit)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont
from services.sdk_manager_service import SDKManagerService
from core.logger import Logger


class SDKDownloadThread(QThread):
    """Thread for downloading Flutter SDK."""
    progress = pyqtSignal(int, int)  # downloaded, total
    status = pyqtSignal(str)
    finished = pyqtSignal(bool, str)  # success, message
    
    def __init__(self, sdk_manager: SDKManagerService, version: str, channel: str = "stable", download_url: str = None):
        super().__init__()
        self.sdk_manager = sdk_manager
        self.version = version
        self.channel = channel
        self.download_url = download_url
    
    def run(self):
        """Download SDK."""
        def progress_callback(downloaded: int, total: int):
            self.progress.emit(downloaded, total)
            if total > 0:
                percent = (downloaded / total) * 100
                self.status.emit(f"Downloading: {percent:.1f}% ({downloaded}/{total} bytes)")
        
        self.status.emit(f"Starting download of Flutter {self.version}...")
        success, message = self.sdk_manager.download_sdk(
            self.version, 
            channel=self.channel,
            download_url=self.download_url,
            progress_callback=progress_callback
        )
        self.finished.emit(success, message)


class SDKDownloadDialog(QDialog):
    """Dialog for downloading Flutter SDK with progress."""
    
    download_complete = pyqtSignal(str, str)  # version, zip_path
    
    def __init__(self, version: str, channel: str = "stable", download_url: str = None, parent=None):
        super().__init__(parent)
        self.version = version
        self.channel = channel
        self.download_url = download_url
        self.sdk_manager = SDKManagerService()
        self.logger = Logger()
        self.zip_path = None
        self._init_ui()
        self._start_download()
    
    def _init_ui(self):
        """Initialize UI components."""
        self.setWindowTitle(f"Downloading Flutter {self.version}")
        self.setMinimumSize(500, 300)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # Header
        header_label = QLabel(f"Downloading Flutter SDK {self.version}", self)
        header_font = QFont()
        header_font.setBold(True)
        header_font.setPointSize(12)
        header_label.setFont(header_font)
        layout.addWidget(header_label)
        
        # Status
        self.status_label = QLabel("Preparing download...", self)
        layout.addWidget(self.status_label)
        
        # Progress bar
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setFormat("%p%")
        layout.addWidget(self.progress_bar)
        
        # Log output
        self.log_text = QTextEdit(self)
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(150)
        self.log_text.setFontFamily("Consolas")
        self.log_text.setFontPointSize(8)
        layout.addWidget(self.log_text)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.cancel_btn = QPushButton("Cancel", self)
        self.cancel_btn.clicked.connect(self._cancel_download)
        button_layout.addWidget(self.cancel_btn)
        
        self.close_btn = QPushButton("Close", self)
        self.close_btn.setEnabled(False)
        self.close_btn.clicked.connect(self.accept)
        button_layout.addWidget(self.close_btn)
        
        layout.addLayout(button_layout)
    
    def _start_download(self):
        """Start SDK download."""
        self.thread = SDKDownloadThread(
            self.sdk_manager, 
            self.version, 
            channel=self.channel,
            download_url=self.download_url
        )
        self.thread.progress.connect(self._on_progress)
        self.thread.status.connect(self._on_status)
        self.thread.finished.connect(self._on_download_finished)
        self.thread.start()
    
    def _on_progress(self, downloaded: int, total: int):
        """Handle download progress."""
        if total > 0:
            percent = int((downloaded / total) * 100)
            self.progress_bar.setValue(percent)
    
    def _on_status(self, message: str):
        """Handle status update."""
        self.status_label.setText(message)
        self.log_text.append(message)
    
    def _on_download_finished(self, success: bool, message: str):
        """Handle download completion."""
        if success:
            self.zip_path = message
            self.status_label.setText("Download completed!")
            self.log_text.append("✅ Download completed successfully!")
            self.download_complete.emit(self.version, self.zip_path)
            self.cancel_btn.setEnabled(False)
            self.close_btn.setEnabled(True)
        else:
            self.status_label.setText("Download failed!")
            self.log_text.append(f"❌ Error: {message}")
            self.cancel_btn.setText("Close")
    
    def _cancel_download(self):
        """Cancel download."""
        if hasattr(self, 'thread') and self.thread.isRunning():
            self.thread.terminate()
            self.log_text.append("Download cancelled by user")
        self.reject()

