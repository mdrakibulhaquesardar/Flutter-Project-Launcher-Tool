"""Emulator Manager dialog for Flutter Project Launcher Tool."""
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QListWidget, QListWidgetItem, QMessageBox,
                             QComboBox, QTextEdit)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont
from services.device_service import DeviceService
from core.logger import Logger
import subprocess
import os


class EmulatorManagerDialog(QDialog):
    """Dialog for managing Android/iOS emulators."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.device_service = DeviceService()
        self.logger = Logger()
        self._init_ui()
        # Defer loading until dialog is shown
        QTimer.singleShot(0, self._load_emulators)
    
    def _init_ui(self):
        """Initialize UI components."""
        self.setWindowTitle("Emulator Manager")
        self.setMinimumSize(700, 500)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        # Header
        header_label = QLabel("Emulator Manager", self)
        header_font = QFont()
        header_font.setBold(True)
        header_font.setPointSize(12)
        header_label.setFont(header_font)
        layout.addWidget(header_label)
        
        # Filter
        filter_layout = QHBoxLayout()
        filter_label = QLabel("Platform:", self)
        self.platform_filter = QComboBox(self)
        self.platform_filter.addItems(["All", "Android", "iOS"])
        self.platform_filter.currentTextChanged.connect(self._load_emulators)
        filter_layout.addWidget(filter_label)
        filter_layout.addWidget(self.platform_filter)
        filter_layout.addStretch()
        layout.addLayout(filter_layout)
        
        # Emulator list
        self.emulator_list = QListWidget(self)
        self.emulator_list.itemDoubleClicked.connect(self._on_emulator_double_clicked)
        layout.addWidget(self.emulator_list)
        
        # Info text
        self.info_text = QTextEdit(self)
        self.info_text.setReadOnly(True)
        self.info_text.setMaximumHeight(100)
        self.info_text.setFontFamily("Consolas")
        self.info_text.setFontPointSize(8)
        layout.addWidget(self.info_text)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        launch_btn = QPushButton("🚀 Launch", self)
        launch_btn.clicked.connect(self._launch_emulator)
        button_layout.addWidget(launch_btn)
        
        refresh_btn = QPushButton("🔄 Refresh", self)
        refresh_btn.clicked.connect(self._load_emulators)
        button_layout.addWidget(refresh_btn)
        
        button_layout.addStretch()
        
        close_btn = QPushButton("Close", self)
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
    
    def _load_emulators(self):
        """Load and display emulators."""
        self.emulator_list.clear()
        self.info_text.clear()
        
        try:
            # Get all devices
            devices = self.device_service.get_connected_devices()
            
            # Filter by platform
            platform_filter = self.platform_filter.currentText()
            if platform_filter == "Android":
                devices = [d for d in devices if d.get("type") == "emulator" and "android" in d.get("name", "").lower()]
            elif platform_filter == "iOS":
                devices = [d for d in devices if d.get("type") == "emulator" and ("ios" in d.get("name", "").lower() or "simulator" in d.get("name", "").lower())]
            else:
                devices = [d for d in devices if d.get("type") == "emulator"]
            
            if not devices:
                no_emulators_item = QListWidgetItem("No emulators found")
                no_emulators_item.setFlags(Qt.ItemFlag.NoItemFlags)
                self.emulator_list.addItem(no_emulators_item)
                self.info_text.append("No emulators detected.\n")
                self.info_text.append("For Android: Use Android Studio AVD Manager to create emulators.\n")
                self.info_text.append("For iOS: Use Xcode Simulator.")
                return
            
            for device in devices:
                device_id = device.get("id", "")
                device_name = device.get("name", "Unknown Emulator")
                device_status = device.get("status", "unknown")
                
                display_text = f"📱 {device_name}"
                if device_status == "available":
                    display_text += " (Running)"
                else:
                    display_text += " (Stopped)"
                
                item = QListWidgetItem(display_text)
                item.setData(Qt.ItemDataRole.UserRole, device_id)
                item.setData(Qt.ItemDataRole.UserRole + 1, device_name)
                
                if device_status == "available":
                    item.setForeground(Qt.GlobalColor.green)
                else:
                    item.setForeground(Qt.GlobalColor.gray)
                
                self.emulator_list.addItem(item)
            
            self.info_text.append(f"Found {len(devices)} emulator(s).\n")
            self.info_text.append("Double-click or select and click 'Launch' to start an emulator.")
            
        except Exception as e:
            self.logger.error(f"Error loading emulators: {e}")
            QMessageBox.warning(self, "Error", f"Could not load emulators:\n{e}")
    
    def _on_emulator_double_clicked(self, item: QListWidgetItem):
        """Handle double-click on emulator."""
        self._launch_emulator()
    
    def _launch_emulator(self):
        """Launch selected emulator."""
        current_item = self.emulator_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "No Selection", "Please select an emulator to launch.")
            return
        
        device_id = current_item.data(Qt.ItemDataRole.UserRole)
        device_name = current_item.data(Qt.ItemDataRole.UserRole + 1)
        
        if not device_id:
            return
        
        # Check if already running
        device = self.device_service.get_device_by_id(device_id)
        if device and device.get("status") == "available":
            QMessageBox.information(self, "Already Running", f"{device_name} is already running.")
            return
        
        # Try to launch emulator
        # For Android, we need to use emulator command
        if "android" in device_name.lower() or "emulator" in device_name.lower():
            self._launch_android_emulator(device_id, device_name)
        else:
            QMessageBox.information(
                self, 
                "Launch Emulator", 
                f"To launch {device_name}, please use:\n"
                f"• Android Studio AVD Manager (for Android)\n"
                f"• Xcode Simulator (for iOS)"
            )
    
    def _launch_android_emulator(self, device_id: str, device_name: str):
        """Launch Android emulator."""
        # Try to find emulator executable
        android_home = os.environ.get("ANDROID_HOME") or os.environ.get("ANDROID_SDK_ROOT")
        
        if not android_home:
            QMessageBox.warning(
                self, 
                "Android SDK Not Found",
                "ANDROID_HOME or ANDROID_SDK_ROOT not set.\n"
                "Please configure Android SDK in your environment."
            )
            return
        
        emulator_exe = os.path.join(android_home, "emulator", "emulator.exe" if os.name == 'nt' else "emulator")
        
        if not os.path.exists(emulator_exe):
            QMessageBox.warning(
                self,
                "Emulator Not Found",
                f"Emulator executable not found at:\n{emulator_exe}\n\n"
                "Please use Android Studio AVD Manager to launch emulators."
            )
            return
        
        try:
            # Launch emulator
            subprocess.Popen([emulator_exe, "-avd", device_id], shell=False)
            QMessageBox.information(self, "Launching", f"Launching {device_name}...\nThis may take a moment.")
            self._load_emulators()  # Refresh list
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not launch emulator:\n{e}")

