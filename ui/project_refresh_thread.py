"""Background thread for refreshing project versions in parallel."""
from PyQt6.QtCore import QThread, pyqtSignal, QMutex, QWaitCondition
from services.project_service import ProjectService
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading


class ProjectRefreshThread(QThread):
    """Thread for parallel project version refreshing."""
    progress = pyqtSignal(str)  # Progress message
    project_updated = pyqtSignal(dict)  # Single project updated
    finished = pyqtSignal(list)  # All projects updated
    error = pyqtSignal(str)  # Error message
    
    def __init__(self, projects: List[Dict[str, Any]], max_workers: int = 4):
        super().__init__()
        self.projects = projects
        self.max_workers = max_workers
        self.project_service = ProjectService()
        self.lock = threading.Lock()
        self.updated_projects = []
    
    def _refresh_single_project(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """Refresh metadata for a single project."""
        project_path = project_data.get("path")
        if not project_path:
            return project_data
        
        try:
            # Update metadata with current Flutter version
            updated_metadata = self.project_service.get_project_metadata(project_path)
            project_data.update(updated_metadata)
            # Save updated project
            self.project_service.add_project(project_path)
            return project_data
        except Exception as e:
            # Return original data if refresh fails
            return project_data
    
    def run(self):
        """Execute parallel project refreshing."""
        try:
            if not self.projects:
                self.finished.emit([])
                return
            
            self.progress.emit(f"Refreshing Flutter SDK versions for {len(self.projects)} projects...")
            
            # Use ThreadPoolExecutor for parallel processing
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # Submit all tasks
                future_to_project = {
                    executor.submit(self._refresh_single_project, project): project 
                    for project in self.projects
                }
                
                # Process completed tasks
                completed = 0
                total = len(self.projects)
                
                for future in as_completed(future_to_project):
                    completed += 1
                    project = future_to_project[future]
                    
                    try:
                        updated_project = future.result()
                        with self.lock:
                            self.updated_projects.append(updated_project)
                        
                        project_name = updated_project.get('name', 'Unknown')
                        self.progress.emit(f"Refreshed {completed}/{total}: {project_name}")
                        self.project_updated.emit(updated_project)
                    except Exception as e:
                        # Use original project data if update failed
                        with self.lock:
                            self.updated_projects.append(project)
                        self.project_updated.emit(project)
            
            # Sort by original order
            project_paths = {p.get("path"): i for i, p in enumerate(self.projects)}
            self.updated_projects.sort(key=lambda p: project_paths.get(p.get("path"), 999))
            
            self.progress.emit(f"Refreshed {len(self.updated_projects)} project(s)")
            self.finished.emit(self.updated_projects)
        except Exception as e:
            self.error.emit(f"Error refreshing projects: {str(e)}")
            self.finished.emit(self.projects)

