# -*- mode: python ; coding: utf-8 -*-
"""AI Studio OS — PyInstaller build spec (FastAPI + WebSocket edition)"""

import os
from pathlib import Path

ROOT = Path(SPECPATH)

a = Analysis(
    ['server.py'],
    pathex=[str(ROOT)],
    binaries=[],
    datas=[
        (str(ROOT / 'index.html'), '.'),
        (str(ROOT / 'main_router.py'), '.'),
        (str(ROOT / 'Agents'), 'Agents'),
        (str(ROOT / 'Skills'), 'Skills'),
        (str(ROOT / 'Guards'), 'Guards'),
        (str(ROOT / 'Knowledge'), 'Knowledge'),
    ],
    hiddenimports=[
        'uvicorn', 'uvicorn.loops', 'uvicorn.loops.auto',
        'uvicorn.protocols', 'uvicorn.protocols.http',
        'uvicorn.protocols.http.auto', 'uvicorn.protocols.websockets',
        'uvicorn.protocols.websockets.auto', 'uvicorn.lifespan',
        'uvicorn.lifespan.on',
        'fastapi', 'fastapi.middleware', 'fastapi.middleware.cors',
        'starlette', 'starlette.responses',
        'Skills', 'Skills.llm_client', 'Skills.system_visionary',
        'Skills.task_planner', 'Skills.web_io', 'Skills.build_memory_codex',
        'Skills.rag_loader',
        'Agents', 'Agents.classifier_agent', 'Agents.lead_planner',
        'Agents.audit_agent', 'Agents.system_planner',
        'Agents.numerical_planner', 'Agents.tech_architect',
        'Agents.schema_translator', 'Agents.code_agent',
        'Agents.ui_agent', 'Agents.combat_agent',
        'Agents.archivist_agent',
        'Guards', 'Guards.qa_auditor', 'Guards.schema_validator',
        'asyncio', 'anyio', 'websockets', 'websockets.legacy',
        'http', 'http.server',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['streamlit', 'altair', 'pandas', 'numpy', 'matplotlib',
              'PIL', 'pillow', 'pyarrow', 'pydeck', 'blinker'],
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
    name='AI_Studio_OS',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
