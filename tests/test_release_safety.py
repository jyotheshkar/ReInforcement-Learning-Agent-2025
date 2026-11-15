"""Release guards use tiny local fixtures; no network or native build is needed."""
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("desktop_publisher", ROOT / "packaging/publish_release.py")
publisher = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(publisher)
SHA = "a" * 40


class ReleaseSafetyTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.assets = Path(self.temporary.name)
        self.environment = patch.dict(os.environ, {
            "GITHUB_EVENT_NAME": "push", "GITHUB_REF": "refs/heads/main",
            "GITHUB_REPOSITORY": publisher.REPOSITORY, "GITHUB_SHA": SHA,
        })
        self.environment.start()
        self.addCleanup(self.environment.stop)
        source = self.assets / "pygame-2.6.1.tar.gz"
        source.write_bytes(b"matching source fixture")
        for target, config in publisher.CONFIG["platforms"].items():
            archive = self.assets / config["archive"]
            archive.write_bytes(target.encode())
            manifest = {
                "source_commit": SHA, "target": target,
                "version": publisher.CONFIG["version"], "tag": publisher.CONFIG["tag"],
                "extracted_archive_smoke": {"status": "passed", "frozen": True,
                                            "frames": 72, "optimizer_updates": 9,
                                            "parameters_changed": True},
                "archive": {"sha256": publisher.file_digest(archive), "bytes": archive.stat().st_size},
                "pygame_corresponding_source": {"filename": source.name,
                                                  "sha256": publisher.file_digest(source)},
            }
            (self.assets / f"BUILD-MANIFEST-{target}.json").write_text(json.dumps(manifest), encoding="utf-8")

    def test_tag_collision_never_mutates_release(self):
        with patch.object(publisher, "tag_sha", return_value="b" * 40), \
                patch.object(publisher, "find_release", return_value=None), \
                patch.object(publisher.subprocess, "run") as run:
            with self.assertRaisesRegex(RuntimeError, "another commit"):
                publisher.publish(SHA, self.assets)
            run.assert_not_called()

    def test_corrupt_archive_is_rejected_before_github_access(self):
        (self.assets / publisher.CONFIG["platforms"]["windows-x64"]["archive"]).write_bytes(b"modified")
        with patch.object(publisher, "api") as api, patch.object(publisher, "tag_sha") as tag:
            with self.assertRaisesRegex(RuntimeError, "evidence failed"):
                publisher.publish(SHA, self.assets)
            api.assert_not_called()
            tag.assert_not_called()

    def test_pull_request_cannot_publish(self):
        with patch.dict(os.environ, {"GITHUB_EVENT_NAME": "pull_request"}), \
                patch.object(publisher.subprocess, "run") as run:
            with self.assertRaisesRegex(RuntimeError, "exact main push"):
                publisher.publish(SHA, self.assets)
            run.assert_not_called()

    def test_create_exact_tag_before_draft_and_publish(self):
        required = [config["archive"] for config in publisher.CONFIG["platforms"].values()]
        required += [f"BUILD-MANIFEST-{target}.json" for target in publisher.CONFIG["platforms"]]
        required += ["pygame-2.6.1.tar.gz", "SHA256SUMS.txt"]
        uploaded = {"assets": [{"name": name} for name in required]}
        with patch.object(publisher, "tag_sha", side_effect=[None, SHA, SHA]), \
                patch.object(publisher, "find_release", side_effect=[None, uploaded]), \
                patch.object(publisher.subprocess, "run") as run:
            publisher.publish(SHA, self.assets)
        commands = [call.args[0] for call in run.call_args_list]
        self.assertEqual(commands[0][:3], ["gh", "api", f"repos/{publisher.REPOSITORY}/git/refs"])
        self.assertIn(f"sha={SHA}", commands[0])
        self.assertEqual(commands[1][:3], ["gh", "release", "create"])
        self.assertIn("--draft", commands[1])
        self.assertIn("--verify-tag", commands[1])
        self.assertEqual(commands[2][:3], ["gh", "release", "edit"])
        self.assertIn("--draft=false", commands[2])

    def test_incomplete_existing_draft_is_not_overwritten(self):
        with patch.object(publisher, "tag_sha", return_value=SHA), \
                patch.object(publisher, "find_release", return_value={"draft": True, "assets": []}), \
                patch.object(publisher.subprocess, "run") as run:
            with self.assertRaisesRegex(RuntimeError, "incomplete"):
                publisher.publish(SHA, self.assets)
            run.assert_not_called()

    def test_draft_lookup_uses_authenticated_list_then_exact_release_id(self):
        tag = publisher.CONFIG["tag"]
        draft = {"id": 42, "tag_name": tag, "draft": True, "assets": []}
        with patch.object(publisher, "api", side_effect=[[draft], draft]) as api:
            self.assertEqual(publisher.find_release(tag), draft)
        self.assertIn("/releases?per_page=100&page=1", api.call_args_list[0].args[0])
        self.assertTrue(api.call_args_list[1].args[0].endswith("/releases/42"))


if __name__ == "__main__":
    unittest.main()
