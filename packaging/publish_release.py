"""Publish checked desktop assets using the release job's scoped gh token.

An existing tag/release is immutable: identical-source reruns are no-ops;
another source commit requires a new version. This script never deletes assets.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
CONFIG = json.loads((ROOT / "packaging/release.json").read_text(encoding="utf-8"))
REPOSITORY = "jyotheshkar/ReInforcement-Learning-Agent-2025"


def api(path: str):
    process = subprocess.run(["gh", "api", path], text=True, capture_output=True)
    if process.returncode:
        if "HTTP 404" in process.stderr:
            return None
        raise RuntimeError(f"GitHub read failed: {process.stderr.strip()}")
    return json.loads(process.stdout)


def tag_sha(tag: str):
    reference = api(f"repos/{REPOSITORY}/git/ref/tags/{tag}")
    if reference is None:
        return None
    target = reference["object"]
    for _ in range(5):
        if target["type"] == "commit":
            return target["sha"]
        if target["type"] != "tag":
            break
        annotation = api(f"repos/{REPOSITORY}/git/tags/{target['sha']}")
        target = annotation["object"]
    raise RuntimeError("Release tag does not resolve to a commit")


def find_release(tag: str):
    # GET /releases/tags/{tag} returns published releases and can miss drafts.
    # The authenticated list includes drafts visible to this write-scoped job.
    matches = []
    for page_number in range(1, 101):
        releases = api(f"repos/{REPOSITORY}/releases?per_page=100&page={page_number}")
        if not isinstance(releases, list):
            raise RuntimeError("Could not enumerate existing releases safely")
        matches.extend(item for item in releases if item.get("tag_name") == tag)
        if len(releases) < 100:
            break
    else:
        raise RuntimeError("Release enumeration limit reached; inspect existing releases manually")
    if len(matches) > 1:
        raise RuntimeError("Multiple releases use this tag; inspect them manually")
    if not matches:
        return None
    detail = api(f"repos/{REPOSITORY}/releases/{matches[0]['id']}")
    if detail is None or detail.get("tag_name") != tag:
        raise RuntimeError("Release changed during inspection")
    return detail


def file_digest(path: Path):
    hasher = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def publish(source_sha: str, assets: Path):
    if not re.fullmatch(r"[0-9a-f]{40}", source_sha):
        raise ValueError("Expected a full source commit SHA")
    if (os.environ.get("GITHUB_EVENT_NAME") != "push"
            or os.environ.get("GITHUB_REF") != "refs/heads/main"
            or os.environ.get("GITHUB_REPOSITORY") != REPOSITORY
            or os.environ.get("GITHUB_SHA") != source_sha):
        raise RuntimeError("Publishing is restricted to this repository's exact main push")
    if not re.fullmatch(r"desktop-v\d+\.\d+\.\d+", CONFIG["tag"]):
        raise RuntimeError("Unexpected release tag")
    if CONFIG["tag"] != "desktop-v" + CONFIG["version"]:
        raise RuntimeError("Version/tag mismatch")
    required = []
    pygame_sources = set()
    for target, target_config in CONFIG["platforms"].items():
        archive = assets / target_config["archive"]
        manifest_path = assets / f"BUILD-MANIFEST-{target}.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        smoke = manifest.get("extracted_archive_smoke", {})
        if (manifest.get("source_commit") != source_sha or manifest.get("target") != target
                or manifest.get("version") != CONFIG["version"]
                or manifest.get("tag") != CONFIG["tag"]
                or smoke.get("status") != "passed" or smoke.get("frozen") is not True
                or smoke.get("frames") != 72 or smoke.get("optimizer_updates", 0) < 1
                or smoke.get("parameters_changed") is not True
                or manifest["archive"]["sha256"] != file_digest(archive)
                or manifest["archive"]["bytes"] != archive.stat().st_size):
            raise RuntimeError(f"Release evidence failed for {target}")
        if archive.stat().st_size >= 2 * 1024**3:
            raise RuntimeError(f"Release asset too large: {archive.name}")
        required.extend([archive, manifest_path])
        source = manifest["pygame_corresponding_source"]
        pygame_source = assets / Path(source["filename"]).name
        if file_digest(pygame_source) != source["sha256"]:
            raise RuntimeError("Pygame corresponding-source hash mismatch")
        pygame_sources.add(pygame_source)
    required.extend(sorted(pygame_sources))
    checksums = assets / "SHA256SUMS.txt"
    checksums.write_text("".join(f"{file_digest(path)}  {path.name}\n" for path in sorted(required)),
                         encoding="utf-8")
    required.append(checksums)

    tag = CONFIG["tag"]
    existing_tag_sha = tag_sha(tag)
    existing_release = find_release(tag)
    if existing_tag_sha is not None and existing_tag_sha != source_sha:
        raise RuntimeError(f"{tag} already refers to another commit. Bump the desktop version; nothing was overwritten.")
    if existing_release is not None:
        if existing_tag_sha != source_sha:
            raise RuntimeError("Existing release has no matching exact-source tag")
        expected = {path.name for path in required}
        present = {item["name"] for item in existing_release["assets"]}
        if existing_release.get("draft") or not expected.issubset(present):
            raise RuntimeError("Existing release is incomplete. Inspect it manually; no assets were overwritten.")
        print(f"{tag} already published for this source commit; leaving it unchanged.")
        return

    # Create/verify the exact lightweight tag explicitly. A draft alone may not
    # materialize a new ref until publication, so --target is not sufficient.
    if existing_tag_sha is None:
        subprocess.run(["gh", "api", f"repos/{REPOSITORY}/git/refs", "--method", "POST",
                        "-f", f"ref=refs/tags/{tag}", "-f", f"sha={source_sha}"], check=True)
    if tag_sha(tag) != source_sha:
        raise RuntimeError("Exact-source tag verification failed before release creation")

    # A draft keeps interrupted/partial uploads out of the public download list.
    # A retry encounters the draft and fails safely for manual inspection.
    subprocess.run(["gh", "release", "create", tag, *map(str, required),
                    "--repo", REPOSITORY, "--verify-tag",
                    "--title", f"Zombie Hunter DQN desktop {CONFIG['version']}",
                    "--notes-file", str(ROOT / "packaging/RELEASE_NOTES.md"), "--draft"], check=True)
    if tag_sha(tag) != source_sha:
        raise RuntimeError("Post-create tag verification failed; release remains a draft")
    uploaded = find_release(tag)
    if uploaded is None:
        raise RuntimeError("Created draft could not be found for asset verification")
    if {item["name"] for item in uploaded["assets"]} != {path.name for path in required}:
        raise RuntimeError("Uploaded asset set is incomplete; release remains a draft")
    subprocess.run(["gh", "release", "edit", tag, "--repo", REPOSITORY,
                    "--draft=false", "--latest"], check=True)
    print(f"Published {tag} for {source_sha}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--assets", type=Path, required=True)
    arguments = parser.parse_args()
    publish(arguments.source_sha, arguments.assets.resolve())
