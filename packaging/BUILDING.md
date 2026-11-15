# Build the native desktop application

Build from a checkout of the release tag on the target operating system and CPU architecture. PyInstaller does not cross-compile this application. The release matrix uses Python 3.11 on `windows-2022` x64, `ubuntu-22.04` x64 and `macos-15` ARM64. macOS packages require macOS 15 or newer; Intel Macs are not a build target.

Create a Python 3.11 virtual environment and activate it using your shell's normal activation command. Install the pinned dependencies:

```sh
python -m pip install torch==2.15.0 --index-url https://download.pytorch.org/whl/cpu
python -m pip install -r packaging/requirements-build.txt
python -m unittest discover -s tests -v
python ai.py --smoke-test --smoke-report build/source-smoke.json
```

The CPU wheel is deliberate: CUDA is not needed by the desktop demonstration. Source development may use another supported PyTorch installation, but the release's exact installed versions and target are recorded in its manifest. Build dependencies include NumPy 2.4.6, Pygame 2.6.1, PyInstaller 6.22.3 and contrib hooks 2026.10.

Choose the matching target and replace `COMMIT_SHA` with the full 40-character source commit returned by `git rev-parse HEAD`:

```sh
python packaging/build_desktop.py --target windows-x64 --source-sha COMMIT_SHA
python packaging/build_desktop.py --target linux-x64 --source-sha COMMIT_SHA
python packaging/build_desktop.py --target macos-arm64 --source-sha COMMIT_SHA
```

Run only the one command for your machine. Use a fresh checkout for a new build; the helper refuses to reuse an existing `build/desktop/TARGET` directory. Results are written to `release-assets/`. Building is resource intensive because CPU PyTorch and its native libraries are included. No publisher certificate, Apple Developer ID or notarization credentials are configured. macOS binaries receive PyInstaller's required local ad-hoc signature, verified after archive extraction.

The helper retains the standard PyInstaller Torch hook, including Python sources needed by optimizer/Dynamo introspection. It uses an onedir bundle rather than self-extracting a large runtime on each launch. Keep the complete folder intact. Linux tar archives and macOS `ditto` archives preserve the POSIX symlinks required by PyInstaller; repackaging them with a symlink-flattening tool can break the application.

## Validation and release

The source smoke check and each extracted binary execute 72 real game frames using SDL dummy display/audio drivers. This fills replay beyond the 64-experience threshold, runs actual Adam updates, and checks finite Q outputs and changed, finite network parameters. Tests do not measure policy quality or replace a human check of the visible desktop window. Default launch remains the original automatic Pygame game. CPU tensor operations use one worker thread to keep the small MLP from competing with the Pygame event loop through a large worker pool; the target frame rate remains 60 FPS.

Each archive includes a manifest, launch instructions and original third-party licence notices. External platform manifests add the final archive hash and extracted-binary execution report. `SHA256SUMS.txt` is generated across the final release assets. Manifests describe provenance; builds are not asserted to be bit-for-bit reproducible.

Pull requests build and validate all three native targets with read-only repository permission. A push to this repository's `main` publishes only when all targets pass. The publishing job alone has `contents: write`; it creates an exact-source draft, checks its asset set and tag, then publishes it. Existing releases/assets are never overwritten. An identical-source completed release is a no-op; another commit under an existing tag fails and requires a version bump in `release.json`, `ai.py`, the macOS spec and release notes. Interrupted drafts require manual inspection, rather than silently replacing files.

## Dependency source and rebuilding Pygame

The release includes the exact `pygame-2.6.1.tar.gz` source archive fetched from PyPI and checked against PyPI's SHA-256 metadata. Original licences for Pygame, SDL and other wheel components are retained under `licenses/`; Python, PyTorch, NumPy, PyInstaller and hook notices are preserved as supplied by their distributions. Components keep their own terms. This packaging does not assign a licence to the original project source.

To inspect, modify or replace Pygame, extract its matching source archive, follow its included platform build instructions to build a wheel, then install that wheel into a fresh build environment in place of the PyPI Pygame wheel. Re-run this project's source checks and native builder with your modified source. Use the project's source archive for the matching release tag, which includes this spec and all build scripts. Pygame and its native dependencies remain dynamically linked in the onedir distribution; preserve notices and any corresponding-source obligations when redistributing your rebuild. Source/build references: [Pygame source](https://github.com/pygame/pygame), [Pygame compilation guide](https://www.pygame.org/wiki/Compilation), [PyTorch source](https://github.com/pytorch/pytorch), [NumPy source](https://github.com/numpy/numpy), [CPython source](https://github.com/python/cpython), [PyInstaller source](https://github.com/pyinstaller/pyinstaller), [contrib hooks](https://github.com/pyinstaller/pyinstaller-hooks-contrib).
