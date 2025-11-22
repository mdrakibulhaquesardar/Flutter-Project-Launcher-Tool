"""Flutter Fire Setup Plugin."""
from pathlib import Path
import yaml


def setup_flutter_fire(api, project_path: str, **kwargs):
    """Setup Firebase configuration."""
    logger = api.get_logger()
    project = Path(project_path)
    
    pubspec_path = project / "pubspec.yaml"
    if not pubspec_path.exists():
        api.show_message(
            "Error",
            "pubspec.yaml not found. This is not a Flutter project.",
            "error"
        )
        return
    
    # Read pubspec.yaml
    try:
        with open(pubspec_path, 'r', encoding='utf-8') as f:
            pubspec = yaml.safe_load(f)
    except Exception as e:
        api.show_message(
            "Error",
            f"Failed to read pubspec.yaml: {e}",
            "error"
        )
        return
    
    # Add Firebase dependencies
    if "dependencies" not in pubspec:
        pubspec["dependencies"] = {}
    
    firebase_deps = {
        "firebase_core": "^3.0.0",
        "firebase_auth": "^5.0.0",
        "cloud_firestore": "^5.0.0",
        "firebase_storage": "^12.0.0"
    }
    
    for dep, version in firebase_deps.items():
        if dep not in pubspec["dependencies"]:
            pubspec["dependencies"][dep] = version
    
    # Write updated pubspec.yaml
    try:
        with open(pubspec_path, 'w', encoding='utf-8') as f:
            yaml.dump(pubspec, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
    except Exception as e:
        api.show_message(
            "Error",
            f"Failed to write pubspec.yaml: {e}",
            "error"
        )
        return
    
    # Create Firebase config directories
    android_dir = project / "android" / "app"
    ios_dir = project / "ios"
    
    # Create placeholder files
    if android_dir.exists():
        google_services_placeholder = android_dir / "google-services.json.placeholder"
        google_services_placeholder.write_text(
            "# Place your google-services.json file here\n"
            "# Download from Firebase Console: Project Settings > Your Apps > Android App"
        )
    
    if ios_dir.exists():
        google_services_placeholder = ios_dir / "GoogleService-Info.plist.placeholder"
        google_services_placeholder.write_text(
            "# Place your GoogleService-Info.plist file here\n"
            "# Download from Firebase Console: Project Settings > Your Apps > iOS App"
        )
    
    logger.info(f"Setup Firebase configuration for {project_path}")
    api.show_message(
        "Success",
        f"Firebase setup completed!\n\n"
        f"Added dependencies to pubspec.yaml:\n"
        f"- firebase_core\n"
        f"- firebase_auth\n"
        f"- cloud_firestore\n"
        f"- firebase_storage\n\n"
        f"Next steps:\n"
        f"1. Run 'flutter pub get'\n"
        f"2. Add google-services.json (Android) and GoogleService-Info.plist (iOS)\n"
        f"3. Follow Firebase setup guide",
        "info"
    )


def initialize(api):
    """Initialize plugin."""
    api.register_template("flutter_fire", lambda project_path, **kwargs: setup_flutter_fire(api, project_path, **kwargs))
    api.get_logger().info("Flutter Fire Setup plugin initialized")

