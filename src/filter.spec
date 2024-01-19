# ---------------------------------------------------------------------------
# File:   filter.spec - executable specified stuff
# Author: Jens Kallup - paule32
#
# Rights: (c) 2024 by kallup non-profit software
#         all rights reserved
#
# only for education, and for non-profit usage !!!
# commercial use ist not allowed.
# ---------------------------------------------------------------------------

icon_files = [
    ( "img/flag_english.png", "flag_english" ),
    ( "img/flag_german.png",  "flag_german" ),
    ( "img/flag_french.png",  "flag_french" ),
    ( "img/flag_spanish.png", "flag_spanish" )
]

a = Analysis(
    ['filter.py'],
    pathex=[],
    binaries=icon_files,
    datas=[],
    hiddenimports=[],
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
    name='filter',
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
)
