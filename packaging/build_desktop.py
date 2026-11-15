"""Build, archive, extract and exercise one native desktop distribution.

Run on the target OS/architecture. Never cross-compile or publish from here.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path, PurePosixPath
import platform
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
from urllib.parse import urlparse
from urllib.request import urlopen
import zipfile

ROOT = Path(__file__).resolve().parents[1]
CONFIG = json.loads((ROOT / "packaging/release.json").read_text(encoding="utf-8"))
MAX_ASSET_BYTES = 2 * 1024**3 - 1


def digest(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def matching_notice(path: Path) -> bool:
    name = str(path).lower()
    return any(term in name for term in
               ("license", "licence", "copying", "notice", "copyright", "patents", "lgpl"))


def safe_notice_path(path: str) -> Path:
    # Wheel RECORD paths can contain ../bin entries. Preserve only safe parts.
    return Path(*[p for p in Path(path).parts if p not in ("..", ".", "/", "\\")
                  and not p.endswith(":")])


def collect_notices(destination: Path) -> tuple[list[dict], list[str]]:
    """Preserve original wheel notices, package licence directories and CPython."""
    inventory, notices = [], []
    covered = set()
    for dist in sorted(importlib.metadata.distributions(),
                       key=lambda item: item.metadata.get("Name", "").lower()):
        name = dist.metadata.get("Name", "unknown")
        version = dist.version
        inventory.append({"name": name, "version": version,
                          "home_page": dist.metadata.get("Home-page"),
                          "project_urls": dist.metadata.get_all("Project-URL", []),
                          "license_expression": dist.metadata.get("License-Expression"),
                          "license_metadata": dist.metadata.get("License")})
        component = re.sub(r"[^A-Za-z0-9_.-]", "_", name + "-" + version)
        for file in dist.files or []:
            if not matching_notice(Path(str(file))):
                continue
            source = Path(dist.locate_file(file))
            if not source.is_file() or source.stat().st_size > 10 * 1024 * 1024:
                continue
            # Ignore compiled files whose parent happens to contain "license".
            if source.suffix.lower() in (".pyc", ".pyd", ".dll", ".so", ".dylib", ".a"):
                continue
            target = destination / component / safe_notice_path(str(file))
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
            notices.append(str(target.relative_to(destination)).replace("\\", "/"))
            covered.add(name.lower().replace("_", "-"))
    for required in ("numpy", "pygame", "torch", "pyinstaller", "pyinstaller-hooks-contrib"):
        if required not in covered:
            raise RuntimeError(f"No licence notice found for required component {required}")

    candidates = [Path(sys.base_prefix) / name for name in ("LICENSE.txt", "LICENSE", "License.txt")]
    candidate = next((path for path in candidates if path.is_file()), None)
    python_notice = destination / "CPython" / "LICENSE.txt"
    python_notice.parent.mkdir(parents=True, exist_ok=True)
    if candidate:
        shutil.copyfile(candidate, python_notice)
    else:
        # setup-python installations can omit their source-tree root licence.
        exact_version = platform.python_version()
        url = f"https://raw.githubusercontent.com/python/cpython/v{exact_version}/LICENSE"
        with urlopen(url, timeout=60) as response:
            python_notice.write_bytes(response.read(1024 * 1024))
    notices.append("CPython/LICENSE.txt")
    return inventory, sorted(notices)


def matching_pygame_source(output: Path) -> dict:
    """Fetch the exact sdist directly; do not execute package build metadata."""
    version = importlib.metadata.version("pygame")
    api = f"https://pypi.org/pypi/pygame/{version}/json"
    with urlopen(api, timeout=60) as response:
        metadata = json.load(response)
    source = next(item for item in metadata["urls"] if item["packagetype"] == "sdist")
    if urlparse(source["url"]).hostname != "files.pythonhosted.org":
        raise RuntimeError("Unexpected source-archive host")
    filename = Path(source["filename"]).name
    if filename != f"pygame-{version}.tar.gz":
        raise RuntimeError("Unexpected pygame source filename")
    destination = output / filename
    with urlopen(source["url"], timeout=120) as response, destination.open("wb") as target:
        shutil.copyfileobj(response, target)
    actual = digest(destination)
    if actual != source["digests"]["sha256"]:
        raise RuntimeError("pygame source SHA-256 disagrees with PyPI metadata")
    return {"filename": filename, "url": source["url"], "sha256": actual,
            "metadata_url": api, "bytes": destination.stat().st_size}


def collect_pygame_source_notices(source: Path, destination: Path) -> list[str]:
    """Copy original native notices even when a wheel omits developer docs.

    The caller has verified this exact sdist's PyPI SHA-256. Read only selected
    regular members; never extract the archive tree or follow archive links.
    """
    version = "2.6.1"
    archive_root = f"pygame-{version}"
    selected = {}
    with tarfile.open(source, "r:gz") as archive:
        for member in archive.getmembers():
            path = PurePosixPath(member.name)
            if (path.is_absolute() or ".." in path.parts or "\\" in member.name
                    or not member.isfile() or member.size > 5 * 1024 * 1024):
                continue
            if len(path.parts) < 3 or path.parts[0] != archive_root:
                continue
            relative = PurePosixPath(*path.parts[1:])
            if not (relative == PurePosixPath("docs/LGPL.txt")
                    or relative.parent == PurePosixPath("docs/licenses")):
                continue
            if relative.suffix.lower() != ".txt":
                continue
            if str(relative) in selected:
                raise RuntimeError("Duplicate source notice in pygame archive")
            stream = archive.extractfile(member)
            if stream is None:
                raise RuntimeError("Could not read pygame source notice")
            selected[str(relative)] = stream.read()
    required = {"docs/LGPL.txt", "docs/licenses/LICENSE.sdl2.txt",
                "docs/licenses/LICENSE.sdl2_image.txt", "docs/licenses/LICENSE.sdl2_mixer.txt"}
    if not required.issubset(selected):
        raise RuntimeError("Matching pygame source is missing required LGPL/SDL notices")
    notices = []
    for relative, content in sorted(selected.items()):
        target = destination / f"pygame-{version}-source" / Path(*PurePosixPath(relative).parts)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
        notices.append(target.relative_to(destination).as_posix())
    return notices


def run_smoke(executable: Path, work_directory: Path, report: Path) -> dict:
    environment = os.environ.copy()
    environment.update(SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy",
                       PYGAME_HIDE_SUPPORT_PROMPT="1")
    # No PYTHONPATH or installed Python is needed by the extracted executable.
    environment.pop("PYTHONPATH", None)
    environment.pop("PYTHONHOME", None)
    subprocess.run([str(executable.resolve()), "--smoke-test", "--smoke-report", str(report.resolve())],
                   cwd=work_directory, env=environment, check=True, timeout=180)
    value = json.loads(report.read_text(encoding="utf-8"))
    required = (value.get("status") == "passed", value.get("version") == CONFIG["version"],
                value.get("frozen") is True, value.get("frames") == 72,
                value.get("optimizer_updates", 0) >= 1,
                value.get("replay_experiences", 0) >= 64,
                value.get("q_shape") == [1, 5], value.get("q_values_finite") is True,
                value.get("parameters_finite") is True, value.get("parameters_changed") is True,
                value.get("device") == "cpu")
    if not all(required):
        raise RuntimeError(f"Extracted executable failed runtime contract: {value}")
    return value


def make_archive(stage: Path, archive: Path, target: str) -> None:
    if target == "macos-arm64":
        # POSIX PyInstaller onedir bundles contain symlinks. ditto preserves them.
        subprocess.run(["ditto", "-c", "-k", "--sequesterRsrc", "--keepParent",
                        str(stage / "ZombieHunter"), str(archive)], check=True)
    elif target == "linux-x64":
        with tarfile.open(archive, "w:gz", dereference=False) as stream:
            stream.add(stage / "ZombieHunter", arcname="ZombieHunter")
    else:
        with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as stream:
            for path in sorted((stage / "ZombieHunter").rglob("*")):
                if path.is_file():
                    stream.write(path, path.relative_to(stage))


def extract_and_verify(archive: Path, target: str, platform_config: dict, output: Path) -> dict:
    with tempfile.TemporaryDirectory(prefix="zombiehunter-native-") as temporary:
        temporary = Path(temporary)
        extracted = temporary / "extracted"
        extracted.mkdir()
        if target == "macos-arm64":
            subprocess.run(["ditto", "-x", "-k", str(archive), str(extracted)], check=True)
            subprocess.run(["codesign", "--verify", "--deep", "--strict",
                            str(extracted / "ZombieHunter/ZombieHunter.app")], check=True)
        elif target == "linux-x64":
            # This is our own freshly produced archive, not an arbitrary upload.
            with tarfile.open(archive) as stream:
                stream.extractall(extracted)
        else:
            with zipfile.ZipFile(archive) as stream:
                stream.extractall(extracted)
        unrelated_cwd = temporary / "unrelated-working-directory"
        unrelated_cwd.mkdir()
        executable = extracted / platform_config["executable_path"]
        return run_smoke(executable, unrelated_cwd, output / f"smoke-{target}.json")


def build(target: str, source_sha: str, output: Path) -> None:
    configuration = CONFIG["platforms"][target]
    if platform.system() != configuration["system"] or platform.machine().lower() != configuration["machine"].lower():
        raise RuntimeError(f"Build {target} on its native runner, not {platform.platform()}")
    if not re.fullmatch(r"[0-9a-f]{40}", source_sha):
        raise ValueError("--source-sha must identify an exact 40-character Git commit")
    module = ast.parse((ROOT / "ai.py").read_text(encoding="utf-8"))
    source_version = next(node.value.value for node in module.body if isinstance(node, ast.Assign)
                          and any(isinstance(item, ast.Name) and item.id == "APP_VERSION" for item in node.targets))
    if source_version != CONFIG["version"]:
        raise RuntimeError("Application and release configuration versions disagree")
    output.mkdir(parents=True, exist_ok=True)
    # All mutable build paths are confined to this task's checkout.
    work = ROOT / "build/desktop" / target
    if work.exists():
        raise RuntimeError(f"Build directory already exists: {work}. Use a fresh checkout.")
    dist, stage = work / "dist", work / "stage"
    work.mkdir(parents=True)
    subprocess.run([sys.executable, "-m", "PyInstaller", str(ROOT / "packaging/ZombieHunter.spec"),
                    "--noconfirm", "--clean", "--distpath", str(dist),
                    "--workpath", str(work / "pyinstaller")], cwd=ROOT, check=True)
    payload = stage / "ZombieHunter"
    if target == "macos-arm64":
        payload.mkdir(parents=True)
        shutil.copytree(dist / "ZombieHunter.app", payload / "ZombieHunter.app", symlinks=True)
    else:
        shutil.copytree(dist / "ZombieHunter", payload, symlinks=True)

    inventory, notices = collect_notices(payload / "licenses")
    pygame_source = matching_pygame_source(output)
    pygame_native_notices = collect_pygame_source_notices(
        output / pygame_source["filename"], payload / "licenses")
    notices = sorted(set(notices + pygame_native_notices))
    print("Preserved Pygame/SDL source notices: " + json.dumps(pygame_native_notices))
    notice_text = (
        "Zombie Hunter DQN — third-party components\n\n"
        "This package retains the original licence terms for its dependencies.\n"
        "Read the unmodified notices in licenses/; no new licence is assigned to the application source.\n"
        "CPython, PyTorch, NumPy, Pygame/SDL and PyInstaller components are included.\n"
        "Pygame 2.6.1 corresponding source: pygame-2.6.1.tar.gz alongside the release assets.\n"
        "The release's project source plus BUILDING.md describe rebuilding with a modified Pygame.\n"
        "Keep dynamically linked libraries and these notices when redistributing.\n\n"
        "Installed build-environment distributions (not all are bundled runtime modules):\n"
        + "\n".join(f"- {item['name']} {item['version']}" for item in inventory)
        + "\n\nPreserved notice files:\n" + "\n".join(notices) + "\n"
    )
    (payload / "THIRD-PARTY-LICENSES.txt").write_text(notice_text, encoding="utf-8")
    for source, filename in ((ROOT / "docs/DOWNLOADS.md", "DOWNLOADS.md"),
                             (ROOT / "packaging/BUILDING.md", "BUILDING.md"),
                             (ROOT / "packaging/RELEASE_NOTES.md", "RELEASE_NOTES.md")):
        shutil.copyfile(source, payload / filename)
    manifest = {
        "application": CONFIG["application"], "version": CONFIG["version"], "tag": CONFIG["tag"],
        "source_repository": "https://github.com/jyotheshkar/ReInforcement-Learning-Agent-2025",
        "source_commit": source_sha, "target": target, "python": platform.python_version(),
        "build_platform": platform.platform(), "machine": platform.machine(),
        "dependencies": inventory, "pygame_corresponding_source": pygame_source,
        "preserved_notice_files": notices, "pygame_source_notice_files": pygame_native_notices,
        "signing": "ad-hoc; no Developer ID or notarization" if target == "macos-arm64" else "unsigned",
        "policy_quality": "not evaluated; no pretrained checkpoint supplied",
    }
    with tempfile.TemporaryDirectory(prefix="zombiehunter-stage-test-") as temporary:
        manifest["pre_archive_smoke"] = run_smoke(stage / configuration["executable_path"],
                                                 Path(temporary), work / "pre-archive-smoke.json")
    write_json(payload / "BUILD-MANIFEST.json", manifest)
    archive = output / configuration["archive"]
    make_archive(stage, archive, target)
    if archive.stat().st_size > MAX_ASSET_BYTES:
        raise RuntimeError("Native archive exceeds GitHub's per-asset limit")
    manifest["extracted_archive_smoke"] = extract_and_verify(archive, target, configuration, output)
    manifest["archive"] = {"filename": archive.name, "sha256": digest(archive),
                           "bytes": archive.stat().st_size}
    write_json(output / f"BUILD-MANIFEST-{target}.json", manifest)
    print(f"Verified native package: {archive.name}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", choices=CONFIG["platforms"], required=True)
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--output", type=Path, default=ROOT / "release-assets")
    args = parser.parse_args()
    build(args.target, args.source_sha, args.output.resolve())
