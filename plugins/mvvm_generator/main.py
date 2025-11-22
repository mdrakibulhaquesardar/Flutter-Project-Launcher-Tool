"""MVVM Architecture Generator Plugin."""
from pathlib import Path
from typing import Dict, Any


def generate_mvvm_arch(api, project_path: str, **kwargs):
    """Generate MVVM Architecture folder structure."""
    logger = api.get_logger()
    project = Path(project_path)
    
    # Create MVVM structure
    lib_dir = project / "lib"
    
    # Create core directories
    (lib_dir / "core" / "base").mkdir(parents=True, exist_ok=True)
    (lib_dir / "core" / "utils").mkdir(parents=True, exist_ok=True)
    (lib_dir / "core" / "constants").mkdir(parents=True, exist_ok=True)
    
    # Create features directory
    features_dir = lib_dir / "features"
    features_dir.mkdir(exist_ok=True)
    
    # Create example feature
    example_feature = features_dir / "example_feature"
    example_feature.mkdir(exist_ok=True)
    
    # Create MVVM structure for feature
    (example_feature / "models").mkdir(exist_ok=True)
    (example_feature / "views").mkdir(exist_ok=True)
    (example_feature / "viewmodels").mkdir(exist_ok=True)
    (example_feature / "services").mkdir(exist_ok=True)
    
    # Create base viewmodel
    base_viewmodel = lib_dir / "core" / "base" / "base_viewmodel.dart"
    base_viewmodel.write_text("""// Base ViewModel class
import 'package:flutter/foundation.dart';

abstract class BaseViewModel extends ChangeNotifier {
  bool _isLoading = false;
  String? _error;

  bool get isLoading => _isLoading;
  String? get error => _error;

  void setLoading(bool value) {
    _isLoading = value;
    notifyListeners();
  }

  void setError(String? error) {
    _error = error;
    notifyListeners();
  }

  @override
  void dispose() {
    super.dispose();
  }
}
""")
    
    logger.info(f"Generated MVVM Architecture structure in {project_path}")
    api.show_message(
        "Success",
        f"MVVM Architecture structure generated successfully!\n\n"
        f"Location: {project_path}\n"
        f"Example feature created: lib/features/example_feature\n\n"
        f"Structure:\n"
        f"- models/ - Data models\n"
        f"- views/ - UI widgets\n"
        f"- viewmodels/ - Business logic\n"
        f"- services/ - API/services",
        "info"
    )


def initialize(api):
    """Initialize plugin."""
    api.register_architecture("mvvm", lambda project_path, **kwargs: generate_mvvm_arch(api, project_path, **kwargs))
    api.get_logger().info("MVVM Architecture Generator plugin initialized")

