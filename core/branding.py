"""Branding configuration for FluStudio."""
from pathlib import Path
from typing import Optional
from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QIcon


class Branding:
    """Application branding configuration."""
    
    # Application Info
    APP_NAME = "FluStudio"
    APP_VERSION = "1.0.1"
    ORGANIZATION_NAME = "NextCode Studio"
    ORGANIZATION_DOMAIN = "nextcodestudio.com"
    
    # Branding Paths
    ASSETS_DIR = Path(__file__).parent.parent / "assets"
    ICONS_DIR = ASSETS_DIR / "icons"
    
    # Icon Paths
    APP_ICON = ICONS_DIR / "app_icon.ico"  # Windows icon
    APP_ICON_PNG = ICONS_DIR / "app_icon.png"  # PNG icon for other platforms
    LOGO_PNG = ICONS_DIR / "logo.png"  # Logo for About dialog
    
    @classmethod
    def get_app_icon_path(cls) -> Optional[Path]:
        """Get application icon path (prefers .ico on Windows, .png otherwise)."""
        import os
        if os.name == 'nt':
            if cls.APP_ICON.exists():
                return cls.APP_ICON
        if cls.APP_ICON_PNG.exists():
            return cls.APP_ICON_PNG
        return None
    
    @classmethod
    def get_logo_path(cls) -> Optional[Path]:
        """Get logo path for About dialog."""
        if cls.LOGO_PNG.exists():
            return cls.LOGO_PNG
        return cls.get_app_icon_path()
    
    @classmethod
    def get_about_text(cls) -> str:
        """Get formatted About dialog text."""
        logo_html = ""
        logo_path = cls.get_logo_path()
        if logo_path and logo_path.exists():
            logo_html = f'<img src="{logo_path}" width="64" height="64" style="margin: 10px;">'
        
        return f"""
        <div style="text-align: center;">
            {logo_html}
            <h2>{cls.APP_NAME}</h2>
            <p><b>Version {cls.APP_VERSION}</b></p>
            <p>A powerful desktop application for managing Flutter projects.</p>
            <p>Built with Python and PyQt6</p>
            <hr>
            <p style="color: #666; font-size: 9pt;">
                © 2024 {cls.ORGANIZATION_NAME}<br>
                All rights reserved
            </p>
        </div>
        """
    
    @classmethod
    def apply_window_icon(cls, widget: QWidget) -> bool:
        """
        Apply application icon to a widget (window/dialog).
        
        Args:
            widget: QWidget to apply icon to
            
        Returns:
            True if icon was applied, False otherwise
        """
        icon_path = cls.get_app_icon_path()
        if icon_path and icon_path.exists():
            widget.setWindowIcon(QIcon(str(icon_path)))
            return True
        return False

