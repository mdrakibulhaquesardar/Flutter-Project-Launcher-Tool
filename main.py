"""Main entry point for FluStudio."""
import sys
import os
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from ui.main_window import MainWindow
from ui.license_dialog import LicenseDialog
from core.branding import Branding
from core.license import LicenseManager
from core.logger import Logger

# Windows-specific: Set process name for Task Manager
if os.name == 'nt':
    try:
        import ctypes
        # Set the process name in Windows Task Manager
        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleTitleW("FluStudio")
    except Exception:
        pass  # Silently fail if this doesn't work


def main():
    """Application entry point."""
    app = QApplication(sys.argv)
    app.setApplicationName(Branding.APP_NAME)
    app.setOrganizationName(Branding.ORGANIZATION_NAME)
    app.setApplicationVersion(Branding.APP_VERSION)
    
    # Set application icon
    icon_path = Branding.get_app_icon_path()
    if icon_path and icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))
    
    # Initialize logger
    logger = Logger()
    logger.info(f"Starting {Branding.APP_NAME} v{Branding.APP_VERSION}")
    
    # Apply global theme
    from core.theme import Theme
    app.setStyleSheet(Theme.get_global_stylesheet())
    
    # High DPI scaling is enabled by default in PyQt6
    # No need to set these attributes
    
    # Initialize license manager
    license_manager = LicenseManager()
    
    # Check license status and show reminder if needed
    if license_manager.should_show_reminder():
        days_remaining = license_manager.get_days_remaining()
        reply = QMessageBox.information(
            None, "Trial Reminder",
            f"Your trial expires in {days_remaining} day(s).\n\n"
            "Please activate a license key to continue using FluStudio.\n\n"
            "Would you like to activate a license now?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            license_dialog = LicenseDialog()
            license_dialog.exec()
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()


