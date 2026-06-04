# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for "Delta Plax Education Suite Server.exe" (section 13).
# Build from the repo root:  pyinstaller installer/deltaplax_server.spec
#
# Bundles the FastAPI app, the Alembic migrations and the operational scripts
# into a single Windows executable. The React static build is expected at
# ``frontend/dist`` and is bundled as a data directory served on the LAN.

block_cipher = None

a = Analysis(
    ["../backend/app/local_server.py"],
    pathex=["../backend"],
    binaries=[],
    datas=[
        ("../backend/alembic", "alembic"),
        ("../backend/alembic.ini", "."),
        ("../scripts", "scripts"),
        # ("../frontend/dist", "frontend/dist"),  # uncomment once the SPA is built
    ],
    hiddenimports=[
        "uvicorn.logging",
        "uvicorn.loops.auto",
        "uvicorn.protocols.http.auto",
        "uvicorn.protocols.websockets.auto",
        "uvicorn.lifespan.on",
        "app.api.v1.router",
    ],
    hookspath=[],
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
    name="Delta Plax Education Suite Server",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # runs as a background/service process
)
