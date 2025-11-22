"""Main entry point for FluStudio."""
import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from ui.main_window import MainWindow

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
    app.setApplicationName("FluStudio")
    app.setOrganizationName("FlutterTools")
    
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


