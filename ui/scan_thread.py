"""Background thread for scanning Flutter projects."""
from PyQt6.QtCore import QThread, pyqtSignal
from services.project_service import ProjectService
from typing import List, Dict, Any


class ScanProjectsThread(QThread):
    """Thread for async project scanning."""
    progress = pyqtSignal(str)  # Progress message
    found_project = pyqtSignal(dict)  # Found project metadata
    finished = pyqtSignal(int)  # Number of projects found
    
    def __init__(self, search_paths: List[str], max_depth: int = 3):
        super().__init__()
        self.search_paths = search_paths
        self.max_depth = max_depth
        self.project_service = ProjectService()
    
    def run(self):
        """Execute project scanning."""
        found_count = 0
        
        for search_path in self.search_paths:
            self.progress.emit(f"Scanning: {search_path}")
            found_projects = self.project_service.scan_projects(
                [search_path], 
                max_depth=self.max_depth
            )
            
            for project in found_projects:
                project_path = project.get("path")
                if project_path:
                    # Add project to recent list
                    self.project_service.add_project(project_path)
                    self.found_project.emit(project)
                    found_count += 1
        
        self.progress.emit(f"Scan complete. Found {found_count} project(s)")
        self.finished.emit(found_count)

