"""File operation utilities for Flutter Project Launcher Tool."""
import json
import shutil
from pathlib import Path
from typing import Dict, Any, Optional


def ensure_directory(path: str) -> Path:
    """Ensure directory exists, create if not."""
    dir_path = Path(path)
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path


def read_json(file_path: str, default: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Read JSON file, return default if file doesn't exist."""
    path = Path(file_path)
    if path.exists():
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return default or {}
    return default or {}


def write_json(file_path: str, data: Dict[str, Any]):
    """Write data to JSON file."""
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def is_flutter_project(path: str) -> bool:
    """Check if a directory is a Flutter project."""
    project_path = Path(path)
    pubspec = project_path / "pubspec.yaml"
    return pubspec.exists() and project_path.is_dir()


def copy_directory(src: str, dst: str, ignore_patterns: Optional[list] = None):
    """Copy directory recursively, optionally ignoring patterns."""
    src_path = Path(src)
    dst_path = Path(dst)
    
    if ignore_patterns is None:
        ignore_patterns = ['.git', '__pycache__', '.dart_tool', 'build']
    
    def should_ignore(path: Path) -> bool:
        for pattern in ignore_patterns:
            if pattern in path.parts:
                return True
        return False
    
    if dst_path.exists():
        shutil.rmtree(dst_path)
    
    shutil.copytree(src_path, dst_path, ignore=should_ignore if ignore_patterns else None)


