"""Source discovery and archival behavior across real separate Git worktrees."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import project_map as pm
from code_parsers import sha
from document_archive import archive_record
from source_inventory import bind_workspace, source_query, review_record_sources, cache_path, cached_state
from render_map import export_reader
from record_search import compact_response


class SourceArchiveTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.repo, self.base = self.root / "code", self.root / "map"
        self.repo.mkdir()
        self.git("init", "-q")
        pm.init_project(self.base, "test project", "project-test")
        self.env = patch.dict(os.environ, {"PROJECT_MAP_SOURCE_CACHE": str(self.root / "cache")})
        self.env.start(); self.addCleanup(self.env.stop)

    def git(self, *args):
        return subprocess.run(["git", "-C", str(self.repo), *args], check=True, capture_output=True)

    def code(self, name, body):
        path = self.repo / name; path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")
        return path

    def record(self, rid, body="current explanation", **meta):
        path = self.base / "records" / (rid + ".md")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("---\n" + json.dumps({"id": rid, "kind": "interface", "title": rid, **meta}) + "\n---\n" + body, encoding="utf-8")
        return path

    def manifest(self, **fields):
        path = self.base / "project.yaml"
        obj = json.loads(path.read_text(encoding="utf-8")); obj.update(fields)
        path.write_text(json.dumps(obj), encoding="utf-8")

    def bind(self, **options):
        return bind_workspace(self.base, "code", self.repo, **options)

    def source(self, path, **fields):
        return {"workspace_id": "code", "path": path, "role": "implementation", **fields}

    def test_explicit_binding_incremental_and_git_ignore(self):
        self.code("app.py", 'def main():\n    return 1\nif __name__ == "__main__":\n    main()\n')
        self.code("new.py", "def discovered(): pass\n")
        self.code(".gitignore", "ignored.py\n")
        self.code("ignored.py", "def hidden(): pass\n")
        self.code("vendor/lib.py", "def excluded(): pass\n")
        self.code("unknown.rs", "fn main() {}")
        self.git("add", "app.py", ".gitignore")
        with self.assertRaisesRegex(ValueError, "No source workspace"):
            source_query(self.base)
        self.bind()
        first = source_query(self.base)
        self.assertEqual(first["results"][0]["counts"]["parsed"], 2)
        second = source_query(self.base)
        self.assertEqual(second["results"][0]["counts"]["reused"], 2)
        state = cached_state(pm.load_project(self.base), "code")
        self.assertNotIn("ignored.py", state["files"])
        self.assertIn({"path": "unknown.rs", "reason": "unsupported_file_type"}, state["skipped"])
        self.assertEqual(source_query(self.base, kind="entrypoint")["results"][0]["path"], "app.py")
        self.assertIn("源码入口与依赖", Path(first["report"]).read_text(encoding="utf-8"))
        self.code("new.py", "def discovered(): return 2\n")
        self.assertEqual(source_query(self.base)["results"][0]["counts"]["parsed"], 1)
        (self.repo / "app.py").unlink()
        self.assertEqual(source_query(self.base, kind="entrypoint")["total"], 0)
        with self.assertRaisesRegex(ValueError, "worktree root"):
            bind_workspace(self.base, "wrong", self.repo / "vendor")

    def test_python_ts_html_entrypoints_and_static_references(self):
        self.bind(python_roots=["src"])
        self.code("src/pkg/__init__.py", "")
        self.code("src/pkg/api.py", "def dispatch(): return 7\n")
        self.code("src/pkg/main.py", "from .api import dispatch as send\ndef main(): return send()\n")
        self.code("pyproject.toml", '[project.scripts]\nrun = "pkg.main:main"\n')
        self.code("web/main.ts", "import { run as launch } from './api';\nexport const main = () => launch();\nimport(variable);\n")
        self.code("web/api.ts", "export function run(): number { return 1; }\n")
        self.code("web/index.html", '<script src="main.ts"></script><script>function start(){ return 1; } start();</script>')
        self.code("package.json", '{"main":"./web/main.ts","scripts":{"start":"node web/main.ts"}}')
        calls = source_query(self.base, kind="call", limit=100)["results"]
        call = next(c for c in calls if c["target"] == "send")
        self.assertEqual((call["target_path"], call["target_symbol"]), ("src/pkg/api.py", "dispatch"))
        call = next(c for c in calls if c["target"] == "launch")
        self.assertEqual((call["target_path"], call["target_symbol"]), ("web/api.ts", "run"))
        imports = source_query(self.base, kind="dependency", query="web/index.html")["results"]
        self.assertEqual(imports[0]["target_path"], "web/main.ts")
        entries = source_query(self.base, kind="entrypoint")["results"]
        self.assertIn("python_package_entry", {e["kind"] for e in entries})
        coverage = source_query(self.base, kind="coverage")["results"]
        self.assertTrue(any(x["reason"] == "nonliteral_dynamic_import" for x in coverage))

    def test_review_tracks_source_dependencies_and_search_surfaces_warning(self):
        self.bind()
        self.code("entry.py", "from dependency import run\ndef main(): return run()\n")
        self.code("dependency.py", "def run(): return 1\n")
        self.record("IF-main", "Main contract", sources=[self.source("entry.py", symbol="main")])
        self.record("IF-dep", sources=[self.source("dependency.py")])
        query = source_query(self.base, kind="gap")
        gaps = query["results"]
        report = Path(query["report"]).read_text(encoding="utf-8")
        self.assertEqual(report.count("→ `dependency.py`"), 1)
        self.assertTrue(any(g["kind"] == "unregistered_relation" for g in gaps))
        with self.assertRaisesRegex(ValueError, "reason"):
            review_record_sources(self.base, "IF-main", "")
        review_record_sources(self.base, "IF-main", "Checked main delegates to run and returns its value")
        self.code("dependency.py", "def run(): return 2\n")
        doc = pm.load_project(self.base)
        read = compact_response("read", pm.read_record(doc, "IF-main"))
        self.assertEqual(read["source_health"]["state"], "needs_review")
        self.assertEqual(read["sources"][0]["changed_dependencies"][0]["path"], "dependency.py")
        hit = compact_response("search", pm.search_project(doc, "IF-main"))["results"][0]
        self.assertEqual(hit["source_health"]["state"], "needs_review")
        self.assertEqual(pm.read_record(doc, "IF-main")["record"]["status"], "current")
        # Repeated scans cannot silently accept a changed dependency as valid.
        for _ in range(2):
            self.assertTrue(any(r["record_id"] == "IF-main" for r in source_query(self.base, kind="review")["results"]))
        review_record_sources(self.base, "IF-main", "Verified changed return value remains within contract")
        self.assertNotIn("source_health", pm.read_record(pm.load_project(self.base), "IF-main"))
        self.code("entry.py", "from dependency import run\ndef main(): return run() + 1\n")
        item = pm.read_record(pm.load_project(self.base), "IF-main")["resolved_sources"][0]
        self.assertEqual(item["symbol_review"], "needs_review")
        self.assertFalse((self.base / "archive").exists())

    def test_observation_without_review_stays_pending_until_explicit_review(self):
        self.bind(); self.code("main.py", "def main(): return 1\n")
        self.record("R", sources=[self.source("main.py")])
        source_query(self.base)
        self.code("main.py", "def main(): return 2\n")
        self.assertEqual(source_query(self.base, kind="review")["total"], 1)
        self.assertEqual(source_query(self.base, kind="review")["total"], 1)
        self.assertIn("source_health", pm.read_record(pm.load_project(self.base), "R"))

    def test_registration_gap_groups_repeated_imports_without_losing_evidence(self):
        self.bind()
        self.code("entry.py", "from dependency import run\nfrom dependency import run as again\ndef main(): return run()\n")
        self.code("dependency.py", "def run(): return 1\n")
        self.record("A", sources=[self.source("entry.py")])
        self.record("B", sources=[self.source("dependency.py")])
        result = source_query(self.base, kind="gap")
        gaps = result["results"]
        self.assertEqual(Path(result["report"]).read_text(encoding="utf-8").count("→ `dependency.py`"), 1)
        self.assertEqual(len(gaps), 1)
        self.assertEqual(gaps[0]["occurrences"], 2)
        self.assertEqual(gaps[0]["sample_lines"], [1, 2])
        self.assertEqual(source_query(self.base, kind="dependency")["total"], 2)

    def test_parser_unavailable_is_disclosed_and_retried(self):
        self.bind(); self.code("main.ts", "export function main() {}")
        with patch("code_parsers.js_parser", side_effect=ImportError("no grammar")):
            rows = source_query(self.base, kind="coverage")["results"]
            self.assertEqual(rows[0]["reason"], "parser_unavailable")
        self.assertEqual(source_query(self.base)["results"][0]["counts"]["parsed"], 1)
        self.assertEqual(source_query(self.base, kind="symbol")["results"][0]["name"], "main")

    def test_worktree_binding_and_map_cache_identity(self):
        self.code("main.py", "def original(): pass\n"); self.git("add", ".")
        self.git("-c", "user.name=test", "-c", "user.email=test@local", "commit", "-qm", "seed")
        other = self.root / "other-worktree"
        self.git("worktree", "add", "--detach", str(other), "HEAD")
        (other / "main.py").write_text("def alternate(): pass\n", encoding="utf-8")
        self.bind(); bind_workspace(self.base, "other", other)
        rows = source_query(self.base, kind="symbol", limit=100)["results"]
        self.assertEqual({(r["workspace_id"], r["name"]) for r in rows}, {("code", "original"), ("other", "alternate")})
        doc = pm.load_project(self.base)
        self.assertNotEqual(cache_path(doc, "code"), cache_path(doc, "other"))
        second = self.root / "map-two"
        pm.init_project(second, "same", "project-test")
        bind_workspace(second, "code", self.repo)
        self.assertNotEqual(cache_path(doc, "code"), cache_path(pm.load_project(second), "code"))

    def test_archive_preserves_original_identity_and_independent_status(self):
        path = self.record("REQ-old", "ObsoleteUniqueBody\n" * 20, kind="requirement", status="current", custom={"preserved": True})
        self.record("REQ-new", "Current replacement", kind="requirement")
        raw = path.read_bytes()
        with self.assertRaisesRegex(ValueError, "evidence"):
            archive_record(self.base, "REQ-old", "obsolete", "")
        result = archive_record(self.base, "REQ-old", "Old constraints superseded", "Checked replacement and implementation", "REQ-new")
        archived = self.base / result["documentation"]["archive_path"]
        self.assertEqual(archived.read_bytes(), raw)
        self.assertNotIn("ObsoleteUniqueBody", path.read_text(encoding="utf-8"))
        doc = pm.load_project(self.base)
        default = pm.read_record(doc, "REQ-old")
        self.assertEqual(default["record"]["status"], "current")
        self.assertIn("REQ-new", default["body"])
        self.assertEqual(default["record"]["custom"], {"preserved": True})
        self.assertEqual(pm.search_project(doc, "ObsoleteUniqueBody")["total"], 0)
        self.assertEqual(pm.search_project(doc, "ObsoleteUniqueBody", current_only=False)["total"], 1)
        read = pm.read_record(doc, "REQ-old", include_history=True, max_chars=30)
        self.assertIn("ObsoleteUniqueBody", read["body"])
        self.assertTrue(read["continuation"]["include_history"])
        self.assertFalse(archive_record(self.base, "REQ-old", "already", "checked")["changed"])
        archived.write_text("tampered", encoding="utf-8")
        self.assertIn("REQ-new", pm.read_record(pm.load_project(self.base), "REQ-old")["body"])
        with self.assertRaisesRegex(ValueError, "snapshot changed"):
            pm.read_record(pm.load_project(self.base), "REQ-old", include_history=True)

    def test_external_binding_keeps_source_and_survives_missing_original(self):
        source = self.root / "external.md"
        source.write_text("# Archived\nOldBoundUnique\n", encoding="utf-8")
        raw = source.read_bytes()
        self.manifest(sources=[{"source_id": "external", "path": "../external.md"}], bindings=[{"id": "EXT", "title": "EXT", "kind": "interface", "source_id": "external", "heading": "Archived"}])
        archive_record(self.base, "EXT", "obsolete", "Implementation removed this contract")
        self.assertEqual(source.read_bytes(), raw)
        source.unlink()
        doc = pm.load_project(self.base)
        self.assertIn("说明缺口", pm.read_record(doc, "EXT")["body"])
        self.assertIn("OldBoundUnique", pm.read_record(doc, "EXT", include_history=True)["body"])
        self.assertTrue(doc["validation"]["valid"])

    def test_archive_bytes_survive_git_line_ending_conversion(self):
        subprocess.run(["git", "init", "-q", str(self.base)], check=True, capture_output=True)
        path = self.record("OLD", "Windows original\nsecond line\n")
        raw = path.read_bytes().replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")
        path.write_bytes(raw)
        result = archive_record(self.base, "OLD", "obsolete", "Verified replacement")
        relative = result["documentation"]["archive_path"]
        subprocess.run(["git", "-C", str(self.base), "-c", "core.autocrlf=true", "add", "archive"], check=True, capture_output=True)
        stored = subprocess.check_output(["git", "-C", str(self.base), "show", ":" + relative])
        self.assertEqual(stored, raw)
        (self.base / relative).unlink()
        subprocess.run(["git", "-C", str(self.base), "-c", "core.autocrlf=false", "checkout-index", "--", relative], check=True, capture_output=True)
        self.assertIn("Windows original", pm.read_record(pm.load_project(self.base), "OLD", include_history=True)["body"])

    def test_export_isolates_old_body_and_preserves_old_links(self):
        self.record("OLD", "OnlyInArchiveBody")
        self.record("NEW", "[old path](OLD.md) and [[OLD]]")
        archive_record(self.base, "OLD", "obsolete", "verified", "NEW")
        output = self.base / "views/index.html"
        export_reader(pm.load_project(self.base), output, diagrams=False)
        payload = json.loads(output.with_name("docs.json").read_text(encoding="utf-8"))
        self.assertNotIn("OnlyInArchiveBody", output.read_text(encoding="utf-8"))
        self.assertNotIn("OnlyInArchiveBody", json.dumps(payload))
        old = next(r for r in payload["records"] if r["id"] == "OLD")
        self.assertIn("OnlyInArchiveBody", (output.parent / old["archive_page"]).read_text(encoding="utf-8"))
        new = next(r for r in payload["records"] if r["id"] == "NEW")
        self.assertEqual(new["body_html"].count('data-map-record="OLD"'), 2)

    def test_shared_external_body_cannot_leak_through_linked_document(self):
        source = self.root / "external.md"
        source.write_text("# Current\nOK\n# Archived\nOldSharedUnique\n", encoding="utf-8")
        self.manifest(sources=[{"source_id": "ext", "path": "../external.md"}], bindings=[
            {"id": rid, "title": rid, "kind": "interface", "source_id": "ext", "heading": rid}
            for rid in ("Current", "Archived")])
        self.record("REF", "[whole source](../../external.md)")
        archive_record(self.base, "Archived", "obsolete", "checked")
        output = self.base / "views/index.html"
        export_reader(pm.load_project(self.base), output, diagrams=False)
        self.assertNotIn("OldSharedUnique", output.with_name("docs.json").read_text(encoding="utf-8"))
        self.assertIn("OldSharedUnique", source.read_text(encoding="utf-8"))

    def test_legacy_archived_status_is_hidden_but_history_readable(self):
        self.record("LEGACY", "LegacyOldBody", status="archived")
        doc = pm.load_project(self.base)
        self.assertNotIn("LegacyOldBody", pm.read_record(doc, "LEGACY")["body"])
        self.assertIn("LegacyOldBody", pm.read_record(doc, "LEGACY", include_history=True)["body"])
        output = self.base / "views/index.html"
        export_reader(doc, output, diagrams=False)
        self.assertNotIn("LegacyOldBody", output.read_text(encoding="utf-8"))


if __name__ == "__main__": unittest.main()
