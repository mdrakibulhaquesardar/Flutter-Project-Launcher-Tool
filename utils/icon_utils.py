"""Icon utilities for Flutter Project Launcher Tool."""
from pathlib import Path
from typing import Optional
import os


def find_flutter_project_icon(project_path: str) -> Optional[str]:
    """
    Find the app icon for a Flutter project.
    
    Checks common locations:
    - Android: android/app/src/main/res/mipmap-*/ic_launcher.png
    - Android: android/app/src/main/res/drawable/ic_launcher.png
    - iOS: ios/Runner/Assets.xcassets/AppIcon.appiconset/
    - Web: web/icons/icon-*.png or web/favicon.png
    - Assets: assets/icon/ or assets/icons/
    
    Returns:
        Path to icon file if found, None otherwise
    """
    project = Path(project_path)
    
    if not project.exists():
        return None
    
    # Priority order for icon search
    icon_paths = [
        # Android - mipmap folders (check multiple densities)
        project / "android" / "app" / "src" / "main" / "res" / "mipmap-hdpi" / "ic_launcher.png",
        project / "android" / "app" / "src" / "main" / "res" / "mipmap-mdpi" / "ic_launcher.png",
        project / "android" / "app" / "src" / "main" / "res" / "mipmap-xhdpi" / "ic_launcher.png",
        project / "android" / "app" / "src" / "main" / "res" / "mipmap-xxhdpi" / "ic_launcher.png",
        project / "android" / "app" / "src" / "main" / "res" / "mipmap-xxxhdpi" / "ic_launcher.png",
        # Android - drawable folder
        project / "android" / "app" / "src" / "main" / "res" / "drawable" / "ic_launcher.png",
        # Android - alternative locations
        project / "android" / "app" / "src" / "main" / "res" / "mipmap" / "ic_launcher.png",
        # iOS - AppIcon (check for any PNG in the appiconset)
        project / "ios" / "Runner" / "Assets.xcassets" / "AppIcon.appiconset",
        # Web icons
        project / "web" / "icons" / "icon-512.png",
        project / "web" / "icons" / "icon-192.png",
        project / "web" / "favicon.png",
        # Assets folder
        project / "assets" / "icon" / "icon.png",
        project / "assets" / "icon" / "app_icon.png",
        project / "assets" / "icons" / "icon.png",
        project / "assets" / "icons" / "app_icon.png",
    ]
    
    # Check direct paths first
    for icon_path in icon_paths:
        if icon_path.exists():
            if icon_path.is_file():
                return str(icon_path)
            elif icon_path.is_dir():
                # For iOS AppIcon.appiconset, find the largest PNG
                png_files = list(icon_path.glob("*.png"))
                if png_files:
                    # Sort by file size (largest first)
                    png_files.sort(key=lambda x: x.stat().st_size, reverse=True)
                    return str(png_files[0])
    
    # Check Android mipmap folders dynamically
    android_res = project / "android" / "app" / "src" / "main" / "res"
    if android_res.exists():
        for mipmap_dir in android_res.glob("mipmap-*"):
            icon_file = mipmap_dir / "ic_launcher.png"
            if icon_file.exists():
                return str(icon_file)
    
    # Check web/icons folder for any icon
    web_icons = project / "web" / "icons"
    if web_icons.exists():
        icon_files = list(web_icons.glob("*.png"))
        if icon_files:
            # Prefer larger icons
            icon_files.sort(key=lambda x: x.stat().st_size, reverse=True)
            return str(icon_files[0])
    
    # Check assets/icon or assets/icons folders
    for assets_path in [project / "assets" / "icon", project / "assets" / "icons"]:
        if assets_path.exists():
            icon_files = list(assets_path.glob("*.png"))
            if icon_files:
                icon_files.sort(key=lambda x: x.stat().st_size, reverse=True)
                return str(icon_files[0])
    
    return None

