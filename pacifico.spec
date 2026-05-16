# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# Definición de los archivos y carpetas a incluir
# Nota: No se incluye explicitamente progress.db para que se genere externamente
archivos_datos = [
    ('assets', 'assets'),
    ('data/levels.py', 'data'),
    ('data/niveles_contenido.py', 'data'),
    ('scenes', 'scenes'),
    ('minigames', 'minigames'),
    ('utils', 'utils')
]

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=archivos_datos,
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
    name='Pacifico_Educativo',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False, # windowed=True (sin consola visible)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['assets\\\\images\\\\ui\\\\icono.ico'], # Ícono del ejecutable
)
