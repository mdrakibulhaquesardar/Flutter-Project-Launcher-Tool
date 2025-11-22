"""Command console widget for Flutter Project Launcher Tool."""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QPlainTextEdit, QPushButton, 
                             QHBoxLayout, QMenu, QMessageBox)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import (QTextCharFormat, QColor, QTextCursor, QSyntaxHighlighter, 
                        QTextDocument, QKeySequence, QShortcut, QAction)
from typing import Optional
import re
from datetime import datetime


class LogSyntaxHighlighter(QSyntaxHighlighter):
    """Syntax highlighter for Flutter console logs."""
    
    def __init__(self, parent: Optional[QTextDocument] = None):
        super().__init__(parent)
        self._setup_rules()
    
    def _setup_rules(self):
        """Setup syntax highlighting rules."""
        self.highlighting_rules = []
        
        # Error patterns
        error_patterns = [
            r'\b(error|Error|ERROR|failed|Failed|FAILED|exception|Exception|EXCEPTION)\b',
            r'\[ERROR\]',
            r'✗',
            r'FAILURE',
        ]
        error_format = QTextCharFormat()
        error_format.setForeground(QColor(220, 50, 47))  # Red
        error_format.setFontWeight(600)
        for pattern in error_patterns:
            self.highlighting_rules.append((pattern, error_format))
        
        # Warning patterns
        warning_patterns = [
            r'\b(warning|Warning|WARNING|warn|Warn|WARN)\b',
            r'\[WARNING\]',
            r'⚠',
        ]
        warning_format = QTextCharFormat()
        warning_format.setForeground(QColor(203, 75, 22))  # Orange
        for pattern in warning_patterns:
            self.highlighting_rules.append((pattern, warning_format))
        
        # Success patterns
        success_patterns = [
            r'\b(success|Success|SUCCESS|succeeded|Succeeded|SUCCEEDED|done|Done|DONE)\b',
            r'\[SUCCESS\]',
            r'✓',
            r'BUILD SUCCESSFUL',
        ]
        success_format = QTextCharFormat()
        success_format.setForeground(QColor(133, 153, 0))  # Green
        for pattern in success_patterns:
            self.highlighting_rules.append((pattern, success_format))
        
        # Flutter command patterns
        flutter_format = QTextCharFormat()
        flutter_format.setForeground(QColor(97, 175, 239))  # Blue
        flutter_format.setFontWeight(500)
        self.highlighting_rules.append((r'\bflutter\s+\w+', flutter_format))
        self.highlighting_rules.append((r'\bfvm\s+\w+', flutter_format))
        
        # Version numbers
        version_format = QTextCharFormat()
        version_format.setForeground(QColor(152, 195, 121))  # Light green
        self.highlighting_rules.append((r'\b\d+\.\d+\.\d+', version_format))
        
        # File paths (Windows and Unix)
        path_format = QTextCharFormat()
        path_format.setForeground(QColor(209, 154, 102))  # Brown/orange
        self.highlighting_rules.append((r'[A-Z]:\\[^\s]+', path_format))  # Windows paths
        self.highlighting_rules.append((r'/[\w/\.-]+', path_format))  # Unix paths
        
        # URLs
        url_format = QTextCharFormat()
        url_format.setForeground(QColor(86, 182, 194))  # Cyan
        url_format.setUnderlineStyle(QTextCharFormat.UnderlineStyle.SingleUnderline)
        self.highlighting_rules.append((r'https?://[^\s]+', url_format))
        
        # Timestamps
        timestamp_format = QTextCharFormat()
        timestamp_format.setForeground(QColor(127, 132, 142))  # Gray
        self.highlighting_rules.append((r'\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}', timestamp_format))
    
    def highlightBlock(self, text: str):
        """Apply syntax highlighting to a block of text."""
        for pattern, format in self.highlighting_rules:
            expression = re.compile(pattern, re.IGNORECASE)
            for match in expression.finditer(text):
                start, end = match.span()
                self.setFormat(start, end - start, format)


