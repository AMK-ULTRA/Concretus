# -*- mode: python ; coding: utf-8 -*-

import sys
import os
from PyInstaller.utils.hooks import collect_submodules

block_cipher = None

# Define project root
project_root = os.path.abspath(os.path.dirname('__file__'))

# Define assets to include
datas = [
    ('assets/images/*.png', 'assets/images'),
    ('assets/images/*.ico', 'assets/images'),
    ('assets/styles/*.css', 'assets/styles'),
    ('assets/files/*.pdf', 'assets/files'),
    ('assets/files/License.txt', 'assets/files')
]

# Add all needed PyQt hooks
hiddenimports = [
    'PyQt6.QtCore',
    'PyQt6.QtGui',
    'PyQt6.QtWidgets',
    'PyQt6.sip',
    'reportlab.lib.styles',
    'reportlab.lib.pagesizes',
    'reportlab.lib.units',
    'reportlab.platypus',
    'reportlab.lib.colors',
    'pyqtgraph',
    'numpy',
    'numpy.polynomial',
]

# Add all your submodules
for module in ['core', 'gui', 'reports']:
    if os.path.isdir(module):  # Check that the module exists
        hiddenimports.extend(collect_submodules(module))

a = Analysis(
    ['app.py'],
    pathex=[project_root],
    binaries=[],
    datas=datas,  # Use the asset list directly
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
    name='Concretus',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,  # Change to True for debugging
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/images/logo.ico',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Concretus',
)