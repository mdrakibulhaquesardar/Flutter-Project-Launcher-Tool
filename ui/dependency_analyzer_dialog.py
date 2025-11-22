"""Dependency Analyzer dialog for Flutter Project Launcher Tool."""
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QTextEdit, QMessageBox, QTabWidget, QWidget)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont
from services.dependency_service import DependencyService
from core.logger import Logger
from typing import Optional


class DependencyAnalyzerDialog(QDialog):
    """Dialog for analyzing Flutter project dependencies."""
    
    def __init__(self, project_path: Optional[str] = None, parent=None):
        super().__init__(parent)
        self.dependency_service = DependencyService()
        self.logger = Logger()
        self.project_path = project_path
        self._init_ui()
        # Defer loading until dialog is shown
        if project_path:
            QTimer.singleShot(0, self._analyze_dependencies)
    
    def _init_ui(self):
        """Initialize UI components."""
        self.setWindowTitle("Dependency Analyzer")
        self.setMinimumSize(800, 600)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        # Header
        header_label = QLabel("Flutter Dependency Analyzer", self)
        header_font = QFont()
        header_font.setBold(True)
        header_font.setPointSize(12)
        header_label.setFont(header_font)
        layout.addWidget(header_label)
        
        if not self.project_path:
            no_project_label = QLabel("⚠️ No project selected. Please select a project first.", self)
            no_project_label.setStyleSheet("color: orange; padding: 10px;")
            layout.addWidget(no_project_label)
        
        # Tabs
        tabs = QTabWidget(self)
        
        # Dependencies tab
        deps_tab = QWidget()
        deps_layout = QVBoxLayout(deps_tab)
        self.deps_text = QTextEdit(deps_tab)
        self.deps_text.setReadOnly(True)
        self.deps_text.setFontFamily("Consolas")
        self.deps_text.setFontPointSize(9)
        deps_layout.addWidget(self.deps_text)
        tabs.addTab(deps_tab, "Dependencies")
        
        # Dependency Tree tab
        tree_tab = QWidget()
        tree_layout = QVBoxLayout(tree_tab)
        self.tree_text = QTextEdit(tree_tab)
        self.tree_text.setReadOnly(True)
        self.tree_text.setFontFamily("Consolas")
        self.tree_text.setFontPointSize(9)
        tree_layout.addWidget(self.tree_text)
        tabs.addTab(tree_tab, "Dependency Tree")
        
        # Outdated Packages tab
        outdated_tab = QWidget()
        outdated_layout = QVBoxLayout(outdated_tab)
        self.outdated_text = QTextEdit(outdated_tab)
        self.outdated_text.setReadOnly(True)
        self.outdated_text.setFontFamily("Consolas")
        self.outdated_text.setFontPointSize(9)
        outdated_layout.addWidget(self.outdated_text)
        tabs.addTab(outdated_tab, "Outdated Packages")
        
        layout.addWidget(tabs)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        refresh_btn = QPushButton("🔄 Refresh", self)
        refresh_btn.clicked.connect(self._analyze_dependencies)
        button_layout.addWidget(refresh_btn)
        
        check_outdated_btn = QPushButton("🔍 Check Outdated", self)
        check_outdated_btn.clicked.connect(self._check_outdated)
        button_layout.addWidget(check_outdated_btn)
        
        close_btn = QPushButton("Close", self)
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
    
    def _analyze_dependencies(self):
        """Analyze project dependencies."""
        if not self.project_path:
            QMessageBox.warning(self, "No Project", "Please select a project first.")
            return
        
        self.deps_text.clear()
        self.deps_text.append("Analyzing dependencies...\n")
        
        dep_info = self.dependency_service.analyze_dependencies(self.project_path)
        
        if "error" in dep_info:
            self.deps_text.append(f"❌ Error: {dep_info['error']}")
            return
        
        text = f"Project: {dep_info.get('project_name', 'Unknown')}\n"
        text += f"Version: {dep_info.get('project_version', 'Unknown')}\n"
        text += f"SDK Constraint: {dep_info.get('sdk_constraint', 'Not specified')}\n"
        text += f"Total Dependencies: {dep_info.get('total_dependencies', 0)}\n"
        text += "\n" + "=" * 60 + "\n\n"
        
        # Dependencies
        deps = dep_info.get("dependencies", [])
        if deps:
            text += "📦 Dependencies:\n"
            text += "-" * 60 + "\n"
            for dep in deps:
                text += f"  • {dep['name']}\n"
                text += f"    Version: {dep['version']}\n"
                if dep.get('type') == 'path':
                    text += f"    Type: Local Path ({dep.get('path', '')})\n"
                elif dep.get('type') == 'git':
                    text += f"    Type: Git ({dep.get('git', '')})\n"
                text += "\n"
        
        # Dev Dependencies
        dev_deps = dep_info.get("dev_dependencies", [])
        if dev_deps:
            text += "\n🔧 Dev Dependencies:\n"
            text += "-" * 60 + "\n"
            for dep in dev_deps:
                text += f"  • {dep['name']}\n"
                text += f"    Version: {dep['version']}\n"
                if dep.get('type') == 'path':
                    text += f"    Type: Local Path ({dep.get('path', '')})\n"
                elif dep.get('type') == 'git':
                    text += f"    Type: Git ({dep.get('git', '')})\n"
                text += "\n"
        
        self.deps_text.setPlainText(text)
        
        # Load dependency tree
        self._load_dependency_tree()
    
    def _load_dependency_tree(self):
        """Load dependency tree."""
        if not self.project_path:
            return
        
        self.tree_text.clear()
        self.tree_text.append("Loading dependency tree...\n")
        
        tree_output = self.dependency_service.get_dependency_tree(self.project_path)
        self.tree_text.setPlainText(tree_output)
    
    def _check_outdated(self):
        """Check for outdated packages."""
        if not self.project_path:
            QMessageBox.warning(self, "No Project", "Please select a project first.")
            return
        
        self.outdated_text.clear()
        self.outdated_text.append("Checking for outdated packages...\n")
        self.outdated_text.append("This may take a moment...\n\n")
        
        result = self.dependency_service.check_outdated_packages(self.project_path)
        
        if "error" in result:
            self.outdated_text.append(f"❌ Error: {result['error']}")
            return
        
        output = result.get("output", "")
        has_updates = result.get("has_updates", False)
        
        if has_updates:
            self.outdated_text.append("⚠️ Some packages can be updated!\n\n")
        else:
            self.outdated_text.append("✅ All packages are up to date (or check manually)\n\n")
        
        self.outdated_text.append("=" * 60 + "\n")
        self.outdated_text.append(output)

