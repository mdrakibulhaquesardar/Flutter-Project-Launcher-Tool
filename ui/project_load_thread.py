"""Background thread for loading projects list."""
from PyQt6.QtCore import QThread, pyqtSignal
from services.project_service import ProjectService
from typing import List, Dict, Any


class ProjectLoadThread(QThread):
    """Thread for async project list loading."""
    progress = pyqtSignal(str)  # Progress message
    project_loaded = pyqtSignal(dict)  # Single project loaded
    finished = pyqtSignal(list)  # All projects loaded
    error = pyqtSignal(str)  # Error message
    
    def __init__(self, refresh_versions: bool = False):
        super().__init__()
        self.refresh_versions = refresh_versions
        self.project_service = ProjectService()
    
    def run(self):
        """Execute project loading."""
        try:
            self.progress.emit("Loading projects from database...")
            projects = self.project_service.load_recent_projects()
            
            if not projects:
                self.finished.emit([])
                return
            
            # If refresh_versions is True, update metadata for each project
            if self.refresh_versions:
                self.progress.emit(f"Refreshing Flutter SDK versions for {len(projects)} projects...")
                updated_projects = []
                
                for i, project_data in enumerate(projects):
                    project_path = project_data.get("path")
                    if project_path:
                        try:
                            self.progress.emit(f"Refreshing {i+1}/{len(projects)}: {project_data.get('name', 'Unknown')}")
                            # Update metadata with current Flutter version
                            updated_metadata = self.project_service.get_project_metadata(project_path)
                            project_data.update(updated_metadata)
                            # Save updated project
                            self.project_service.add_project(project_path)
                            updated_projects.append(project_data)
                            # Emit each project as it's loaded
                            self.project_loaded.emit(project_data)
                        except Exception as e:
                            # Continue with original data if refresh fails
                            updated_projects.append(project_data)
                            self.project_loaded.emit(project_data)
                projects = updated_projects
            else:
                # Emit projects one by one for progressive loading
                for project_data in projects:
                    self.project_loaded.emit(project_data)
            
            self.progress.emit(f"Loaded {len(projects)} project(s)")
            self.finished.emit(projects)
        except Exception as e:
            self.error.emit(f"Error loading projects: {str(e)}")
            self.finished.emit([])

