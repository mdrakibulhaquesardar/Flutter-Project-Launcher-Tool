"""Main entry point for FluStudio."""
import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from ui.main_window import MainWindow
from core.branding import Branding

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
    
    # Apply global theme
    from core.theme import Theme
    app.setStyleSheet(Theme.get_global_stylesheet())
    
    # High DPI scaling is enabled by default in PyQt6
    # No need to set these attributes
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()


