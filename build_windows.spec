# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['src/main.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        'src.graphics.canvas',
        'src.graphics.region_item',
        'src.graphics.wall_item',
        'src.graphics.obstacle_item',
        'src.graphics.region_editor',
        'src.widgets.toolbar',
        'src.widgets.side_panel',
        'src.models.project',
        'src.models.region',
        'src.models.venue',
        'src.export.exporter',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='水浒侠影纵横VR场景设计',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon=None,
)