class CommandConsole(QWidget):
    """Enhanced console widget with syntax highlighting and VS Code-like features."""
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._init_ui()
        self._setup_highlighting()
        self._setup_context_menu()
        self._setup_shortcuts()
        self.auto_scroll_enabled = True
    
    def _init_ui(self):
        """Initialize UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        
        # Use QPlainTextEdit for better performance with large logs
        self.console = QPlainTextEdit(self)
        self.console.setReadOnly(True)
        
        # Set font using QFont
        from PyQt6.QtGui import QFont
        font = QFont("Consolas", 9)
        self.console.setFont(font)
        self.console.setStyleSheet("""
            QPlainTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: 1px solid #3c3c3c;
                selection-background-color: #264f78;
            }
        """)
        
        # Set up syntax highlighter
        self.highlighter = LogSyntaxHighlighter(self.console.document())
        
        layout.addWidget(self.console)
        
        # Button bar
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(4, 4, 4, 4)
        button_layout.addStretch()
        
        # Copy button
        self.copy_btn = QPushButton("📋 Copy", self)
        self.copy_btn.setToolTip("Copy selected text (Ctrl+C)")
        self.copy_btn.clicked.connect(self.copy_selection)
        button_layout.addWidget(self.copy_btn)
        
        # Clear button
        self.clear_btn = QPushButton("🗑️ Clear", self)
        self.clear_btn.clicked.connect(self.clear)
        button_layout.addWidget(self.clear_btn)
        
        # Export button
        self.export_btn = QPushButton("💾 Export", self)
        self.export_btn.setToolTip("Export log to file")
        self.export_btn.clicked.connect(self.export_log)
        button_layout.addWidget(self.export_btn)
        
        layout.addLayout(button_layout)
        
        # Connect scrollbar to track auto-scroll state
        self.console.verticalScrollBar().valueChanged.connect(self._on_scroll_changed)
    
    def _setup_highlighting(self):
        """Setup text formatting for errors and warnings."""
        # Base formats (used for manual formatting)
        self.error_format = QTextCharFormat()
        self.error_format.setForeground(QColor(220, 50, 47))  # Red
        self.error_format.setFontWeight(600)
        
        self.warning_format = QTextCharFormat()
        self.warning_format.setForeground(QColor(203, 75, 22))  # Orange
        
        self.success_format = QTextCharFormat()
        self.success_format.setForeground(QColor(133, 153, 0))  # Green
        
        self.info_format = QTextCharFormat()
        self.info_format.setForeground(QColor(97, 175, 239))  # Blue
    
    def _setup_context_menu(self):
        """Setup right-click context menu."""
        self.console.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.console.customContextMenuRequested.connect(self._show_context_menu)
    
    def _show_context_menu(self, position):
        """Show context menu at cursor position."""
        menu = QMenu(self)
        
        # Copy action
        copy_action = QAction("📋 Copy", self)
        copy_action.setShortcut(QKeySequence.StandardKey.Copy)
        copy_action.triggered.connect(self.copy_selection)
        copy_action.setEnabled(self.console.textCursor().hasSelection())
        menu.addAction(copy_action)
        
        # Copy All action
        copy_all_action = QAction("📋 Copy All", self)
        copy_all_action.triggered.connect(self.copy_all)
        menu.addAction(copy_all_action)
        
        menu.addSeparator()
        
        # Select All action
        select_all_action = QAction("Select All", self)
        select_all_action.setShortcut(QKeySequence.StandardKey.SelectAll)
        select_all_action.triggered.connect(self.console.selectAll)
        menu.addAction(select_all_action)
        
        menu.addSeparator()
        
        # Clear action
        clear_action = QAction("🗑️ Clear", self)
        clear_action.triggered.connect(self.clear)
        menu.addAction(clear_action)
        
        menu.addSeparator()
        
        # Export action
        export_action = QAction("💾 Export Log...", self)
        export_action.triggered.connect(self.export_log)
        menu.addAction(export_action)
        
        menu.exec(self.console.mapToGlobal(position))
    
    def _setup_shortcuts(self):
        """Setup keyboard shortcuts."""
        # Copy shortcut
        copy_shortcut = QShortcut(QKeySequence.StandardKey.Copy, self.console)
        copy_shortcut.activated.connect(self.copy_selection)
        
        # Select All shortcut
        select_all_shortcut = QShortcut(QKeySequence.StandardKey.SelectAll, self.console)
        select_all_shortcut.activated.connect(self.console.selectAll)
    
    def _on_scroll_changed(self, value):
        """Track if user manually scrolled (disable auto-scroll)."""
        scrollbar = self.console.verticalScrollBar()
        max_value = scrollbar.maximum()
        # If user scrolled away from bottom, disable auto-scroll
        if value < max_value - 10:  # 10px threshold
            self.auto_scroll_enabled = False
        # If user scrolled back to bottom, re-enable auto-scroll
        elif value >= max_value - 10:
            self.auto_scroll_enabled = True
    
    def _auto_scroll(self):
        """Auto-scroll to bottom if enabled."""
        if self.auto_scroll_enabled:
            scrollbar = self.console.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())
    
    def append(self, text: str, is_error: bool = False, is_warning: bool = False, 
               is_success: bool = False, is_info: bool = False):
        """Append text to console with optional formatting."""
        cursor = self.console.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        
        # Apply format if specified (syntax highlighter will also apply patterns)
        if is_error:
            cursor.setCharFormat(self.error_format)
        elif is_warning:
            cursor.setCharFormat(self.warning_format)
        elif is_success:
            cursor.setCharFormat(self.success_format)
        elif is_info:
            cursor.setCharFormat(self.info_format)
        
        cursor.insertText(text)
        cursor.insertText("\n")
        self.console.setTextCursor(cursor)
        
        # Auto-scroll to bottom
        QTimer.singleShot(10, self._auto_scroll)  # Small delay for better performance
    
    def append_error(self, text: str):
        """Append error message."""
        self.append(text, is_error=True)
    
    def append_warning(self, text: str):
        """Append warning message."""
        self.append(text, is_warning=True)
    
    def append_success(self, text: str):
        """Append success message."""
        self.append(text, is_success=True)
    
    def append_info(self, text: str):
        """Append info message."""
        self.append(text, is_info=True)
    
    def clear(self):
        """Clear console content."""
        self.console.clear()
        self.auto_scroll_enabled = True
    
    def copy_selection(self):
        """Copy selected text to clipboard."""
        cursor = self.console.textCursor()
        if cursor.hasSelection():
            text = cursor.selectedText()
            from PyQt6.QtWidgets import QApplication
            QApplication.clipboard().setText(text)
            self.append_info("Copied to clipboard")
    
    def copy_all(self):
        """Copy all console text to clipboard."""
        text = self.console.toPlainText()
        if text:
            from PyQt6.QtWidgets import QApplication
            QApplication.clipboard().setText(text)
            self.append_info("All text copied to clipboard")
    
    def export_log(self):
        """Export log to file."""
        from PyQt6.QtWidgets import QFileDialog
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_filename = f"flutter_log_{timestamp}.txt"
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, 
            "Export Log", 
            default_filename,
            "Text Files (*.txt);;Log Files (*.log);;All Files (*)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.console.toPlainText())
                self.append_success(f"✓ Log exported to: {file_path}")
            except Exception as e:
                self.append_error(f"✗ Error exporting log: {e}")
    
    def save_log(self):
        """Alias for export_log (backward compatibility)."""
        self.export_log()
    
    def get_text(self) -> str:
        """Get console text content."""
        return self.console.toPlainText()
    
    def set_auto_scroll(self, enabled: bool):
        """Enable/disable auto-scroll."""
        self.auto_scroll_enabled = enabled
        if enabled:
            self._auto_scroll()


