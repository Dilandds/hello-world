# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for STL 3D Viewer Windows build.
"""

import sys
from pathlib import Path

block_cipher = None

# Get the base directory
base_dir = Path(SPECPATH)

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('ui', 'ui'),
        ('core', 'core'),
    ],
    hiddenimports=[
        # PyQt5 modules
        'PyQt5',
        'PyQt5.QtCore',
        'PyQt5.QtGui',
        'PyQt5.QtWidgets',
        'PyQt5.sip',
        # PyVista and VTK
        'pyvista',
        'pyvistaqt',
        'vtkmodules',
        'vtkmodules.all',
        'vtkmodules.qt.QVTKRenderWindowInteractor',
        # NumPy
        'numpy',
        'numpy.core._methods',
        'numpy.lib.format',
        # ReportLab for PDF export
        'reportlab',
        'reportlab.pdfgen',
        'reportlab.lib',
        'reportlab.platypus',
        # Custom modules
        'stl_viewer',
        'viewer_widget',
        'viewer_widget_offscreen',
        'ui.sidebar_panel',
        'ui.toolbar',
        'ui.styles',
        'ui.components',
        'core.mesh_calculator',
        # Standard library modules that might be missed
        'logging',
        'pathlib',
        'datetime',
        'io',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['PyQt6', 'PyQt6.QtCore', 'PyQt6.QtGui', 'PyQt6.QtWidgets'],
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
    name='STL 3D Viewer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Windowed app, no console
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Can add icon.ico here if available
)
