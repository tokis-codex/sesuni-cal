# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['date_calculator.py'],
    pathex=[],
    binaries=[],
    datas=[('date_calculator.ico', '.'), ('gmail_fallback.png', '.'), ('daum_fallback.png', '.'), ('naver_fallback.png', '.'), ('history_tab.png', '.'), ('calendar_tab.png', '.')],
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
    a.binaries,
    a.datas,
    [],
    name='Sesuni_Calculator',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['date_calculator.ico'],
)
