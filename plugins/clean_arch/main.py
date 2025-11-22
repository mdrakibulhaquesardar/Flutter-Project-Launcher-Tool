"""Clean Architecture Generator Plugin."""
from pathlib import Path
from typing import Dict, Any


def generate_clean_arch(api, project_path: str, **kwargs):
    """Generate Clean Architecture folder structure."""
    logger = api.get_logger()
    project = Path(project_path)
    
    # Define Clean Architecture structure
    structure = {
        "lib": {
            "core": {
                "error": [],
                "usecases": [],
                "utils": []
            },
            "features": {}
        }
    }
    
    # Create base structure
    lib_dir = project / "lib"
    core_dir = lib_dir / "core"
    
    # Create core directories
    (core_dir / "error").mkdir(parents=True, exist_ok=True)
    (core_dir / "usecases").mkdir(parents=True, exist_ok=True)
    (core_dir / "utils").mkdir(parents=True, exist_ok=True)
    
    # Create feature template structure
    features_dir = lib_dir / "features"
    features_dir.mkdir(parents=True, exist_ok=True)
    
    # Create example feature
    example_feature = features_dir / "example_feature"
    example_feature.mkdir(exist_ok=True)
    
    # Create feature subdirectories
    (example_feature / "data").mkdir(exist_ok=True)
    (example_feature / "data" / "datasources").mkdir(exist_ok=True)
    (example_feature / "data" / "models").mkdir(exist_ok=True)
    (example_feature / "data" / "repositories").mkdir(exist_ok=True)
    
    (example_feature / "domain").mkdir(exist_ok=True)
    (example_feature / "domain" / "entities").mkdir(exist_ok=True)
    (example_feature / "domain" / "repositories").mkdir(exist_ok=True)
    (example_feature / "domain" / "usecases").mkdir(exist_ok=True)
    
    (example_feature / "presentation").mkdir(exist_ok=True)
    (example_feature / "presentation" / "pages").mkdir(exist_ok=True)
    (example_feature / "presentation" / "widgets").mkdir(exist_ok=True)
    (example_feature / "presentation" / "providers").mkdir(exist_ok=True)
    
    logger.info(f"Generated Clean Architecture structure in {project_path}")
    api.show_message(
        "Success",
        f"Clean Architecture structure generated successfully!\n\n"
        f"Location: {project_path}\n"
        f"Example feature created: lib/features/example_feature",
        "info"
    )


def initialize(api):
    """Initialize plugin."""
    api.register_architecture("clean_arch", lambda project_path, **kwargs: generate_clean_arch(api, project_path, **kwargs))
    api.get_logger().info("Clean Architecture Generator plugin initialized")

