"""Template management service for Flutter Project Launcher Tool."""
import json
import zipfile
import shutil
from pathlib import Path
from typing import List, Dict, Optional, Any
from core.logger import Logger
from utils.file_utils import read_json, write_json, ensure_directory


class TemplateService:
    """Service for Flutter project templates."""
    
    def __init__(self):
        self.logger = Logger()
        self.templates_dir = Path("data/templates")
        ensure_directory(str(self.templates_dir))
        self.metadata_file = self.templates_dir / "templates.json"
        from core.database import Database
        self.db = Database()
        self._initialize_default_templates()
    
    def _initialize_default_templates(self):
        """Initialize default template metadata."""
        if not self.metadata_file.exists():
            default_templates = {
                "templates": [
                    {
                        "id": "default",
                        "name": "Default Flutter App",
                        "description": "Standard Flutter counter app template",
                        "type": "builtin"
                    },
                    {
                        "id": "mvvm",
                        "name": "MVVM Architecture",
                        "description": "Flutter project with MVVM pattern",
                        "type": "custom"
                    },
                    {
                        "id": "clean",
                        "name": "Clean Architecture",
                        "description": "Flutter project with Clean Architecture",
                        "type": "custom"
                    },
                    {
                        "id": "getx",
                        "name": "GetX Template",
                        "description": "Flutter project with GetX state management",
                        "type": "custom"
                    }
                ]
            }
            write_json(str(self.metadata_file), default_templates)
    
    def get_templates(self) -> List[Dict[str, Any]]:
        """Get all available templates."""
        # Load from database first
        db_templates = self.db.get_templates()
        
        if db_templates:
            templates = []
            for t in db_templates:
                template = {
                    "id": t.get("name", ""),
                    "name": t.get("name", ""),
                    "description": t.get("description", ""),
                    "type": "custom" if t.get("is_custom") else "builtin",
                    "path": t.get("path"),
                    "exists": Path(t.get("path", "")).exists() if t.get("path") else True
                }
                templates.append(template)
            return templates
        
        # Fallback to JSON
        data = read_json(str(self.metadata_file))
        templates = data.get("templates", [])
        
        # Check which custom templates actually exist
        for template in templates:
            if template.get("type") == "custom":
                template_path = self.templates_dir / template.get("id")
                template["exists"] = template_path.exists()
            else:
                template["exists"] = True
        
        # Migrate to database
        for template in templates:
            template_data = {
                "name": template.get("id", template.get("name", "")),
                "description": template.get("description", ""),
                "path": template.get("path", str(self.templates_dir / template.get("id", ""))),
                "is_custom": template.get("type") == "custom"
            }
            self.db.add_template(template_data)
        
        return templates
    
    def get_template(self, template_id: str) -> Optional[Dict[str, Any]]:
        """Get template by ID."""
        templates = self.get_templates()
        for template in templates:
            if template.get("id") == template_id:
                return template
        return None
    
    def add_template(self, template_id: str, name: str, description: str, 
                    source_path: str) -> bool:
        """Add a custom template from a source directory."""
        try:
            template_dir = self.templates_dir / template_id
            ensure_directory(str(template_dir))
            
            # Copy template files
            shutil.copytree(source_path, template_dir, dirs_exist_ok=True)
            
            # Add to database
            template_data = {
                "name": template_id,
                "description": description,
                "path": str(template_dir),
                "is_custom": True
            }
            self.db.add_template(template_data)
            
            # Also update JSON for backward compatibility
            data = read_json(str(self.metadata_file))
            templates = data.get("templates", [])
            templates = [t for t in templates if t.get("id") != template_id]
            templates.append({
                "id": template_id,
                "name": name,
                "description": description,
                "type": "custom",
                "path": str(template_dir)
            })
            data["templates"] = templates
            write_json(str(self.metadata_file), data)
            
            self.logger.info(f"Added template: {template_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error adding template: {e}")
            return False
    
    def remove_template(self, template_id: str) -> bool:
        """Remove a custom template."""
        try:
            template_dir = self.templates_dir / template_id
            if template_dir.exists():
                shutil.rmtree(template_dir)
            
            # Remove from database
            self.db.delete_template(template_id)
            
            # Also update JSON for backward compatibility
            data = read_json(str(self.metadata_file))
            templates = data.get("templates", [])
            templates = [t for t in templates if t.get("id") != template_id]
            data["templates"] = templates
            write_json(str(self.metadata_file), data)
            
            self.logger.info(f"Removed template: {template_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error removing template: {e}")
            return False
    
    def export_template(self, template_id: str, output_path: str) -> bool:
        """Export template as ZIP file."""
        try:
            template = self.get_template(template_id)
            if not template or template.get("type") == "builtin":
                return False
            
            template_dir = self.templates_dir / template_id
            if not template_dir.exists():
                return False
            
            with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file_path in template_dir.rglob('*'):
                    if file_path.is_file():
                        arcname = file_path.relative_to(template_dir)
                        zipf.write(file_path, arcname)
            
            self.logger.info(f"Exported template {template_id} to {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error exporting template: {e}")
            return False
    
    def import_template(self, zip_path: str) -> bool:
        """Import template from ZIP file."""
        try:
            with zipfile.ZipFile(zip_path, 'r') as zipf:
                # Read metadata if available
                if 'template.json' in zipf.namelist():
                    metadata_str = zipf.read('template.json').decode('utf-8')
                    metadata = json.loads(metadata_str)
                    template_id = metadata.get("id", Path(zip_path).stem)
                    name = metadata.get("name", template_id)
                    description = metadata.get("description", "")
                else:
                    template_id = Path(zip_path).stem
                    name = template_id
                    description = ""
                
                # Extract to templates directory
                template_dir = self.templates_dir / template_id
                ensure_directory(str(template_dir))
                zipf.extractall(template_dir)
                
                # Add to metadata
                data = read_json(str(self.metadata_file))
                templates = data.get("templates", [])
                
                templates = [t for t in templates if t.get("id") != template_id]
                templates.append({
                    "id": template_id,
                    "name": name,
                    "description": description,
                    "type": "custom",
                    "path": str(template_dir)
                })
                
                data["templates"] = templates
                write_json(str(self.metadata_file), data)
                
                self.logger.info(f"Imported template: {template_id}")
                return True
                
        except Exception as e:
            self.logger.error(f"Error importing template: {e}")
            return False


