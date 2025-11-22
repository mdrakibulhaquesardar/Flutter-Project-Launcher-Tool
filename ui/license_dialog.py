"""License management dialog for FluStudio."""
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QMessageBox, QProgressBar,
                             QGroupBox, QTextEdit)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from datetime import datetime
from core.license import LicenseManager
from core.branding import Branding
from core.logger import Logger


class LicenseDialog(QDialog):
    """Dialog for managing application license."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.license_manager = LicenseManager()
        self.logger = Logger()
        self._init_ui()
        self._load_license_info()
    
    def _init_ui(self):
        """Initialize UI components."""
        Branding.apply_window_icon(self)
        
        self.setWindowTitle("License")
        self.setMinimumSize(500, 400)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title_label = QLabel("FluStudio License")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # License Status Group
        status_group = QGroupBox("License Status")
        status_layout = QVBoxLayout()
        status_layout.setSpacing(10)
        
        self.status_label = QLabel()
        self.status_label.setWordWrap(True)
        status_layout.addWidget(self.status_label)
        
        # Trial progress (if trial active)
        self.trial_progress_label = QLabel()
        self.trial_progress_label.setVisible(False)
        status_layout.addWidget(self.trial_progress_label)
        
        self.trial_progress_bar = QProgressBar()
        self.trial_progress_bar.setVisible(False)
        self.trial_progress_bar.setMinimum(0)
        self.trial_progress_bar.setMaximum(14)
        status_layout.addWidget(self.trial_progress_bar)
        
        # License info
        self.license_info_label = QLabel()
        self.license_info_label.setVisible(False)
        self.license_info_label.setWordWrap(True)
        status_layout.addWidget(self.license_info_label)
        
        status_group.setLayout(status_layout)
        layout.addWidget(status_group)
        
        # License Key Input Group
        key_group = QGroupBox("Activate License")
        key_layout = QVBoxLayout()
        key_layout.setSpacing(10)
        
        key_input_layout = QHBoxLayout()
        key_label = QLabel("License Key:")
        self.key_input = QLineEdit()
        self.key_input.setPlaceholderText("XXXX-XXXX-XXXX-XXXX")
        self.key_input.textChanged.connect(self._on_key_changed)
        key_input_layout.addWidget(key_label)
        key_input_layout.addWidget(self.key_input)
        key_layout.addLayout(key_input_layout)
        
        activate_btn_layout = QHBoxLayout()
        activate_btn_layout.addStretch()
        self.activate_btn = QPushButton("Activate")
        self.activate_btn.setEnabled(False)
        self.activate_btn.clicked.connect(self._activate_license)
        activate_btn_layout.addWidget(self.activate_btn)
        key_layout.addLayout(activate_btn_layout)
        
        key_group.setLayout(key_layout)
        layout.addWidget(key_group)
        
        # Purchase License
        purchase_layout = QHBoxLayout()
        purchase_layout.addStretch()
        purchase_btn = QPushButton("Purchase License")
        purchase_btn.clicked.connect(self._purchase_license)
        purchase_layout.addWidget(purchase_btn)
        layout.addLayout(purchase_layout)
        
        layout.addStretch()
        
        # Close button
        close_layout = QHBoxLayout()
        close_layout.addStretch()
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        close_layout.addWidget(close_btn)
        layout.addLayout(close_layout)
    
    def _on_key_changed(self, text: str):
        """Handle license key input change."""
        # Enable activate button if key format looks valid
        key_clean = text.replace('-', '').replace(' ', '').upper()
        is_valid_format = len(key_clean) == 16 and key_clean.isalnum()
        self.activate_btn.setEnabled(is_valid_format)
    
    def _load_license_info(self):
        """Load and display license information."""
        info = self.license_manager.get_license_info()
        status = info["status"]
        
        if status == "license_active":
            self.status_label.setText(
                "<b>Status:</b> License Activated<br>"
                "<span style='color: green;'>✓ Your license is active</span>"
            )
            self.status_label.setStyleSheet("color: green;")
            
            activated_at = info.get("activated_at")
            if activated_at:
                try:
                    dt = datetime.fromisoformat(activated_at)
                    self.license_info_label.setText(
                        f"<b>Activated:</b> {dt.strftime('%Y-%m-%d %H:%M:%S')}"
                    )
                    self.license_info_label.setVisible(True)
                except Exception:
                    pass
            
            self.trial_progress_label.setVisible(False)
            self.trial_progress_bar.setVisible(False)
            
        elif status == "trial_active":
            days_remaining = info["days_remaining"]
            self.status_label.setText(
                "<b>Status:</b> Trial Period Active<br>"
                f"<span style='color: orange;'>You have {days_remaining} day(s) remaining</span>"
            )
            self.status_label.setStyleSheet("color: orange;")
            
            # Show progress
            self.trial_progress_label.setText(f"Trial Progress: {days_remaining} of {LicenseManager.TRIAL_DAYS} days remaining")
            self.trial_progress_label.setVisible(True)
            
            self.trial_progress_bar.setValue(days_remaining)
            self.trial_progress_bar.setVisible(True)
            
            # Show reminder if expiring soon
            if self.license_manager.should_show_reminder():
                reminder_text = (
                    f"<b>Reminder:</b> Your trial expires in {days_remaining} day(s). "
                    "Please activate a license key to continue using FluStudio."
                )
                self.license_info_label.setText(reminder_text)
                self.license_info_label.setStyleSheet("color: orange;")
                self.license_info_label.setVisible(True)
            
        elif status == "trial_expired":
            self.status_label.setText(
                "<b>Status:</b> Trial Period Expired<br>"
                "<span style='color: red;'>Your trial period has ended</span>"
            )
            self.status_label.setStyleSheet("color: red;")
            
            self.license_info_label.setText(
                "Please activate a license key to continue using FluStudio."
            )
            self.license_info_label.setStyleSheet("color: red;")
            self.license_info_label.setVisible(True)
            
            self.trial_progress_label.setVisible(False)
            self.trial_progress_bar.setVisible(False)
            
        else:  # license_invalid
            self.status_label.setText(
                "<b>Status:</b> Invalid License<br>"
                "<span style='color: red;'>Your license key is invalid</span>"
            )
            self.status_label.setStyleSheet("color: red;")
            
            self.license_info_label.setText(
                "Please enter a valid license key or contact support."
            )
            self.license_info_label.setVisible(True)
    
    def _activate_license(self):
        """Activate the entered license key."""
        key = self.key_input.text().strip()
        
        if not key:
            QMessageBox.warning(self, "Invalid Key", "Please enter a license key.")
            return
        
        # Normalize key format
        key_clean = key.replace('-', '').replace(' ', '').upper()
        if len(key_clean) != 16:
            QMessageBox.warning(
                self, "Invalid Format",
                "License key must be 16 characters.\nFormat: XXXX-XXXX-XXXX-XXXX"
            )
            return
        
        # Format with dashes
        formatted_key = f"{key_clean[:4]}-{key_clean[4:8]}-{key_clean[8:12]}-{key_clean[12:16]}"
        
        # Activate
        success, message = self.license_manager.activate_license(formatted_key)
        
        if success:
            QMessageBox.information(self, "License Activated", message)
            # Force refresh by creating new license manager instance
            self.license_manager = LicenseManager()
            self._load_license_info()  # Refresh display
            self.key_input.clear()
        else:
            QMessageBox.warning(self, "Activation Failed", message)
    
    def _purchase_license(self):
        """Open purchase/license website."""
        from PyQt6.QtGui import QDesktopServices
        from PyQt6.QtCore import QUrl
        
        url = f"https://{Branding.ORGANIZATION_DOMAIN}/purchase"
        QDesktopServices.openUrl(QUrl(url))

