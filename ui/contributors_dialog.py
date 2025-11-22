"""Contributors dialog showing GitHub contributors."""
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QScrollArea, QWidget, QMessageBox,
                             QFrame, QTextEdit)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QPixmap, QIcon
from core.logger import Logger
from core.theme import Theme
from core.branding import Branding
import requests
from typing import List, Dict, Optional
from pathlib import Path
import webbrowser


class ContributorsLoadThread(QThread):
    """Thread for loading contributors from GitHub."""
    progress = pyqtSignal(str)
    contributors_loaded = pyqtSignal(list)
    error = pyqtSignal(str)
    
    def __init__(self, repo_owner: str, repo_name: str):
        super().__init__()
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.logger = Logger()
    
    def run(self):
        """Fetch contributors from GitHub API."""
        try:
            self.progress.emit("Loading contributors from GitHub...")
            
            # GitHub API endpoint for contributors
            api_url = f"https://api.github.com/repos/{self.repo_owner}/{self.repo_name}/contributors"
            
            headers = {
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "FluStudio"
            }
            
            contributors = []
            page = 1
            per_page = 100
            
            while True:
                params = {"page": page, "per_page": per_page}
                response = requests.get(api_url, headers=headers, params=params, timeout=10)
                
                if response.status_code != 200:
                    if page == 1:
                        self.error.emit(f"Failed to fetch contributors: {response.status_code}")
                        return
                    break
                
                page_contributors = response.json()
                if not page_contributors:
                    break
                
                contributors.extend(page_contributors)
                
                # Check if there are more pages
                if len(page_contributors) < per_page:
                    break
                
                page += 1
            
            # Sort by contributions (descending)
            contributors.sort(key=lambda x: x.get("contributions", 0), reverse=True)
            
            self.progress.emit(f"Loaded {len(contributors)} contributors")
            self.contributors_loaded.emit(contributors)
            
        except requests.exceptions.RequestException as e:
            self.error.emit(f"Network error: {str(e)}")
        except Exception as e:
            self.error.emit(f"Error loading contributors: {str(e)}")


class ContributorCard(QWidget):
    """Widget for displaying a single contributor."""
    
    def __init__(self, contributor_data: Dict, rank: int, parent=None):
        super().__init__(parent)
        self.contributor_data = contributor_data
        self.rank = rank
        self._init_ui()
    
    def _init_ui(self):
        """Initialize contributor card UI."""
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(15, 12, 15, 12)
        main_layout.setSpacing(15)
        
        # Rank badge
        rank_label = QLabel(f"#{self.rank}", self)
        rank_label.setFixedWidth(50)
        rank_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        rank_font = QFont()
        rank_font.setBold(True)
        rank_font.setPointSize(12)
        rank_label.setFont(rank_font)
        
        # Color rank badge based on position
        if self.rank == 1:
            rank_color = "#FFD700"  # Gold
        elif self.rank == 2:
            rank_color = "#C0C0C0"  # Silver
        elif self.rank == 3:
            rank_color = "#CD7F32"  # Bronze
        else:
            rank_color = Theme.PRIMARY
        
        rank_label.setStyleSheet(f"""
            QLabel {{
                background-color: {rank_color};
                color: white;
                border-radius: 25px;
                padding: 6px;
                font-weight: bold;
            }}
        """)
        main_layout.addWidget(rank_label)
        
        # Contributor info
        info_layout = QVBoxLayout()
        info_layout.setSpacing(6)
        info_layout.setContentsMargins(0, 0, 0, 0)
        
        # Username with GitHub icon
        username = self.contributor_data.get("login", "Unknown")
        username_layout = QHBoxLayout()
        username_layout.setContentsMargins(0, 0, 0, 0)
        username_layout.setSpacing(6)
        
        username_label = QLabel(f"@{username}", self)
        username_font = QFont()
        username_font.setBold(True)
        username_font.setPointSize(12)
        username_label.setFont(username_font)
        username_label.setStyleSheet(f"color: {Theme.PRIMARY};")
        username_layout.addWidget(username_label)
        username_layout.addStretch()
        
        info_layout.addLayout(username_layout)
        
        # Contributions info with icon
        contributions = self.contributor_data.get("contributions", 0)
        contributions_layout = QHBoxLayout()
        contributions_layout.setContentsMargins(0, 0, 0, 0)
        contributions_layout.setSpacing(8)
        
        contributions_icon = QLabel("📊", self)
        contributions_icon.setStyleSheet("font-size: 12pt;")
        contributions_layout.addWidget(contributions_icon)
        
        contributions_text = f"{contributions:,} contribution{'s' if contributions != 1 else ''}"
        contributions_label = QLabel(contributions_text, self)
        contributions_label.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 10pt;")
        contributions_layout.addWidget(contributions_label)
        contributions_layout.addStretch()
        
        info_layout.addLayout(contributions_layout)
        
        # Type (if available)
        user_type = self.contributor_data.get("type", "")
        if user_type:
            type_label = QLabel(f"Type: {user_type.title()}", self)
            type_label.setStyleSheet(f"color: {Theme.TEXT_MUTED}; font-size: 9pt;")
            info_layout.addWidget(type_label)
        
        info_layout.addStretch()
        main_layout.addLayout(info_layout, 1)
        
        # Action buttons
        button_layout = QVBoxLayout()
        button_layout.setSpacing(6)
        button_layout.setContentsMargins(0, 0, 0, 0)
        
        profile_url = self.contributor_data.get("html_url", "")
        if profile_url:
            profile_btn = QPushButton("👤 Profile", self)
            profile_btn.setMinimumWidth(110)
            profile_btn.setMaximumWidth(110)
            profile_btn.clicked.connect(lambda: webbrowser.open(profile_url))
            button_layout.addWidget(profile_btn)
            
            # Contributions link
            contributions_btn = QPushButton("📈 Stats", self)
            contributions_btn.setMinimumWidth(110)
            contributions_btn.setMaximumWidth(110)
            contributions_btn.clicked.connect(lambda: webbrowser.open(
                f"{profile_url}?tab=repositories"
            ))
            button_layout.addWidget(contributions_btn)
        
        button_layout.addStretch()
        main_layout.addLayout(button_layout)
        
        # Style
        self.setStyleSheet(f"""
            ContributorCard {{
                border: 1px solid {Theme.BORDER};
                border-radius: 8px;
                background-color: {Theme.SURFACE};
                margin: 2px;
            }}
            ContributorCard:hover {{
                background-color: {Theme.HOVER};
                border-color: {Theme.PRIMARY};
                border-width: 2px;
            }}
        """)


