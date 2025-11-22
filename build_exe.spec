# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for FluStudio
"""

import sys
import os
from pathlib import Path

block_cipher = None

# Application data
app_name = 'FluStudio'
app_version = '1.0.0'

# Get paths - SPECPATH is set by PyInstaller
try:
    base_path = Path(SPECPATH)
except NameError:
    # Fallback if SPECPATH not available
    base_path = Path(os.path.dirname(os.path.abspath(SPECPATH or __file__)))

assets_dir = base_path / 'assets'
plugins_dir = base_path / 'plugins'
data_dir = base_path / 'data'

# Collect all data files
datas = []
if assets_dir.exists():
    datas.append((str(assets_dir), 'assets'))
if plugins_dir.exists():
    datas.append((str(plugins_dir), 'plugins'))
if data_dir.exists():
    datas.append((str(data_dir), 'data'))

# Hidden imports (modules that PyInstaller might miss)
hiddenimports = [
    'PyQt6.QtCore',
    'PyQt6.QtGui',
    'PyQt6.QtWidgets',
    'yaml',
    'requests',
    'sqlite3',
    'json',
    'pathlib',
    'ctypes',
    'subprocess',
    'threading',
    'queue',
]

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
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
    [],
    exclude_binaries=True,
    name=app_name,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # No console window (GUI application)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(assets_dir / 'icons' / 'app_icon.ico') if assets_dir.exists() and (assets_dir / 'icons' / 'app_icon.ico').exists() else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name=app_name,
)

