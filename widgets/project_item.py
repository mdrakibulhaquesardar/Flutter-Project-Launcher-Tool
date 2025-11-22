"""Project item widget for Flutter Project Launcher Tool."""
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QMenu
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QFont, QPixmap, QIcon
from pathlib import Path
from typing import Dict, Any, Optional


class ProjectItem(QWidget):
    """Custom widget for displaying project in list."""
    
    # Signals
    clicked = pyqtSignal(str)  # project_path
    run_clicked = pyqtSignal(str)
    open_clicked = pyqtSignal(str)
    build_apk_clicked = pyqtSignal(str)
    build_bundle_clicked = pyqtSignal(str)
    view_details_clicked = pyqtSignal(str)
    open_vscode_clicked = pyqtSignal(str)
    open_android_studio_clicked = pyqtSignal(str)
    copy_path_clicked = pyqtSignal(str)
    manage_tags_clicked = pyqtSignal(str)
    remove_from_list_clicked = pyqtSignal(str)
    
    def __init__(self, project_data: Dict[str, Any], parent: Optional[QWidget] = None, is_grid_view: bool = False):
        super().__init__(parent)
        self.project_data = project_data
        self.project_path = project_data.get("path", "")
        self.is_grid_view = is_grid_view
        self._init_ui()
    
    def _init_ui(self):
        """Initialize UI components."""
        from core.theme import Theme
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 12, 15, 12)
        layout.setSpacing(15)
        
        # Left side - Project icon (profile picture style)
        icon_path = self.project_data.get("icon_path")
        icon_size = 48  # Larger icon size
        container_size = 52  # Container size with border
        
        if icon_path and Path(icon_path).exists():
            try:
                icon_label = QLabel(self)
                pixmap = QPixmap(icon_path)
                # Scale icon to smaller profile picture size
                scaled_pixmap = pixmap.scaled(icon_size, icon_size, Qt.AspectRatioMode.KeepAspectRatio, 
                                            Qt.TransformationMode.SmoothTransformation)
                icon_label.setPixmap(scaled_pixmap)
                icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                icon_label.setStyleSheet(f"""
                    QLabel {{
                        border: 3px solid {Theme.PRIMARY};
                        border-radius: 26px;
                        padding: 2px;
                        background-color: {Theme.SURFACE};
                    }}
                """)
                icon_label.setFixedSize(container_size, container_size)
                layout.addWidget(icon_label)
            except Exception:
                # If icon loading fails, show placeholder
                placeholder = QLabel("📱", self)
                placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
                placeholder.setStyleSheet(f"""
                    QLabel {{
                        border: 3px solid {Theme.BORDER};
                        border-radius: 26px;
                        padding: 2px;
                        background-color: {Theme.SURFACE};
                        font-size: 24px;
                    }}
                """)
                placeholder.setFixedSize(container_size, container_size)
                layout.addWidget(placeholder)
        else:
            # Show placeholder icon if no icon found
            placeholder = QLabel("📱", self)
            placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
            from core.theme import Theme
            placeholder.setStyleSheet(f"""
                QLabel {{
                    border: 3px solid {Theme.BORDER};
                    border-radius: 26px;
                    padding: 2px;
                    background-color: {Theme.SURFACE};
                    font-size: 24px;
                }}
            """)
            placeholder.setFixedSize(container_size, container_size)
            layout.addWidget(placeholder)
        
        # Center - Project info
        info_layout = QVBoxLayout()
        info_layout.setSpacing(4)
        
        # Project name
        self.name_label = QLabel(self.project_data.get("name", "Unknown Project"), self)
        name_font = QFont()
        name_font.setBold(True)
        name_font.setPointSize(12)
        self.name_label.setFont(name_font)
        self.name_label.setStyleSheet(f"color: {Theme.TEXT_PRIMARY};")
        info_layout.addWidget(self.name_label)
        
        # Package name (from pubspec.yaml)
        package_name = self.project_data.get("package_name") or self.project_data.get("name", "")
        if package_name:
            package_label = QLabel(f"📦 {package_name}", self)
            package_label.setStyleSheet(f"color: {Theme.PRIMARY}; font-size: 9pt;")
            info_layout.addWidget(package_label)
        
        # Project path
        path = self.project_data.get("path", "")
        path_display = Path(path).as_posix() if path else "No path"
        self.path_label = QLabel(f"📁 {path_display}", self)
        self.path_label.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 8pt;")
        self.path_label.setWordWrap(True)
        info_layout.addWidget(self.path_label)
        
        # Metadata row 1: Last modified
        metadata_row1 = []
        if self.project_data.get("last_modified"):
            from datetime import datetime
            try:
                dt = datetime.fromisoformat(self.project_data["last_modified"])
                metadata_row1.append(f"🕒 Modified: {dt.strftime('%Y-%m-%d %H:%M')}")
            except:
                pass
        
        # Metadata row 2: Flutter SDK version
        metadata_row2 = []
        flutter_version = self.project_data.get("flutter_version")
        flutter_constraint = self.project_data.get("flutter_sdk_constraint")
        
        if flutter_version:
            # Extract just the version number if it contains "Flutter"
            version_display = flutter_version
            if "Flutter" in flutter_version:
                import re
                version_match = re.search(r'Flutter\s+([\d.]+)', flutter_version)
                if version_match:
                    version_display = f"v{version_match.group(1)}"
                else:
                    version_display = flutter_version.replace("Flutter", "").strip()
            metadata_row2.append(f"🔧 SDK: {version_display}")
        elif flutter_constraint:
            metadata_row2.append(f"🔧 SDK Constraint: {flutter_constraint}")
        else:
            metadata_row2.append("🔧 SDK: Unknown")
        
        # Display metadata rows
        if metadata_row1:
            self.metadata_label1 = QLabel(" • ".join(metadata_row1), self)
            self.metadata_label1.setStyleSheet(f"color: {Theme.TEXT_MUTED}; font-size: 8pt;")
            info_layout.addWidget(self.metadata_label1)
        
        if metadata_row2:
            self.metadata_label2 = QLabel(" • ".join(metadata_row2), self)
            self.metadata_label2.setStyleSheet(f"color: {Theme.TEXT_MUTED}; font-size: 8pt;")
            info_layout.addWidget(self.metadata_label2)
        
        # Tags display
        tags = self.project_data.get("tags", [])
        if tags and isinstance(tags, list):
            tags_layout = QHBoxLayout()
            tags_layout.setSpacing(4)
            tags_label = QLabel("Tags:", self)
            tags_label.setStyleSheet(f"color: {Theme.TEXT_MUTED}; font-size: 8pt;")
            tags_layout.addWidget(tags_label)
            
            for tag in tags[:5]:  # Show max 5 tags
                tag_label = QLabel(f"#{tag}", self)
                tag_label.setStyleSheet(f"""
                    QLabel {{
                        background-color: {Theme.PRIMARY};
                        color: white;
                        padding: 2px 6px;
                        border-radius: 3px;
                        font-size: 7pt;
                    }}
                """)
                tags_layout.addWidget(tag_label)
            
            if len(tags) > 5:
                more_label = QLabel(f"+{len(tags) - 5}", self)
                more_label.setStyleSheet(f"color: {Theme.TEXT_MUTED}; font-size: 7pt;")
                tags_layout.addWidget(more_label)
            
            tags_layout.addStretch()
            info_layout.addLayout(tags_layout)
        
        info_layout.addStretch()
        layout.addLayout(info_layout, 1)
        
        # Right side - Action buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(8)
        
        self.run_btn = QPushButton("▶ Run", self)
        self.run_btn.setMinimumWidth(90)
        self.run_btn.setMaximumWidth(90)
        self.run_btn.clicked.connect(lambda: self.run_clicked.emit(self.project_path))
        self.run_btn.setToolTip("Run this Flutter project")
        button_layout.addWidget(self.run_btn)
        
        self.open_btn = QPushButton("📂 Open", self)
        self.open_btn.setMinimumWidth(90)
        self.open_btn.setMaximumWidth(90)
        self.open_btn.clicked.connect(lambda: self.open_clicked.emit(self.project_path))
        self.open_btn.setToolTip("Open project folder")
        button_layout.addWidget(self.open_btn)
        
        layout.addLayout(button_layout)
        
        # Style - use theme
        self.setStyleSheet(Theme.get_project_item_stylesheet())
    
    def mousePressEvent(self, event):
        """Handle mouse click on item."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.project_path)
        super().mousePressEvent(event)
    
    def contextMenuEvent(self, event):
        """Handle right-click context menu."""
        menu = QMenu(self)
        
        # Run Project
        run_action = menu.addAction("▶ Run Project")
        run_action.triggered.connect(lambda: self.run_clicked.emit(self.project_path))
        
        menu.addSeparator()
        
        # Open actions
        open_folder_action = menu.addAction("📂 Open Folder")
        open_folder_action.triggered.connect(lambda: self.open_clicked.emit(self.project_path))
        
        open_vscode_action = menu.addAction("📝 Open in VS Code")
        open_vscode_action.triggered.connect(lambda: self.open_vscode_clicked.emit(self.project_path))
        
        open_as_action = menu.addAction("🛠 Open in Android Studio")
        open_as_action.triggered.connect(lambda: self.open_android_studio_clicked.emit(self.project_path))
        
        menu.addSeparator()
        
        # Build actions
        build_apk_action = menu.addAction("📦 Build APK")
        build_apk_action.triggered.connect(lambda: self.build_apk_clicked.emit(self.project_path))
        
        build_bundle_action = menu.addAction("🎁 Build Bundle")
        build_bundle_action.triggered.connect(lambda: self.build_bundle_clicked.emit(self.project_path))
        
        menu.addSeparator()
        
        # Project actions
        view_details_action = menu.addAction("ℹ️ View Details")
        view_details_action.triggered.connect(lambda: self.view_details_clicked.emit(self.project_path))
        
        manage_tags_action = menu.addAction("🏷️ Manage Tags")
        manage_tags_action.triggered.connect(lambda: self.manage_tags_clicked.emit(self.project_path))
        
        menu.addSeparator()
        
        # Utility actions
        copy_path_action = menu.addAction("📋 Copy Path")
        copy_path_action.triggered.connect(lambda: self.copy_path_clicked.emit(self.project_path))
        
        remove_action = menu.addAction("🗑️ Remove from List")
        remove_action.triggered.connect(lambda: self.remove_from_list_clicked.emit(self.project_path))
        
        # Show menu at cursor position
        menu.exec(event.globalPos())


