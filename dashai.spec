import os
import platform
import site
from PyInstaller.utils.hooks import collect_all, copy_metadata

SITEPKG = str(site.getsitepackages()[-1])

# Plugins are installed at runtime with "sys.executable -m pip" (see
# hooks/rthook_python_surrogate.py), so pip has to travel inside the bundle.
pip_datas, pip_binaries, pip_hiddenimports = collect_all("pip")

# pip resolves a plugin against what dashAI already ships before downloading
# anything, and that check reads *.dist-info metadata. Without the metadata pip
# considers torch & friends missing and re-downloads the whole dependency tree
# into the user's plugins directory.
try:
    dependency_metadata = copy_metadata("dashAI", recursive=True)
except Exception as error:  # pragma: no cover - build time diagnostics only
    print(f"WARNING: could not collect dependency metadata for plugins: {error}")
    dependency_metadata = copy_metadata("dashAI")

# Check for llama_cpp/lib presence to determine if we can include the binaries
llama_lib = os.path.exists(os.path.join(SITEPKG, "llama_cpp/lib"))

if platform.system() == "Darwin":
    webview_datas, webview_binaries, webview_hiddenimports = collect_all('webview')
else:
    webview_datas, webview_binaries, webview_hiddenimports = [], [], []

# Ensure the temp_checkpoints directory exists before building
if not os.path.exists(os.path.join("DashAI/back/user_models/temp_checkpoints")):
    os.makedirs("DashAI/back/user_models/temp_checkpoints")

a = Analysis(
    platform.system() == "Windows" and ["DashAI/__main__.py"] or ["DashAI/webview.py"],
    pathex=["."],
    binaries=(llama_lib and [(f"{SITEPKG}/llama_cpp/lib/*", "llama_cpp/lib")] or []) + webview_binaries + pip_binaries,
    datas=[
        ("DashAI/__main__.py", "DashAI/__main__.py"),
        ("DashAI/alembic", "DashAI/alembic"),
        ("DashAI/front/build", "DashAI/front/build"),
        ("DashAI/back/static/images", "DashAI/back/static/images"),
        ("DashAI/back/types/inf/ptype/LR.sav", "DashAI/back/types/inf/ptype"),
        ("DashAI/back/types/inf/ptype/scaler.pkl", "DashAI/back/types/inf/ptype"),
        (
            "DashAI/back/user_models/temp_checkpoints",
            "DashAI/back/user_models/temp_checkpoints",
        ),
        ("DashAI/back/seeds", "DashAI/back/seeds"),
        (f"{SITEPKG}/transformers", "transformers"),
        # Ship source .py for packages that run torch.jit.script at import time.
        # PyInstaller bundles only .pyc, but TorchScript needs original source
        # via inspect.getsource, so these must be shipped as data dirs.
        (f"{SITEPKG}/diffusers", "diffusers"),
        (f"{SITEPKG}/controlnet_aux", "controlnet_aux"),
    ] + webview_datas + pip_datas + dependency_metadata,
    hiddenimports=webview_hiddenimports + pip_hiddenimports,
    hookspath=["hooks"],
    runtime_hooks=["hooks/rthook_python_surrogate.py"],
    excludes=None,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    exclude_binaries=True,
    name="dashAI-launcher-cpu",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
    argv_emulation=True,
    icon="installer/dashAI.ico",
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="dashAI-launcher-cpu",
)

if platform.system() == "Darwin":
    app = BUNDLE(
        coll,
        name='dashAI.app',
        icon='installer/dashAI.icns',
        bundle_identifier='com.dashai.app',
        info_plist={
            'NSHighResolutionCapable': 'True',
            'LSBackgroundOnly': 'False',
        },
    )
