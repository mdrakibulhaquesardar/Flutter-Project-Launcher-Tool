"""Template item widget for Flutter Project Launcher Tool."""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from typing import Dict, Any, Optional


class TemplateItem(QWidget):
    """Custom widget for displaying template card."""
    
    # Signals
    selected = pyqtSignal(str)  # template_id
    
    def __init__(self, template_data: Dict[str, Any], parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.template_data = template_data
        self.template_id = template_data.get("id", "")
        self._init_ui()
    
    def _init_ui(self):
        """Initialize UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(8)
        
        # Template name
        self.name_label = QLabel(self.template_data.get("name", "Unknown Template"), self)
        name_font = QFont()
        name_font.setBold(True)
        name_font.setPointSize(12)
        self.name_label.setFont(name_font)
        self.name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.name_label)
        
        # Template description
        description = self.template_data.get("description", "No description")
        self.desc_label = QLabel(description, self)
        self.desc_label.setWordWrap(True)
        self.desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.desc_label.setStyleSheet("color: #666; font-size: 9pt;")
        layout.addWidget(self.desc_label)
        
        # Template type badge
        template_type = self.template_data.get("type", "unknown")
        type_label = QLabel(template_type.upper(), self)
        type_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        if template_type == "builtin":
            type_label.setStyleSheet("""
                background-color: #0078d4;
                color: white;
                padding: 2px 8px;
                border-radius: 10px;
                font-size: 8pt;
            """)
        else:
            type_label.setStyleSheet("""
                background-color: #28a745;
                color: white;
                padding: 2px 8px;
                border-radius: 10px;
                font-size: 8pt;
            """)
        layout.addWidget(type_label)
        
        layout.addStretch()
        
        # Select button
        self.select_btn = QPushButton("Select", self)
        self.select_btn.clicked.connect(lambda: self.selected.emit(self.template_id))
        layout.addWidget(self.select_btn)
        
        # Style
        self.setStyleSheet("""
            TemplateItem {
                border: 2px solid #ddd;
                border-radius: 8px;
                background-color: white;
                min-height: 150px;
            }
            TemplateItem:hover {
                border-color: #0078d4;
                background-color: #f8f9fa;
            }
            QPushButton {
                padding: 6px;
                border: 1px solid #0078d4;
                border-radius: 4px;
                background-color: #0078d4;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #005a9e;
            }
        """)
    
    def mousePressEvent(self, event):
        """Handle mouse click on item."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.selected.emit(self.template_id)
        super().mousePressEvent(event)


