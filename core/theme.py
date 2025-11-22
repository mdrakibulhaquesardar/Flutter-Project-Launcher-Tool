"""Application theme and styling."""
from typing import Dict


class Theme:
    """Application theme colors and styles."""
    
    # Color palette - Classic Windows + Developer Tool Look
    PRIMARY = "#005A9E"      # Windows Blue
    SECONDARY = "#3E4C59"    # Slate Gray
    ACCENT = "#4682B4"       # Steel Blue
    BACKGROUND = ""          # System default (Qt default light gray)
    SURFACE = "#FFFFFF"      # White surface/card background
    
    # Derived colors
    TEXT_PRIMARY = "#000000"  # Black text
    TEXT_SECONDARY = "#3E4C59"  # Slate gray text
    TEXT_MUTED = "#808080"    # Gray text
    BORDER = "#C0C0C0"        # Classic Windows border gray
    HOVER = "#E8F4F8"         # Light blue hover
    
    # Status colors
    SUCCESS = "#107C10"       # Windows green
    WARNING = "#FF8C00"       # Windows orange
    ERROR = "#E81123"         # Windows red
    INFO = PRIMARY
    
    @classmethod
    def get_global_stylesheet(cls) -> str:
        """Get global application stylesheet."""
        # Use system default background if BACKGROUND is empty
        bg_color = cls.BACKGROUND if cls.BACKGROUND else "palette(window)"
        return f"""
        /* Global Application Styles - Classic Windows + Developer Tool Look */
        QMainWindow {{
            background-color: {bg_color};
            color: {cls.TEXT_PRIMARY};
        }}
        
        QWidget {{
            background-color: {bg_color};
            color: {cls.TEXT_PRIMARY};
        }}
        
        /* Menu Bar */
        QMenuBar {{
            background-color: {cls.SURFACE};
            color: {cls.TEXT_PRIMARY};
            border-bottom: 1px solid {cls.BORDER};
            padding: 4px;
        }}
        
        QMenuBar::item {{
            background-color: transparent;
            padding: 6px 12px;
            border-radius: 2px;
        }}
        
        QMenuBar::item:selected {{
            background-color: {cls.PRIMARY};
            color: white;
        }}
        
        QMenuBar::item:pressed {{
            background-color: {cls.ACCENT};
            color: white;
        }}
        
        /* Menus */
        QMenu {{
            background-color: {cls.SURFACE};
            color: {cls.TEXT_PRIMARY};
            border: 1px solid {cls.BORDER};
            padding: 2px;
        }}
        
        QMenu::item {{
            padding: 6px 24px 6px 12px;
            border-radius: 0px;
        }}
        
        QMenu::item:selected {{
            background-color: {cls.PRIMARY};
            color: white;
        }}
        
        QMenu::separator {{
            height: 1px;
            background-color: {cls.BORDER};
            margin: 4px 8px;
        }}
        
        /* Status Bar */
        QStatusBar {{
            background-color: {cls.SURFACE};
            color: {cls.TEXT_SECONDARY};
            border-top: 1px solid {cls.BORDER};
        }}
        
        /* Buttons */
        QPushButton {{
            background-color: {cls.SURFACE};
            color: {cls.TEXT_PRIMARY};
            border: 1px solid {cls.BORDER};
            border-radius: 3px;
            padding: 6px 14px;
            font-weight: normal;
        }}
        
        QPushButton:hover {{
            background-color: {cls.HOVER};
            border-color: {cls.PRIMARY};
        }}
        
        QPushButton:pressed {{
            background-color: {cls.PRIMARY};
            color: white;
            border-color: {cls.PRIMARY};
        }}
        
        QPushButton:disabled {{
            background-color: {bg_color};
            color: {cls.TEXT_MUTED};
            border-color: {cls.BORDER};
        }}
        
        /* Primary Action Buttons */
        QPushButton[class="primary"] {{
            background-color: {cls.PRIMARY};
            color: white;
            border: 1px solid {cls.PRIMARY};
        }}
        
        QPushButton[class="primary"]:hover {{
            background-color: #0066B3;
            border-color: #0066B3;
        }}
        
        /* Accent Buttons */
        QPushButton[class="accent"] {{
            background-color: {cls.ACCENT};
            color: white;
            border: 1px solid {cls.ACCENT};
        }}
        
        QPushButton[class="accent"]:hover {{
            background-color: #5A92C4;
            border-color: #5A92C4;
        }}
        
        /* Labels */
        QLabel {{
            color: {cls.TEXT_PRIMARY};
            background-color: transparent;
        }}
        
        /* Line Edit */
        QLineEdit {{
            background-color: {cls.SURFACE};
            color: {cls.TEXT_PRIMARY};
            border: 1px solid {cls.BORDER};
            border-radius: 2px;
            padding: 4px 8px;
            selection-background-color: {cls.PRIMARY};
            selection-color: white;
        }}
        
        QLineEdit:focus {{
            border-color: {cls.PRIMARY};
        }}
        
        /* Text Edit */
        QTextEdit {{
            background-color: {cls.SURFACE};
            color: {cls.TEXT_PRIMARY};
            border: 1px solid {cls.BORDER};
            border-radius: 2px;
            selection-background-color: {cls.PRIMARY};
            selection-color: white;
        }}
        
        QPlainTextEdit {{
            background-color: {cls.SURFACE};
            color: {cls.TEXT_PRIMARY};
            border: 1px solid {cls.BORDER};
            border-radius: 2px;
            selection-background-color: {cls.PRIMARY};
            selection-color: white;
        }}
        
        /* Scroll Area */
        QScrollArea {{
            background-color: {bg_color};
            border: none;
        }}
        
        QScrollBar:vertical {{
            background-color: {cls.SURFACE};
            width: 17px;
            border: 1px solid {cls.BORDER};
            border-radius: 0px;
        }}
        
        QScrollBar::handle:vertical {{
            background-color: {cls.SECONDARY};
            border-radius: 0px;
            min-height: 30px;
            border: 1px solid {cls.BORDER};
        }}
        
        QScrollBar::handle:vertical:hover {{
            background-color: {cls.PRIMARY};
        }}
        
        QScrollBar:horizontal {{
            background-color: {cls.SURFACE};
            height: 17px;
            border: 1px solid {cls.BORDER};
            border-radius: 0px;
        }}
        
        QScrollBar::handle:horizontal {{
            background-color: {cls.SECONDARY};
            border-radius: 0px;
            min-width: 30px;
            border: 1px solid {cls.BORDER};
        }}
        
        QScrollBar::handle:horizontal:hover {{
            background-color: {cls.PRIMARY};
        }}
        
        /* Progress Bar */
        QProgressBar {{
            background-color: {cls.SURFACE};
            border: 1px solid {cls.BORDER};
            border-radius: 2px;
            text-align: center;
            color: {cls.TEXT_PRIMARY};
        }}
        
        QProgressBar::chunk {{
            background-color: {cls.PRIMARY};
            border-radius: 1px;
        }}
        
        /* Combo Box */
        QComboBox {{
            background-color: {cls.SURFACE};
            color: {cls.TEXT_PRIMARY};
            border: 1px solid {cls.BORDER};
            border-radius: 2px;
            padding: 4px 8px;
        }}
        
        QComboBox:hover {{
            border-color: {cls.PRIMARY};
        }}
        
        QComboBox::drop-down {{
            border: none;
            width: 20px;
        }}
        
        QComboBox::down-arrow {{
            image: none;
            border-left: 4px solid transparent;
            border-right: 4px solid transparent;
            border-top: 6px solid {cls.TEXT_SECONDARY};
            margin-right: 8px;
        }}
        
        QComboBox QAbstractItemView {{
            background-color: {cls.SURFACE};
            color: {cls.TEXT_PRIMARY};
            border: 1px solid {cls.BORDER};
            selection-background-color: {cls.PRIMARY};
            selection-color: white;
        }}
        
        /* List Widget */
        QListWidget {{
            background-color: {cls.SURFACE};
            color: {cls.TEXT_PRIMARY};
            border: 1px solid {cls.BORDER};
            border-radius: 2px;
        }}
        
        QListWidget::item {{
            padding: 6px;
            border-radius: 0px;
        }}
        
        QListWidget::item:selected {{
            background-color: {cls.PRIMARY};
            color: white;
        }}
        
        QListWidget::item:hover {{
            background-color: {cls.HOVER};
        }}
        
        /* Dialog */
        QDialog {{
            background-color: {bg_color};
            color: {cls.TEXT_PRIMARY};
        }}
        
        /* Message Box */
        QMessageBox {{
            background-color: {bg_color};
            color: {cls.TEXT_PRIMARY};
        }}
        
        QMessageBox QLabel {{
            color: {cls.TEXT_PRIMARY};
        }}
        
        /* Splitter */
        QSplitter::handle {{
            background-color: {cls.BORDER};
        }}
        
        QSplitter::handle:horizontal {{
            width: 2px;
        }}
        
        QSplitter::handle:vertical {{
            height: 2px;
        }}
        
        QSplitter::handle:hover {{
            background-color: {cls.PRIMARY};
        }}
        """
    
    @classmethod
    def get_project_item_stylesheet(cls) -> str:
        """Get stylesheet for project items."""
        bg_color = cls.BACKGROUND if cls.BACKGROUND else "palette(window)"
        return f"""
        ProjectItem {{
            border: 1px solid {cls.BORDER};
            border-radius: 6px;
            background-color: {cls.SURFACE};
            padding: 2px;
        }}
        
        ProjectItem:hover {{
            background-color: {cls.HOVER};
            border-color: {cls.PRIMARY};
            border-width: 2px;
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {cls.HOVER}, stop:1 {cls.SURFACE});
        }}
        
        ProjectItem QPushButton {{
            background-color: {bg_color};
            color: {cls.TEXT_PRIMARY};
            border: 1px solid {cls.BORDER};
            border-radius: 4px;
            padding: 5px 14px;
            font-weight: 500;
        }}
        
        ProjectItem QPushButton:hover {{
            background-color: {cls.PRIMARY};
            color: white;
            border-color: {cls.PRIMARY};
            transform: scale(1.05);
        }}
        
        ProjectItem QPushButton:pressed {{
            background-color: {cls.ACCENT};
            border-color: {cls.ACCENT};
        }}
        """
    
    @classmethod
    def get_console_stylesheet(cls) -> str:
        """Get stylesheet for console widgets."""
        bg_color = cls.BACKGROUND if cls.BACKGROUND else "palette(window)"
        return f"""
        QPlainTextEdit {{
            background-color: {cls.SURFACE};
            color: {cls.TEXT_PRIMARY};
            border: 1px solid {cls.BORDER};
            selection-background-color: {cls.PRIMARY};
            selection-color: white;
            font-family: 'Consolas', 'Courier New', monospace;
        }}
        """
    
    @classmethod
    def get_colors(cls) -> Dict[str, str]:
        """Get all theme colors as a dictionary."""
        return {
            "primary": cls.PRIMARY,
            "secondary": cls.SECONDARY,
            "background": cls.BACKGROUND if cls.BACKGROUND else "system",
            "accent": cls.ACCENT,
            "surface": cls.SURFACE,
            "text_primary": cls.TEXT_PRIMARY,
            "text_secondary": cls.TEXT_SECONDARY,
            "text_muted": cls.TEXT_MUTED,
            "border": cls.BORDER,
            "hover": cls.HOVER,
            "success": cls.SUCCESS,
            "warning": cls.WARNING,
            "error": cls.ERROR,
            "info": cls.INFO,
        }

