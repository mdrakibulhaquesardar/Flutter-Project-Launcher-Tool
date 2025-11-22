"""SQLite database management for Flutter Project Launcher Tool."""
import sqlite3
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
from core.logger import Logger


class Database:
    """SQLite database manager for Flutter Project Launcher Tool."""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self.logger = Logger()
        self.db_dir = Path.home() / ".flutter_launcher" / "data"
        self.db_dir.mkdir(parents=True, exist_ok=True)
        self.db_file = self.db_dir / "flutter_launcher.db"
        self._initialized = True
        self._init_database()
        self._migrate_from_json()
    
    def _init_database(self):
        """Initialize database tables."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Settings table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Projects table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                path TEXT UNIQUE NOT NULL,
                flutter_version TEXT,
                flutter_sdk_constraint TEXT,
                fvm_enabled INTEGER DEFAULT 0,
                icon_path TEXT,
                last_modified TIMESTAMP,
                last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                metadata TEXT,
                tags TEXT DEFAULT '[]'
            )
        """)
        
        # SDKs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sdks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                path TEXT UNIQUE NOT NULL,
                version TEXT,
                channel TEXT,
                is_default INTEGER DEFAULT 0,
                is_managed INTEGER DEFAULT 0,
                installed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                metadata TEXT
            )
        """)
        
        # Templates table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                description TEXT,
                path TEXT,
                is_custom INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                metadata TEXT
            )
        """)
        
        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_projects_path ON projects(path)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_projects_last_accessed ON projects(last_accessed DESC)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sdks_path ON sdks(path)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sdks_is_default ON sdks(is_default)")
        
        conn.commit()
        conn.close()
        self.logger.info(f"Database initialized: {self.db_file}")
        
        # Run migrations
        self._migrate_tags_column()
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection."""
        conn = sqlite3.connect(str(self.db_file))
        conn.row_factory = sqlite3.Row  # Return rows as dict-like objects
        return conn
    
    def _migrate_tags_column(self):
        """Migrate tags column if it doesn't exist."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Check if tags column exists
            cursor.execute("PRAGMA table_info(projects)")
            columns = [row[1] for row in cursor.fetchall()]
            
            if 'tags' not in columns:
                self.logger.info("Adding tags column to projects table...")
                cursor.execute("ALTER TABLE projects ADD COLUMN tags TEXT DEFAULT '[]'")
                # Initialize existing projects with empty tags array
                cursor.execute("UPDATE projects SET tags = '[]' WHERE tags IS NULL")
                conn.commit()
                self.logger.info("Tags column migration completed")
            
            conn.close()
        except Exception as e:
            self.logger.error(f"Error migrating tags column: {e}")
    
    def _migrate_from_json(self):
        """Migrate data from JSON files to SQLite."""
        try:
            # Check if migration already done
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM settings WHERE key = 'migrated_from_json'")
            if cursor.fetchone():
                conn.close()
                return
            
            self.logger.info("Migrating data from JSON files to SQLite...")
            
            # Migrate settings - check multiple possible locations
            settings_file = None
            possible_locations = [
                Path("data/settings.json"),  # Development location
                Path.home() / ".flutter_launcher" / "data" / "settings.json",  # User data location
            ]
            for loc in possible_locations:
                if loc.exists():
                    settings_file = loc
                    break
            
            if settings_file and settings_file.exists():
                try:
                    with open(settings_file, 'r', encoding='utf-8') as f:
                        settings_data = json.load(f)
                    
                    for key, value in settings_data.items():
                        if isinstance(value, (dict, list)):
                            value = json.dumps(value)
                        cursor.execute(
                            "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                            (key, str(value))
                        )
                    self.logger.info("Migrated settings from JSON")
                except Exception as e:
                    self.logger.warning(f"Error migrating settings: {e}")
            
            # Migrate projects - check multiple possible locations
            projects_file = None
            possible_locations = [
                Path("data/projects.json"),  # Development location
                Path.home() / ".flutter_launcher" / "data" / "projects.json",  # User data location
            ]
            for loc in possible_locations:
                if loc.exists():
                    projects_file = loc
                    break
            
            if projects_file and projects_file.exists():
                try:
                    with open(projects_file, 'r', encoding='utf-8') as f:
                        projects_data = json.load(f)
                    
                    projects = projects_data.get("projects", [])
                    for project in projects:
                        metadata_json = json.dumps(project)
                        cursor.execute("""
                            INSERT OR REPLACE INTO projects 
                            (name, path, flutter_version, flutter_sdk_constraint, fvm_enabled, icon_path, last_modified, metadata)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            project.get("name", ""),
                            project.get("path", ""),
                            project.get("flutter_version"),
                            project.get("flutter_sdk_constraint"),
                            1 if project.get("fvm_enabled") else 0,
                            project.get("icon_path"),
                            project.get("last_modified"),
                            metadata_json
                        ))
                    self.logger.info(f"Migrated {len(projects)} projects from JSON")
                except Exception as e:
                    self.logger.warning(f"Error migrating projects: {e}")
            
            # Mark migration as done
            cursor.execute(
                "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                ("migrated_from_json", "true")
            )
            
            conn.commit()
            conn.close()
            self.logger.info("Migration completed successfully")
            
        except Exception as e:
            self.logger.error(f"Error during migration: {e}")
    
    # Settings methods
    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get setting value."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            value = row[0]
            # Try to parse as JSON if it looks like JSON
            try:
                parsed = json.loads(value)
                return parsed
            except:
                # Return as string if not JSON
                return value
        return default
    
    def set_setting(self, key: str, value: Any):
        """Set setting value."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Convert value to string/JSON
        if isinstance(value, (dict, list)):
            value_str = json.dumps(value, ensure_ascii=False)
        elif isinstance(value, bool):
            # Store bool as JSON true/false
            value_str = json.dumps(value)
        elif value is None:
            value_str = "null"
        else:
            value_str = str(value)
        
        cursor.execute(
            "INSERT OR REPLACE INTO settings (key, value, updated_at) VALUES (?, ?, CURRENT_TIMESTAMP)",
            (key, value_str)
        )
        conn.commit()
        conn.close()
    
    def delete_setting(self, key: str):
        """Delete setting."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM settings WHERE key = ?", (key,))
        conn.commit()
        conn.close()
    
    # Project methods
    def add_project(self, project_data: Dict[str, Any]) -> int:
        """Add or update project."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        metadata_json = json.dumps(project_data)
        
        # Get tags from project_data, default to empty list
        tags = project_data.get("tags", [])
        if not isinstance(tags, list):
            tags = []
        tags_json = json.dumps(tags)
        
        cursor.execute("""
            INSERT OR REPLACE INTO projects 
            (name, path, flutter_version, flutter_sdk_constraint, fvm_enabled, icon_path, last_modified, last_accessed, metadata, tags)
            VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, ?, ?)
        """, (
            project_data.get("name", ""),
            project_data.get("path", ""),
            project_data.get("flutter_version"),
            project_data.get("flutter_sdk_constraint"),
            1 if project_data.get("fvm_enabled") else 0,
            project_data.get("icon_path"),
            project_data.get("last_modified"),
            metadata_json,
            tags_json
        ))
        
        project_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return project_id
    
    def get_projects(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get recent projects."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        query = "SELECT * FROM projects ORDER BY last_accessed DESC"
        if limit:
            query += f" LIMIT {limit}"
        
        cursor.execute(query)
        rows = cursor.fetchall()
        conn.close()
        
        projects = []
        for row in rows:
            project = dict(row)
            # Parse metadata if available
            if project.get("metadata"):
                try:
                    metadata = json.loads(project["metadata"])
                    project.update(metadata)
                except:
                    pass
            # Parse tags if available
            if project.get("tags"):
                try:
                    tags = json.loads(project["tags"])
                    project["tags"] = tags if isinstance(tags, list) else []
                except:
                    project["tags"] = []
            else:
                project["tags"] = []
            projects.append(project)
        
        return projects
    
    def get_project_by_path(self, path: str) -> Optional[Dict[str, Any]]:
        """Get project by path."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM projects WHERE path = ?", (path,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            project = dict(row)
            if project.get("metadata"):
                try:
                    metadata = json.loads(project["metadata"])
                    project.update(metadata)
                except:
                    pass
            # Parse tags if available
            if project.get("tags"):
                try:
                    tags = json.loads(project["tags"])
                    project["tags"] = tags if isinstance(tags, list) else []
                except:
                    project["tags"] = []
            else:
                project["tags"] = []
            return project
        return None
    
    def update_project_access(self, path: str):
        """Update project last accessed time."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE projects SET last_accessed = CURRENT_TIMESTAMP WHERE path = ?",
            (path,)
        )
        conn.commit()
        conn.close()
    
    def delete_project(self, path: str):
        """Delete project."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM projects WHERE path = ?", (path,))
        conn.commit()
        conn.close()
    
    def update_project_tags(self, path: str, tags: List[str]):
        """Update project tags."""
        conn = self._get_connection()
        cursor = conn.cursor()
        tags_json = json.dumps(tags)
        cursor.execute(
            "UPDATE projects SET tags = ? WHERE path = ?",
            (tags_json, path)
        )
        conn.commit()
        conn.close()
    
    def get_projects_by_tag(self, tag: str) -> List[Dict[str, Any]]:
        """Get projects that have a specific tag."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Get all projects and filter by tag
        cursor.execute("SELECT * FROM projects ORDER BY last_accessed DESC")
        rows = cursor.fetchall()
        conn.close()
        
        projects = []
        for row in rows:
            project = dict(row)
            # Parse tags
            if project.get("tags"):
                try:
                    tags = json.loads(project["tags"])
                    if isinstance(tags, list) and tag in tags:
                        # Parse metadata if available
                        if project.get("metadata"):
                            try:
                                metadata = json.loads(project["metadata"])
                                project.update(metadata)
                            except:
                                pass
                        project["tags"] = tags
                        projects.append(project)
                except:
                    pass
        
        return projects
    
    def get_all_tags(self) -> List[str]:
        """Get all unique tags from all projects."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT tags FROM projects WHERE tags IS NOT NULL AND tags != '[]'")
        rows = cursor.fetchall()
        conn.close()
        
        all_tags = set()
        for row in rows:
            try:
                tags = json.loads(row[0])
                if isinstance(tags, list):
                    all_tags.update(tags)
            except:
                pass
        
        return sorted(list(all_tags))
    
    # SDK methods
    def add_sdk(self, sdk_data: Dict[str, Any]) -> int:
        """Add or update SDK."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        metadata_json = json.dumps(sdk_data)
        
        cursor.execute("""
            INSERT OR REPLACE INTO sdks 
            (path, version, channel, is_default, is_managed, metadata)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            sdk_data.get("path", ""),
            sdk_data.get("version"),
            sdk_data.get("channel", "stable"),
            1 if sdk_data.get("is_default") else 0,
            1 if sdk_data.get("is_managed") else 0,
            metadata_json
        ))
        
        # If this is default, unset others
        if sdk_data.get("is_default"):
            cursor.execute("UPDATE sdks SET is_default = 0 WHERE path != ?", (sdk_data.get("path"),))
        
        sdk_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return sdk_id
    
    def get_sdks(self) -> List[Dict[str, Any]]:
        """Get all SDKs."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM sdks ORDER BY is_default DESC, installed_at DESC")
        rows = cursor.fetchall()
        conn.close()
        
        sdks = []
        for row in rows:
            sdk = dict(row)
            if sdk.get("metadata"):
                try:
                    metadata = json.loads(sdk["metadata"])
                    sdk.update(metadata)
                except:
                    pass
            sdks.append(sdk)
        
        return sdks
    
    def get_default_sdk(self) -> Optional[Dict[str, Any]]:
        """Get default SDK."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM sdks WHERE is_default = 1 LIMIT 1")
        row = cursor.fetchone()
        conn.close()
        
        if row:
            sdk = dict(row)
            if sdk.get("metadata"):
                try:
                    metadata = json.loads(sdk["metadata"])
                    sdk.update(metadata)
                except:
                    pass
            return sdk
        return None
    
    def set_default_sdk(self, path: str):
        """Set default SDK."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE sdks SET is_default = 0")
        cursor.execute("UPDATE sdks SET is_default = 1 WHERE path = ?", (path,))
        conn.commit()
        conn.close()
    
    def delete_sdk(self, path: str):
        """Delete SDK."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM sdks WHERE path = ?", (path,))
        conn.commit()
        conn.close()
    
    # Template methods
    def add_template(self, template_data: Dict[str, Any]) -> int:
        """Add or update template."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        metadata_json = json.dumps(template_data)
        
        cursor.execute("""
            INSERT OR REPLACE INTO templates 
            (name, description, path, is_custom, metadata)
            VALUES (?, ?, ?, ?, ?)
        """, (
            template_data.get("name", ""),
            template_data.get("description"),
            template_data.get("path"),
            1 if template_data.get("is_custom") else 0,
            metadata_json
        ))
        
        template_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return template_id
    
    def get_templates(self) -> List[Dict[str, Any]]:
        """Get all templates."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM templates ORDER BY is_custom DESC, name")
        rows = cursor.fetchall()
        conn.close()
        
        templates = []
        for row in rows:
            template = dict(row)
            if template.get("metadata"):
                try:
                    metadata = json.loads(template["metadata"])
                    template.update(metadata)
                except:
                    pass
            templates.append(template)
        
        return templates
    
    def delete_template(self, name: str):
        """Delete template."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM templates WHERE name = ?", (name,))
        conn.commit()
        conn.close()
    
    def backup_database(self, backup_path: Optional[Path] = None) -> Path:
        """Backup database to file."""
        if backup_path is None:
            backup_path = self.db_dir / f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        
        import shutil
        shutil.copy2(self.db_file, backup_path)
        self.logger.info(f"Database backed up to: {backup_path}")
        return backup_path

