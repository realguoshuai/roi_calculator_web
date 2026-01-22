# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['D:\\code\\git\\roi_calculator\\main_fast.py'],
    pathex=['D:\\code\\git\\roi_calculator\\venv312\\Lib\\site-packages'],
    binaries=[],
    datas=[('D:\\code\\git\\roi_calculator\\venv312\\Lib\\site-packages\\akshare\\file_fold', 'akshare\\file_fold'), ('D:\\code\\git\\roi_calculator\\config.py', '.'), ('D:\\code\\git\\roi_calculator\\roi.py', '.')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='ROI_Calculator',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='ROI_Calculator',
)
