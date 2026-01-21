# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for STL 3D Viewer macOS build.
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
        # Requests for license validation
        'requests',
        'urllib3',
        # Custom modules
        'stl_viewer',
        'viewer_widget',
        'viewer_widget_offscreen',
        'ui.sidebar_panel',
        'ui.toolbar',
        'ui.styles',
        'ui.components',
        'ui.license_dialog',
        'core.mesh_calculator',
        'core.license_validator',
        # Standard library modules that might be missed
        'logging',
        'pathlib',
        'datetime',
        'io',
        'json',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # PyQt6 (not used)
        'PyQt6', 'PyQt6.QtCore', 'PyQt6.QtGui', 'PyQt6.QtWidgets',
        # Unused PyQt5 modules
        'PyQt5.QtWebEngine', 'PyQt5.QtWebEngineWidgets', 'PyQt5.QtWebEngineCore',
        'PyQt5.QtBluetooth', 'PyQt5.QtNfc',
        'PyQt5.QtLocation', 'PyQt5.QtPositioning',
        'PyQt5.QtMultimedia', 'PyQt5.QtMultimediaWidgets', 'PyQt5.QtMultimediaQuick',
        'PyQt5.QtQuick', 'PyQt5.QtQml', 'PyQt5.QtQuickWidgets',
        'PyQt5.QtSql',
        'PyQt5.QtXml', 'PyQt5.QtXmlPatterns',
        'PyQt5.QtNetwork',
        'PyQt5.QtSvg',
        'PyQt5.QtDesigner', 'PyQt5.QtHelp',
        # Test files
        'test_minimal_pyqt6', 'test_pyvista_qt', 'test_pyvista_simple', 'test_volume_methods',
        'check_results',
        # VTK web modules (not needed)
        'vtkmodules.web', 'vtkmodules.qt.web',
    ],
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
    name='STL 3D Viewer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,  # Enable stripping for size reduction
    upx=True,
    console=False,  # Windowed app, no console
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=True,  # Enable stripping for size reduction
    upx=True,
    upx_exclude=[],
    name='STL 3D Viewer',
)

app = BUNDLE(
    coll,
    name='STL 3D Viewer.app',
    icon=None,  # Can add icon.icns here if available
    bundle_identifier='com.jewelleryviewer.stlviewer',
)
