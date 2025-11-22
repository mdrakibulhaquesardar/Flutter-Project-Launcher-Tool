"""Main entry point for Flutter Project Launcher Tool."""
import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from ui.main_window import MainWindow


def main():
    """Application entry point."""
    app = QApplication(sys.argv)
    app.setApplicationName("Flutter Project Launcher")
    app.setOrganizationName("FlutterTools")
    
    # High DPI scaling is enabled by default in PyQt6
    # No need to set these attributes
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()


