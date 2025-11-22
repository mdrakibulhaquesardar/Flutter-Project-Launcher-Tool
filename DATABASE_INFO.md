# SQLite Database Implementation

## Overview
Flutter Project Launcher Tool now uses SQLite database for efficient data storage and management.

## Database Location
```
~/.flutter_launcher/data/flutter_launcher.db
```

## Database Schema

### 1. Settings Table
Stores application settings and preferences.

**Columns:**
- `key` (TEXT PRIMARY KEY) - Setting key
- `value` (TEXT) - Setting value (JSON for complex types)
- `updated_at` (TIMESTAMP) - Last update time

**Stored Settings:**
- `default_sdk` - Default Flutter SDK path
- `default_project_location` - Default project creation location
- `theme` - UI theme (light/dark)
- `auto_scan` - Auto-scan on startup
- `scan_paths` - List of scan paths
- `window_geometry` - Window position/size
- `window_state` - Window state
- `flutter_sdks` - List of Flutter SDK paths

### 2. Projects Table
Stores recent Flutter projects metadata.

**Columns:**
- `id` (INTEGER PRIMARY KEY AUTOINCREMENT)
- `name` (TEXT) - Project name
- `path` (TEXT UNIQUE) - Project path
- `flutter_version` (TEXT) - Flutter SDK version
- `flutter_sdk_constraint` (TEXT) - SDK constraint from pubspec.yaml
- `fvm_enabled` (INTEGER) - FVM usage flag
- `icon_path` (TEXT) - Project icon path
- `last_modified` (TIMESTAMP) - Last modification time
- `last_accessed` (TIMESTAMP) - Last access time
- `created_at` (TIMESTAMP) - Creation time
- `metadata` (TEXT) - JSON metadata

**Indexes:**
- `idx_projects_path` - On path column
- `idx_projects_last_accessed` - On last_accessed DESC

### 3. SDKs Table
Stores Flutter SDK metadata.

**Columns:**
- `id` (INTEGER PRIMARY KEY AUTOINCREMENT)
- `path` (TEXT UNIQUE) - SDK path
- `version` (TEXT) - SDK version
- `channel` (TEXT) - Release channel (stable/beta/dev)
- `is_default` (INTEGER) - Default SDK flag
- `is_managed` (INTEGER) - Managed by tool flag
- `installed_at` (TIMESTAMP) - Installation time
- `metadata` (TEXT) - JSON metadata

**Indexes:**
- `idx_sdks_path` - On path column
- `idx_sdks_is_default` - On is_default column

### 4. Templates Table
Stores Flutter project templates.

**Columns:**
- `id` (INTEGER PRIMARY KEY AUTOINCREMENT)
- `name` (TEXT UNIQUE) - Template name/ID
- `description` (TEXT) - Template description
- `path` (TEXT) - Template path
- `is_custom` (INTEGER) - Custom template flag
- `created_at` (TIMESTAMP) - Creation time
- `metadata` (TEXT) - JSON metadata

## Features

### Automatic Migration
- Automatically migrates data from JSON files on first run
- Preserves existing data
- One-time migration (marked with `migrated_from_json` setting)

### Backward Compatibility
- JSON files are still updated for backward compatibility
- Can fallback to JSON if database is unavailable
- Both storage methods work simultaneously

### Database Operations

#### Settings
- `get_setting(key, default)` - Get setting value
- `set_setting(key, value)` - Set setting value
- `delete_setting(key)` - Delete setting

#### Projects
- `add_project(project_data)` - Add/update project
- `get_projects(limit)` - Get recent projects (sorted by last_accessed)
- `get_project_by_path(path)` - Get project by path
- `update_project_access(path)` - Update last accessed time
- `delete_project(path)` - Delete project

#### SDKs
- `add_sdk(sdk_data)` - Add/update SDK
- `get_sdks()` - Get all SDKs
- `get_default_sdk()` - Get default SDK
- `set_default_sdk(path)` - Set default SDK
- `delete_sdk(path)` - Delete SDK

#### Templates
- `add_template(template_data)` - Add/update template
- `get_templates()` - Get all templates
- `delete_template(name)` - Delete template

### Backup
- `backup_database(backup_path)` - Backup database to file
- Automatic timestamped backups

## Benefits

1. **Performance**: Faster queries and updates
2. **Reliability**: ACID transactions
3. **Scalability**: Handles large datasets efficiently
4. **Querying**: Easy filtering and sorting
5. **Relationships**: Can add foreign keys if needed
6. **Indexing**: Fast lookups on common fields

## Usage Example

```python
from core.database import Database

db = Database()

# Get setting
default_sdk = db.get_setting("default_sdk")

# Set setting
db.set_setting("theme", "dark")

# Add project
project_data = {
    "name": "MyApp",
    "path": "/path/to/project",
    "flutter_version": "3.24.0"
}
db.add_project(project_data)

# Get projects
projects = db.get_projects(limit=10)

# Backup database
backup_path = db.backup_database()
```

