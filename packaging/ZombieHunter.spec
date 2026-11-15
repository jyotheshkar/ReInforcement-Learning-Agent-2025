# Native onedir builds intentionally retain PyInstaller's standard Torch hook.
# It preserves Torch Python sources as well as bytecode for optimizer/Dynamo
# introspection, collects native libraries, and avoids duplicate CUDA guessing.
from pathlib import Path
import sys

root = Path(SPECPATH).parent
a = Analysis(
    [str(root / "ai.py")], pathex=[str(root)], binaries=[], datas=[],
    hiddenimports=[], hookspath=[], hooksconfig={}, runtime_hooks=[], excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz, a.scripts, [], exclude_binaries=True, name="ZombieHunter",
    debug=False, bootloader_ignore_signals=False, strip=False, upx=False,
    console=False, disable_windowed_traceback=False,
    target_arch="arm64" if sys.platform == "darwin" else None,
    codesign_identity=None, entitlements_file=None,
)
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name="ZombieHunter")
if sys.platform == "darwin":
    app = BUNDLE(
        coll, name="ZombieHunter.app", icon=None,
        bundle_identifier="io.github.jyotheshkar.zombiehunter",
        info_plist={
            "CFBundleDisplayName": "Zombie Hunter DQN",
            "CFBundleShortVersionString": "1.0.0",
            "CFBundleVersion": "1.0.0",
            "LSMinimumSystemVersion": "15.0",
            "NSHighResolutionCapable": True,
        },
    )
