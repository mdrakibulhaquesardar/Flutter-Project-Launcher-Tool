"""Riverpod Architecture Generator Plugin."""
from pathlib import Path
from typing import Dict, Any


def generate_riverpod_arch(api, project_path: str, **kwargs):
    """Generate Riverpod Architecture folder structure."""
    logger = api.get_logger()
    project = Path(project_path)
    
    # Create Riverpod structure
    lib_dir = project / "lib"
    
    # Create core directories
    (lib_dir / "core" / "providers").mkdir(parents=True, exist_ok=True)
    (lib_dir / "core" / "constants").mkdir(parents=True, exist_ok=True)
    (lib_dir / "core" / "utils").mkdir(parents=True, exist_ok=True)
    (lib_dir / "core" / "theme").mkdir(parents=True, exist_ok=True)
    
    # Create features directory
    features_dir = lib_dir / "features"
    features_dir.mkdir(exist_ok=True)
    
    # Create example feature
    example_feature = features_dir / "home"
    example_feature.mkdir(exist_ok=True)
    
    # Create feature subdirectories
    (example_feature / "data").mkdir(exist_ok=True)
    (example_feature / "data" / "models").mkdir(exist_ok=True)
    (example_feature / "data" / "repositories").mkdir(exist_ok=True)
    
    (example_feature / "domain").mkdir(exist_ok=True)
    (example_feature / "domain" / "entities").mkdir(exist_ok=True)
    (example_feature / "domain" / "providers").mkdir(exist_ok=True)
    
    (example_feature / "presentation").mkdir(exist_ok=True)
    (example_feature / "presentation" / "pages").mkdir(exist_ok=True)
    (example_feature / "presentation" / "widgets").mkdir(exist_ok=True)
    (example_feature / "presentation" / "providers").mkdir(exist_ok=True)
    
    # Create provider setup file
    provider_setup = lib_dir / "core" / "providers" / "app_providers.dart"
    provider_setup.write_text("""// App-wide Riverpod providers
import 'package:flutter_riverpod/flutter_riverpod.dart';

// Add your global providers here
""")
    
    logger.info(f"Generated Riverpod Architecture structure in {project_path}")
    api.show_message(
        "Success",
        f"Riverpod Architecture structure generated successfully!\n\n"
        f"Location: {project_path}\n"
        f"Example feature created: lib/features/home\n\n"
        f"Don't forget to add riverpod dependencies to pubspec.yaml:\n"
        f"- flutter_riverpod\n"
        f"- riverpod_annotation (optional)",
        "info"
    )


def initialize(api):
    """Initialize plugin."""
    api.register_architecture("riverpod", lambda project_path, **kwargs: generate_riverpod_arch(api, project_path, **kwargs))
    api.get_logger().info("Riverpod Architecture Generator plugin initialized")

