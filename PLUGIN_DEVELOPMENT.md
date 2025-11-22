# Plugin Development Guide

This guide explains how to create plugins for the Flutter Project Launcher Tool.

## Plugin Structure

Each plugin is a folder containing:

```
plugin_name/
├── plugin.json      # Plugin metadata (required)
├── main.py          # Plugin entry point (required)
└── resources/       # Optional resources (icons, templates, etc.)
```

## plugin.json Schema

The `plugin.json` file defines plugin metadata:

```json
{
  "name": "Plugin Display Name",
  "id": "unique_plugin_id",
  "version": "1.0.0",
  "author": "Your Name",
  "description": "Plugin description",
  "plugin_type": "architecture|template|tool|general",
  "entry": "main.py",
  "py_dependencies": [],
  "enabled": true,
  "min_app_version": "1.0.0"
}
```

### Required Fields

- `name`: Display name of the plugin
- `id`: Unique identifier (lowercase, underscores, no spaces)
- `version`: Semantic version (e.g., "1.0.0")
- `entry`: Entry point file (usually "main.py")

### Optional Fields

- `author`: Plugin author name
- `description`: Plugin description
- `plugin_type`: Type of plugin (architecture, template, tool, general)
- `py_dependencies`: List of Python dependencies (not currently auto-installed)
- `enabled`: Whether plugin is enabled by default (default: true)
- `min_app_version`: Minimum app version required

## Plugin Entry Point

The entry point file (usually `main.py`) must define an `initialize()` function:

```python
def initialize(api):
    """Initialize plugin."""
    # Register templates, architectures, tool actions, etc.
    api.register_architecture("my_arch", my_architecture_generator)
    api.get_logger().info("Plugin initialized")
```

## Plugin API

The `PluginAPI` class provides methods for plugins to interact with the app:

### Registering Templates

```python
def my_template_generator(api, project_path: str, **kwargs):
    # Generate template files
    pass

api.register_template("my_template", my_template_generator)
```

### Registering Architectures

```python
def my_architecture_generator(api, project_path: str, **kwargs):
    # Generate architecture structure
    pass

api.register_architecture("my_arch", my_architecture_generator)
```

### Registering Tool Actions

```python
def my_tool_action(api):
    # Execute tool action
    pass

api.register_tool_action("My Tool", "icon_path", my_tool_action)
```

### Registering Menu Items

```python
def my_menu_action(api):
    # Execute menu action
    pass

api.add_menu_item("Tools", "My Menu Item", my_menu_action)
```

### Accessing Services

```python
# Get services
project_service = api.get_project_service()
flutter_service = api.get_flutter_service()
logger = api.get_logger()

# Access settings
value = api.get_setting("key", default_value)
api.set_setting("key", value)

# Show messages
api.show_message("Title", "Message", "info")  # info, warning, error, question
```

## Plugin Types

### Architecture Plugins

Generate folder structures and boilerplate code:

```python
def generate_architecture(api, project_path: str, **kwargs):
    from pathlib import Path
    project = Path(project_path)
    
    # Create directory structure
    (project / "lib" / "features").mkdir(parents=True, exist_ok=True)
    
    api.get_logger().info("Architecture generated")
```

### Template Plugins

Generate project templates:

```python
def generate_template(api, project_path: str, **kwargs):
    # Create template files
    pass
```

### Tool Plugins

Add CLI-like tools accessible from the UI:

```python
def my_tool(api):
    from PyQt6.QtWidgets import QFileDialog
    
    path = QFileDialog.getExistingDirectory(None, "Select Directory")
    if path:
        # Process directory
        pass
```

## Example Plugins

### Clean Architecture Generator

See `plugins/clean_arch/` for a complete example.

### GetX Architecture Generator

See `plugins/getx_generator/` for a complete example.

### Build APK Shortcut

See `plugins/build_apk/` for a complete example.

### Flutter Fire Setup

See `plugins/flutter_fire/` for a complete example.

## Installing Plugins

### From ZIP File

1. Open Plugin Manager (Tools → Plugins)
2. Go to "Add Plugin" tab
3. Click "Browse ZIP File..."
4. Select your plugin ZIP file
5. Plugin will be extracted and registered automatically

### From Folder

1. Open Plugin Manager (Tools → Plugins)
2. Go to "Add Plugin" tab
3. Click "Browse Folder..."
4. Select your plugin folder
5. Plugin will be copied and registered automatically

## Plugin Lifecycle

1. **Discovery**: App scans `plugins/` directory
2. **Loading**: Enabled plugins are loaded dynamically
3. **Initialization**: `initialize()` function is called
4. **Execution**: Plugin functions are called when needed
5. **Unloading**: Plugin is unloaded when disabled or app closes

## Best Practices

1. **Error Handling**: Always wrap operations in try-except blocks
2. **Logging**: Use `api.get_logger()` for logging
3. **User Feedback**: Use `api.show_message()` for important notifications
4. **Path Handling**: Use `pathlib.Path` for cross-platform compatibility
5. **Validation**: Validate inputs before processing

## Troubleshooting

### Plugin Not Loading

- Check `plugin.json` syntax (must be valid JSON)
- Verify `entry` file exists
- Check plugin logs in console
- Ensure `initialize()` function exists

### Plugin Errors

- Check console output for error messages
- Verify all required dependencies are available
- Test plugin in isolation before distributing

## Security Notes

- Plugins have full Python access (user responsibility)
- Only install plugins from trusted sources
- Review plugin code before installation
- Disable plugins if they cause issues

## Future Enhancements

- Remote plugin store
- Plugin dependencies management
- Plugin sandboxing
- Plugin signing/verification
- Plugin update mechanism

