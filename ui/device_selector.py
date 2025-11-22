"""Device selection dialog for Flutter Project Launcher Tool."""
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QListWidget, QListWidgetItem, QMessageBox)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QIcon
from services.device_service import DeviceService
from core.logger import Logger
from typing import Optional, Dict


class DeviceSelector(QDialog):
    """Dialog for selecting a device to run Flutter app on."""
    
    device_selected = pyqtSignal(str)  # device_id
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.device_service = DeviceService()
        self.logger = Logger()
        self.selected_device_id: Optional[str] = None
        self._init_ui()
        self._load_devices()
    
    def _init_ui(self):
        """Initialize UI components."""
        self.setWindowTitle("Select Device")
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # Header
        header_label = QLabel("Select a device to run your app:", self)
        header_font = QFont()
        header_font.setBold(True)
        header_font.setPointSize(12)
        header_label.setFont(header_font)
        layout.addWidget(header_label)
        
        # Device list
        self.device_list = QListWidget(self)
        self.device_list.itemDoubleClicked.connect(self._on_device_double_clicked)
        self.device_list.itemSelectionChanged.connect(self._on_selection_changed)
        layout.addWidget(self.device_list)
        
        # Info label
        self.info_label = QLabel("", self)
        from core.theme import Theme
        self.info_label.setStyleSheet(f"color: {Theme.TEXT_MUTED}; font-size: 9pt;")
        self.info_label.setWordWrap(True)
        layout.addWidget(self.info_label)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.refresh_btn = QPushButton("🔄 Refresh", self)
        self.refresh_btn.clicked.connect(self._load_devices)
        button_layout.addWidget(self.refresh_btn)
        
        self.cancel_btn = QPushButton("Cancel", self)
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)
        
        self.select_btn = QPushButton("Select", self)
        self.select_btn.setDefault(True)
        self.select_btn.setEnabled(False)
        self.select_btn.clicked.connect(self._on_select)
        button_layout.addWidget(self.select_btn)
        
        layout.addLayout(button_layout)
    
    def _load_devices(self):
        """Load and display available devices."""
        self.device_list.clear()
        self.info_label.setText("Loading devices...")
        
        try:
            devices = self.device_service.get_available_devices()
            
            if not devices:
                # Try to get all devices (including busy ones)
                devices = self.device_service.get_connected_devices()
            
            if not devices:
                no_devices_item = QListWidgetItem("No devices found")
                no_devices_item.setFlags(Qt.ItemFlag.NoItemFlags)
                self.device_list.addItem(no_devices_item)
                self.info_label.setText(
                    "No devices detected. Please:\n"
                    "• Connect a physical device via USB\n"
                    "• Start an emulator\n"
                    "• Run 'flutter devices' in terminal to verify"
                )
                return
            
            for device in devices:
                device_id = device.get("id", "")
                device_name = device.get("name", "Unknown Device")
                device_type = device.get("type", "unknown")
                device_status = device.get("status", "available")
                
                # Create display text
                display_text = f"{device_name}"
                if device_type != "unknown":
                    display_text += f" ({device_type})"
                if device_status != "available":
                    display_text += f" - {device_status}"
                
                item = QListWidgetItem(display_text)
                item.setData(Qt.ItemDataRole.UserRole, device_id)
                
                # Add icon based on device type
                if device_type == "emulator":
                    item.setText(f"📱 {display_text}")
                elif device_type == "android":
                    item.setText(f"🤖 {display_text}")
                elif device_type == "ios":
                    item.setText(f"🍎 {display_text}")
                elif device_type == "web":
                    item.setText(f"🌐 {display_text}")
                elif device_type == "desktop":
                    item.setText(f"💻 {display_text}")
                else:
                    item.setText(f"📱 {display_text}")
                
                # Disable if not available
                if device_status != "available":
                    item.setFlags(Qt.ItemFlag.NoItemFlags)
                    item.setForeground(Qt.GlobalColor.gray)
                
                self.device_list.addItem(item)
            
            if devices:
                self.info_label.setText(f"Found {len(devices)} device(s). Double-click to select quickly.")
            
        except Exception as e:
            self.logger.error(f"Error loading devices: {e}")
            QMessageBox.warning(self, "Error", f"Could not load devices:\n{e}")
            self.info_label.setText("Error loading devices. Please check Flutter installation.")
    
    def _on_selection_changed(self):
        """Handle device selection change."""
        current_item = self.device_list.currentItem()
        if current_item and current_item.data(Qt.ItemDataRole.UserRole):
            self.select_btn.setEnabled(True)
            device_id = current_item.data(Qt.ItemDataRole.UserRole)
            device = self.device_service.get_device_by_id(device_id)
            if device:
                info_text = f"Device: {device.get('name', 'Unknown')}\n"
                info_text += f"Type: {device.get('type', 'unknown')}\n"
                info_text += f"ID: {device_id}"
                self.info_label.setText(info_text)
        else:
            self.select_btn.setEnabled(False)
    
    def _on_device_double_clicked(self, item: QListWidgetItem):
        """Handle double-click on device."""
        device_id = item.data(Qt.ItemDataRole.UserRole)
        if device_id:
            self._select_device(device_id)
    
    def _on_select(self):
        """Handle select button click."""
        current_item = self.device_list.currentItem()
        if current_item:
            device_id = current_item.data(Qt.ItemDataRole.UserRole)
            if device_id:
                self._select_device(device_id)
    
    def _select_device(self, device_id: str):
        """Select device and close dialog."""
        self.selected_device_id = device_id
        self.device_selected.emit(device_id)
        self.accept()

