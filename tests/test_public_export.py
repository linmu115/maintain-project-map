from pathlib import Path
import json
import tempfile
import unittest
from unittest.mock import patch

from test_reader_export import fixture
from render_map import export_reader


class PublicExportTests(unittest.TestCase):
    def test_publication_keeps_slash_prefixed_prose_and_code(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data = fixture(root)
            data["records"][0]["body"] = "/api is a documented route."
            data["records"][0]["source_text"] = "/* a source comment */\nfunction main() {}"
            export_reader(data, root / "site/index.html", diagrams=False, public_root=root)
            payload = json.loads((root / "site/docs.json").read_text(encoding="utf-8"))
            for key in ("body", "source_text"):
                self.assertEqual(payload["records"][0][key], data["records"][0][key])

    def test_public_history_never_reads_capture_and_keeps_narrative(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data = fixture(root)
            data["records"].append({"id": "HIST-public", "kind": "history", "title": "公开历程",
                "path": str(root / "history.md"), "owned": True, "status": "current",
                "history": {"path": "history/missing-private-capture", "sha256": "private-hash"},
                "body": "公开叙述。 [原始反馈](history-event:EVT-private)"})
            with patch("development_history.load_capture", side_effect=AssertionError("private capture read")):
                export_reader(data, root / "site/index.html", diagrams=False, public_root=root)
            payload = json.loads((root / "site/docs.json").read_text(encoding="utf-8"))
            task = payload["development_history"]["tasks"]["HIST-public"]
            self.assertFalse(task["available"])
            record = payload["records"][-1]
            self.assertIn("公开叙述", record["body_html"])
            self.assertNotIn("data-history-event", record["body_html"])
            self.assertNotIn("history", record)
            self.assertFalse((root / "site/history").exists())
            registry = json.loads((root / "site/history-assets.json").read_text(encoding="utf-8"))
            self.assertEqual(registry, {"files": [], "captures": {}})
            for item in (root / "site").iterdir():
                text = item.read_text(encoding="utf-8")
                self.assertNotIn(str(root), text)
                self.assertNotIn(root.as_posix(), text)
                self.assertNotIn("missing-private-capture", text)

    def test_declared_sources_outside_public_root_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data = fixture(root)
            data["records"][0]["sources"] = [{"path": "../private.txt"}]
            with self.assertRaisesRegex(ValueError, "outside the declared root"):
                export_reader(data, root / "site/index.html", diagrams=False, public_root=root)
            self.assertFalse((root / "site").exists())

    def test_local_export_residue_cannot_enter_public_site(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data = fixture(root)
            (root / "site").mkdir()
            residue = root / "site/old-event.json"
            residue.write_text("private", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "empty output directory"):
                export_reader(data, root / "site/index.html", diagrams=False, public_root=root)
            self.assertEqual(residue.read_text(), "private")
            self.assertFalse((root / "site/index.html").exists())
