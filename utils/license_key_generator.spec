# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

import os
import sys
from pathlib import Path

# Get the project root directory (parent of utils directory)
# When running from project root, utils/license_key_generator.py should exist
project_root = Path.cwd()
script_path = project_root / 'utils' / 'license_key_generator.py'

# Verify script exists
if not script_path.exists():
    # Try alternative path
    script_path = Path('utils/license_key_generator.py')
    if not script_path.exists():
        raise FileNotFoundError(f"Could not find license_key_generator.py at {script_path}")

a = Analysis(
    [str(script_path)],
    pathex=[str(project_root)],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='FluStudio-LicenseKeyGenerator',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)