class ContributorsDialog(QDialog):
    """Dialog showing GitHub contributors."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = Logger()
        self.repo_owner = "mdrakibulhaquesardar"
        self.repo_name = "Flutter-Project-Launcher-Tool"
        self.load_thread: Optional[ContributorsLoadThread] = None
        
        self.setWindowTitle("Contributors")
        self.setMinimumSize(700, 600)
        
        # Apply branding
        Branding.apply_window_icon(self)
        
        self._init_ui()
        self._load_contributors()
    
    def _init_ui(self):
        """Initialize UI components."""
        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Header section with gradient-like effect
        header_widget = QWidget(self)
        header_widget.setStyleSheet(f"""
            QWidget {{
                background-color: {Theme.SURFACE};
                border-bottom: 2px solid {Theme.BORDER};
            }}
        """)
        header_layout = QVBoxLayout(header_widget)
        header_layout.setSpacing(10)
        header_layout.setContentsMargins(25, 20, 25, 20)
        
        # Title with icon
        title_layout = QHBoxLayout()
        title_layout.setSpacing(10)
        
        title_icon = QLabel("👥", self)
        title_icon.setStyleSheet("font-size: 24pt;")
        title_layout.addWidget(title_icon)
        
        title = QLabel("Contributors", self)
        title_font = QFont()
        title_font.setPointSize(20)
        title_font.setBold(True)
        title.setFont(title_font)
        title_layout.addWidget(title)
        title_layout.addStretch()
        
        header_layout.addLayout(title_layout)
        
        # Subtitle and stats
        subtitle_layout = QVBoxLayout()
        subtitle_layout.setSpacing(5)
        
        subtitle = QLabel(
            "Thank you to all contributors who have helped make this project better!",
            self
        )
        subtitle.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 10pt;")
        subtitle.setWordWrap(True)
        subtitle_layout.addWidget(subtitle)
        
        repo_label = QLabel(
            f"📦 Repository: {self.repo_owner}/{self.repo_name}",
            self
        )
        repo_label.setStyleSheet(f"color: {Theme.PRIMARY}; font-size: 9pt; font-weight: bold;")
        subtitle_layout.addWidget(repo_label)
        
        # Stats label (will be updated when contributors load)
        self.stats_label = QLabel("", self)
        self.stats_label.setStyleSheet(f"color: {Theme.TEXT_MUTED}; font-size: 9pt;")
        subtitle_layout.addWidget(self.stats_label)
        
        header_layout.addLayout(subtitle_layout)
        layout.addWidget(header_widget)
        
        # Contributors list section
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet(f"""
            QScrollArea {{
                border: none;
                background-color: {Theme.BACKGROUND if Theme.BACKGROUND else 'palette(window)'};
            }}
        """)
        
        self.contributors_widget = QWidget()
        self.contributors_layout = QVBoxLayout(self.contributors_widget)
        self.contributors_layout.setSpacing(12)
        self.contributors_layout.setContentsMargins(20, 15, 20, 15)
        
        scroll.setWidget(self.contributors_widget)
        layout.addWidget(scroll, 1)
        
        # Status label
        self.status_label = QLabel("Loading contributors from GitHub...", self)
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet(f"""
            color: {Theme.TEXT_SECONDARY}; 
            padding: 40px; 
            font-size: 11pt;
        """)
        self.contributors_layout.addWidget(self.status_label)
        self.contributors_layout.addStretch()
        
        # Footer with buttons
        footer_widget = QWidget(self)
        footer_widget.setStyleSheet(f"""
            QWidget {{
                background-color: {Theme.SURFACE};
                border-top: 1px solid {Theme.BORDER};
            }}
        """)
        button_layout = QHBoxLayout(footer_widget)
        button_layout.setContentsMargins(20, 12, 20, 12)
        button_layout.setSpacing(10)
        
        button_layout.addStretch()
        
        refresh_btn = QPushButton("🔄 Refresh", self)
        refresh_btn.setMinimumWidth(100)
        refresh_btn.clicked.connect(self._load_contributors)
        button_layout.addWidget(refresh_btn)
        
        github_btn = QPushButton("🌐 View on GitHub", self)
        github_btn.setMinimumWidth(140)
        github_btn.clicked.connect(lambda: webbrowser.open(
            f"https://github.com/{self.repo_owner}/{self.repo_name}/graphs/contributors"
        ))
        button_layout.addWidget(github_btn)
        
        close_btn = QPushButton("Close", self)
        close_btn.setMinimumWidth(100)
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)
        
        layout.addWidget(footer_widget)
    
    def _load_contributors(self):
        """Load contributors from GitHub."""
        # Clear existing contributors
        while self.contributors_layout.count():
            item = self.contributors_layout.takeAt(0)
            if item.widget():
                item.widget().setParent(None)
        
        # Show loading
        self.status_label = QLabel("Loading contributors from GitHub...", self)
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; padding: 20px;")
        self.contributors_layout.addWidget(self.status_label)
        self.contributors_layout.addStretch()
        
        # Stop any existing thread
        if self.load_thread and self.load_thread.isRunning():
            self.load_thread.terminate()
            self.load_thread.wait()
        
        # Start loading thread
        self.load_thread = ContributorsLoadThread(self.repo_owner, self.repo_name)
        self.load_thread.progress.connect(self._on_progress)
        self.load_thread.contributors_loaded.connect(self._on_contributors_loaded)
        self.load_thread.error.connect(self._on_error)
        self.load_thread.start()
    
    def _on_progress(self, message: str):
        """Handle progress updates."""
        if self.status_label:
            self.status_label.setText(message)
        self.logger.info(message)
    
    def _on_contributors_loaded(self, contributors: List[Dict]):
        """Handle contributors loaded."""
        # Remove status label
        if self.status_label:
            self.contributors_layout.removeWidget(self.status_label)
            self.status_label.setParent(None)
            self.status_label = None
        
        if not contributors:
            no_contributors = QLabel("No contributors found.", self)
            no_contributors.setAlignment(Qt.AlignmentFlag.AlignCenter)
            no_contributors.setStyleSheet(f"""
                color: {Theme.TEXT_SECONDARY}; 
                padding: 40px; 
                font-size: 11pt;
            """)
            self.contributors_layout.addWidget(no_contributors)
            self.contributors_layout.addStretch()
            return
        
        # Update stats
        total_contributions = sum(c.get("contributions", 0) for c in contributors)
        self.stats_label.setText(
            f"📊 {len(contributors)} contributor{'s' if len(contributors) != 1 else ''} • "
            f"{total_contributions:,} total contributions"
        )
        
        # Add contributors with rank
        for index, contributor in enumerate(contributors, start=1):
            card = ContributorCard(contributor, index, self.contributors_widget)
            self.contributors_layout.addWidget(card)
        
        self.contributors_layout.addStretch()
        self.logger.info(f"Displayed {len(contributors)} contributors")
    
    def _on_error(self, error_message: str):
        """Handle loading error."""
        if self.status_label:
            self.status_label.setText(f"Error: {error_message}\n\nPlease check your internet connection.")
            self.status_label.setStyleSheet(f"color: {Theme.ERROR}; padding: 20px;")
        
        self.logger.error(error_message)
        QMessageBox.warning(
            self,
            "Error Loading Contributors",
            f"Failed to load contributors:\n{error_message}\n\n"
            f"You can view contributors on GitHub:\n"
            f"https://github.com/{self.repo_owner}/{self.repo_name}/graphs/contributors"
        )

