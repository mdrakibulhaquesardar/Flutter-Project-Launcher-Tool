"""Project item widget for Flutter Project Launcher Tool."""
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton
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
    
    def __init__(self, project_data: Dict[str, Any], parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.project_data = project_data
        self.project_path = project_data.get("path", "")
        self._init_ui()
    
    def _init_ui(self):
        """Initialize UI components."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(12)
        
        # Left side - Project icon (profile picture style)
        icon_path = self.project_data.get("icon_path")
        icon_size = 36  # Smaller icon size
        container_size = 40  # Container size with border
        
        if icon_path and Path(icon_path).exists():
            try:
                icon_label = QLabel(self)
                pixmap = QPixmap(icon_path)
                # Scale icon to smaller profile picture size
                scaled_pixmap = pixmap.scaled(icon_size, icon_size, Qt.AspectRatioMode.KeepAspectRatio, 
                                            Qt.TransformationMode.SmoothTransformation)
                icon_label.setPixmap(scaled_pixmap)
                icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                icon_label.setStyleSheet("""
                    QLabel {
                        border: 2px solid #0078d4;
                        border-radius: 18px;
                        padding: 1px;
                        background-color: white;
                    }
                """)
                icon_label.setFixedSize(container_size, container_size)
                layout.addWidget(icon_label)
            except Exception:
                # If icon loading fails, show placeholder
                placeholder = QLabel("📱", self)
                placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
                placeholder.setStyleSheet("""
                    QLabel {
                        border: 2px solid #ddd;
                        border-radius: 18px;
                        padding: 1px;
                        background-color: #f0f0f0;
                        font-size: 18px;
                    }
                """)
                placeholder.setFixedSize(container_size, container_size)
                layout.addWidget(placeholder)
        else:
            # Show placeholder icon if no icon found
            placeholder = QLabel("📱", self)
            placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
            placeholder.setStyleSheet("""
                QLabel {
                    border: 2px solid #ddd;
                    border-radius: 18px;
                    padding: 1px;
                    background-color: #f0f0f0;
                    font-size: 18px;
                }
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
        name_font.setPointSize(11)
        self.name_label.setFont(name_font)
        info_layout.addWidget(self.name_label)
        
        # Project path
        path = self.project_data.get("path", "")
        path_display = Path(path).as_posix() if path else "No path"
        self.path_label = QLabel(path_display, self)
        self.path_label.setStyleSheet("color: gray;")
        self.path_label.setWordWrap(True)
        info_layout.addWidget(self.path_label)
        
        # Metadata (last modified, Flutter version)
        metadata_text = []
        if self.project_data.get("last_modified"):
            from datetime import datetime
            try:
                dt = datetime.fromisoformat(self.project_data["last_modified"])
                metadata_text.append(f"Modified: {dt.strftime('%Y-%m-%d %H:%M')}")
            except:
                pass
        
        # Show Flutter SDK version prominently
        flutter_version = self.project_data.get("flutter_version")
        flutter_constraint = self.project_data.get("flutter_sdk_constraint")
        
        if flutter_version:
            # Show version with icon
            metadata_text.append(f"🔧 {flutter_version}")
        elif flutter_constraint:
            # Show SDK constraint if version not available
            metadata_text.append(f"SDK: {flutter_constraint}")
        else:
            # Show "Unknown" if no version info
            metadata_text.append("Flutter: Unknown")
        
        if metadata_text:
            self.metadata_label = QLabel(" • ".join(metadata_text), self)
            self.metadata_label.setStyleSheet("color: #666; font-size: 9pt;")
            info_layout.addWidget(self.metadata_label)
        
        info_layout.addStretch()
        layout.addLayout(info_layout, 1)
        
        # Right side - Action buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(5)
        
        self.run_btn = QPushButton("▶ Run", self)
        self.run_btn.setMaximumWidth(80)
        self.run_btn.clicked.connect(lambda: self.run_clicked.emit(self.project_path))
        button_layout.addWidget(self.run_btn)
        
        self.open_btn = QPushButton("📂 Open", self)
        self.open_btn.setMaximumWidth(80)
        self.open_btn.clicked.connect(lambda: self.open_clicked.emit(self.project_path))
        button_layout.addWidget(self.open_btn)
        
        layout.addLayout(button_layout)
        
        # Style
        self.setStyleSheet("""
            ProjectItem {
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: white;
            }
            ProjectItem:hover {
                background-color: #f5f5f5;
                border-color: #0078d4;
            }
            QPushButton {
                padding: 4px 8px;
                border: 1px solid #ccc;
                border-radius: 3px;
                background-color: white;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """)
    
    def mousePressEvent(self, event):
        """Handle mouse click on item."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.project_path)
        super().mousePressEvent(event)


