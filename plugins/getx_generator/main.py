"""GetX Architecture Generator Plugin."""
from pathlib import Path
from typing import Dict, Any


def generate_getx_arch(api, project_path: str, **kwargs):
    """Generate GetX Architecture folder structure."""
    logger = api.get_logger()
    project = Path(project_path)
    
    # Create GetX structure
    lib_dir = project / "lib"
    
    # Create GetX directories
    (lib_dir / "app" / "modules").mkdir(parents=True, exist_ok=True)
    (lib_dir / "app" / "routes").mkdir(parents=True, exist_ok=True)
    (lib_dir / "app" / "bindings").mkdir(parents=True, exist_ok=True)
    (lib_dir / "app" / "data" / "providers").mkdir(parents=True, exist_ok=True)
    (lib_dir / "app" / "data" / "models").mkdir(parents=True, exist_ok=True)
    (lib_dir / "app" / "data" / "repositories").mkdir(parents=True, exist_ok=True)
    (lib_dir / "app" / "core" / "utils").mkdir(parents=True, exist_ok=True)
    (lib_dir / "app" / "core" / "constants").mkdir(parents=True, exist_ok=True)
    
    # Create example module
    example_module = lib_dir / "app" / "modules" / "home"
    example_module.mkdir(exist_ok=True)
    (example_module / "controllers").mkdir(exist_ok=True)
    (example_module / "views").mkdir(exist_ok=True)
    (example_module / "bindings").mkdir(exist_ok=True)
    
    logger.info(f"Generated GetX Architecture structure in {project_path}")
    api.show_message(
        "Success",
        f"GetX Architecture structure generated successfully!\n\n"
        f"Location: {project_path}\n"
        f"Example module created: lib/app/modules/home",
        "info"
    )


def initialize(api):
    """Initialize plugin."""
    api.register_architecture("getx", lambda project_path, **kwargs: generate_getx_arch(api, project_path, **kwargs))
    api.get_logger().info("GetX Architecture Generator plugin initialized")

