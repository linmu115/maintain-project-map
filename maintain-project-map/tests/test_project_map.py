"""Behavioral checks for source identity, bounded retrieval and safe lifecycle."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import subprocess
import sys

MODULE = Path(__file__).resolve().parents[1] / "scripts/project_map.py"
sys.path.insert(0, str(MODULE.parent))
SPEC = importlib.util.spec_from_file_location("project_map", MODULE)
pm = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(pm)


class MapTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.base = self.root / "map"
        pm.init_project(self.base, "中文示例", "project-one", "skill")

    def manifest(self, **updates):
        p = self.base / "project.yaml"
        data = json.loads(p.read_text(encoding="utf-8"))
        data.update(updates)
        p.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

    def record(self, rid, body="说明正文\n第二行\n", **meta):
        path = self.base / "records" / f"{rid}.md"
        path.parent.mkdir(exist_ok=True)
        data = {"id": rid, "kind": "module", "title": rid, **meta}
        path.write_bytes(("---\n" + json.dumps(data, ensure_ascii=False) + "\n---\n" + body).encode("utf-8"))
        return path

    def test_init_idempotent_and_does_not_scan(self):
        before = (self.base / "project.yaml").read_bytes()
        (self.base / "random.md").write_text("not a record", encoding="utf-8")
        result = pm.init_project(self.base, "different name")
        self.assertFalse(result["created"])
        self.assertEqual(before, (self.base / "project.yaml").read_bytes())
        self.assertEqual(pm.load_project(self.base)["records"], [])
        self.assertFalse((self.base / ".git").exists())

    def test_heading_binding_and_fingerprint_tracks_live_source(self):
        source = self.root / "spec.md"
        source.write_text("# Design\n\n## 地图\n当前定义\n### 细节\n内容\n## Other\nelse\n", encoding="utf-8")
        self.manifest(sources=[{"source_id": "spec", "path": "../spec.md", "format": "markdown"}], bindings=[{"id": "OBJ-map", "kind": "object", "source_id": "spec", "heading": "地图", "title": "地图"}])
        a = pm.load_project(self.base)
        r = a["records"][0]
        self.assertEqual((r["line"], r["end_line"]), (3, 6))
        self.assertIn("细节", r["body"])
        self.assertNotIn("Other", r["body"])
        self.assertEqual(r["path"], str(source.resolve()))
        source.write_text(source.read_text(encoding="utf-8").replace("当前定义", "新的定义"), encoding="utf-8")
        b = pm.load_project(self.base)
        self.assertNotEqual(a["fingerprint"], b["fingerprint"])
        self.assertIn("新的定义", b["records"][0]["body"])

    def test_table_binding_by_id_survives_line_movement(self):
        source = self.base / "requirements.md"
        text = "| 编号 | 需求 |\n| --- | --- |\n| REQ-1 | 中文查询 \\| 别名 |\n| REQ-2 | other |\n"
        source.write_text(text, encoding="utf-8")
        self.manifest(sources=[{"source_id": "requirements", "path": "requirements.md", "format": "markdown-table", "id_column": "编号"}], bindings=[{"id": "REQ-1", "kind": "requirement", "source_id": "requirements", "row_id": "REQ-1"}])
        a = pm.load_project(self.base)["records"][0]
        source.write_text("# Intro\n\n" + text, encoding="utf-8")
        b = pm.load_project(self.base)["records"][0]
        self.assertEqual(a["body"], b["body"])
        self.assertEqual(a["line"] + 2, b["line"])
        self.assertEqual(b["table_fields"]["需求"], "中文查询 | 别名")

    def test_duplicate_ids_and_dangling_local_refs(self):
        self.record("one", relations=[{"relation": "consumes", "to": {"record_id": "missing"}}])
        self.record("two", id="one")
        result = pm.load_project(self.base)["validation"]
        self.assertFalse(result["valid"])
        self.assertEqual({e["code"] for e in result["errors"]}, {"duplicate_id", "dangling_local_relation"})
        with self.assertRaises(pm.MapError):
            pm.read_record(pm.load_project(self.base), "one")

    def test_old_chinese_alias_and_retirement_remain_reachable(self):
        original = "# 曾经可用\n\n功能说明保持不变。\n"
        self.record("old", original, aliases=["以前的自动发布"], custom={"keep": True})
        self.record("new")
        pm.set_lifecycle(self.base, "old", "retired", "用户改为本地导出", "new")
        doc = pm.load_project(self.base)
        old = pm.read_record(doc, "old")
        self.assertEqual(old["body"], original)
        self.assertEqual(old["record"]["status"], "retired")
        self.assertEqual(old["record"]["custom"], {"keep": True})
        self.assertEqual(pm.search_project(doc, "自动发布", current_only=False)["results"][0]["id"], "old")
        self.assertEqual(pm.search_project(doc, "自动发布", current_only=True)["total"], 0)
        self.assertEqual(old["record"]["lifecycle"]["successor"], {"record_id": "new"})

    def test_multi_keyword_filters_ranking_and_literal_snippets(self):
        self.record("Z-api", "# 说明\n返回提交接口的错误；失败时保留任务。\n", kind="interface", title="任务提交", aliases=["submitJob"])
        self.record("A-background", "过去分析提交接口的错误。", kind="exploration", title="一次调试")
        self.record("B-old", "提交接口的错误", kind="interface", status="archived")
        doc = pm.load_project(self.base)
        result = pm.search_project(doc, "接口 错误")
        self.assertEqual(result["results"][0]["id"], "Z-api")
        self.assertEqual(result["total"], 2)
        hit = result["results"][0]["snippet"]
        self.assertEqual(hit["text"], "返回提交接口的错误；失败时保留任务。")
        self.assertEqual(hit["line"], doc["records"][-1]["line"] + 1)
        self.assertEqual(pm.search_project(doc, "接口 错误", kinds=["interface"])["total"], 1)
        self.assertEqual(pm.search_project(doc, "SUBMITJOB")["results"][0]["match"], "exact")
        self.assertEqual(pm.search_project(doc, "B-old")["total"], 0)
        self.assertEqual(pm.search_project(doc, "B-old", current_only=False)["results"][0]["id"], "B-old")

    def test_disclosed_cjk_fallback_and_no_silent_filter_expansion(self):
        self.record("IF-query", "按项目 ID 查询记录，分段读取正文。", kind="interface", title="查询与分段读取")
        self.record("MOD-preview", "生成页面并启动本机服务。", title="阅读预览")
        doc = pm.load_project(self.base)
        result = pm.search_project(doc, "怎么查询项目记录")
        self.assertEqual(result["match_mode"], "cjk_bigrams")
        self.assertEqual(result["results"][0]["id"], "IF-query")
        self.assertEqual(result["results"][0]["match"], "partial_terms")
        self.assertEqual(pm.search_project(doc, "怎么查询项目记录", match="phrase")["total"], 0)
        self.assertEqual(pm.search_project(doc, "查询", kinds=["verification"])["total"], 0)
        self.assertEqual(pm.search_project(doc, "完全无关的天文观测问题")["total"], 0)

    def test_search_pages_and_cross_field_words(self):
        for n in range(5):
            self.record(f"R-{n}", "读取参数说明", kind="interface", title=f"接口 {n}")
        doc = pm.load_project(self.base)
        first = pm.search_project(doc, "接口 参数", limit=2)
        second = pm.search_project(doc, "接口 参数", limit=2, offset=first["next_offset"])
        self.assertEqual(first["total"], 5)
        self.assertTrue(set(r["id"] for r in first["results"]).isdisjoint(r["id"] for r in second["results"]))
        self.assertEqual(pm.search_project(doc, "接口 missing", match="all")["total"], 0)
        self.assertEqual(pm.search_project(doc, "接口 missing")["match_mode"], "any_terms")

    def test_sources_bind_workspace_and_mark_changes_for_review(self):
        import hashlib
        repo = self.root / "source-checkout"
        repo.mkdir()
        source = repo / "entry.py"
        source.write_text("def main(): pass\n", encoding="utf-8")
        baseline = hashlib.sha256(source.read_bytes()).hexdigest()
        self.manifest(workspaces=[{"id": "source", "path": "../source-checkout"}])
        self.record("M", sources=[{"role": "implementation", "workspace_id": "source", "path": "entry.py", "symbol": "main", "reviewed_sha256": baseline}])
        result = pm.read_record(pm.load_project(self.base), "M")["resolved_sources"][0]
        self.assertEqual(result["resolved_path"], str(source.resolve()))
        self.assertEqual(result["workspace_root"], str(repo.resolve()))
        self.assertEqual(result["review"], "unchanged_since_review")
        self.assertEqual(result["symbol_check"], "found")
        source.write_text("def main(): return 1\n", encoding="utf-8")
        changed = pm.read_record(pm.load_project(self.base), "M")
        self.assertEqual(changed["resolved_sources"][0]["review"], "needs_review")
        self.assertEqual(changed["record"]["status"], "current")

    def test_sources_do_not_guess_workspace_or_claim_unchecked_freshness(self):
        self.record("M", sources=[{"path": "map.md"}, {"workspace_id": "missing", "path": "map.md"},
                                  {"workspace_id": "known", "path": "../map/map.md"}])
        self.manifest(workspaces=[{"id": "known", "path": "../source-checkout"}])
        sources = pm.read_record(pm.load_project(self.base), "M")["resolved_sources"]
        self.assertEqual(sources[0]["availability"], "exists")
        self.assertEqual(sources[0]["workspace_binding"], "undeclared")
        self.assertEqual(sources[0]["review"], "no_baseline")
        self.assertEqual(sources[1]["availability"], "unresolved_workspace")
        self.assertEqual(sources[2]["availability"], "outside_workspace")

    def test_compact_read_keeps_continuation_and_full_metadata_is_opt_in(self):
        self.record("R", "甲乙丙丁戊己\n", custom={"long": "detail"}, gap="尚未验证错误恢复")
        cmd = [sys.executable, "-X", "utf8", str(MODULE), "read", str(self.base), "R", "--max-chars", "3"]
        run = lambda argv: json.loads(subprocess.run(argv, capture_output=True, text=True, encoding="utf-8", check=True, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)).stdout)
        compact = run(cmd)
        self.assertNotIn("custom", compact["record"])
        self.assertEqual(compact["record"]["gap"], "尚未验证错误恢复")
        self.assertIn("custom", run(cmd + ["--detail", "full"])["record"])
        token = compact["continuation"]
        next_part = run(cmd + ["--offset", str(token["offset"]), "--record-fingerprint", token["record_fingerprint"]])
        self.assertEqual(compact["body"] + next_part["body"], "甲乙丙丁戊己")

    def test_compact_read_preserves_outcome_and_applicability(self):
        from record_search import compact_response
        self.record("E", kind="exploration", outcome="failed", applicability="仅旧版本", coverage_note="未检查新版")
        compact = compact_response("read", pm.read_record(pm.load_project(self.base), "E"))
        self.assertEqual(compact["record"]["outcome"], "failed")
        self.assertEqual(compact["record"]["applicability"], "仅旧版本")
        self.assertEqual(compact["record"]["coverage_note"], "未检查新版")

    def test_failed_exploration_is_not_retired_functionality(self):
        self.record("EXP-1", kind="exploration", outcome="failed", status="current")
        with self.assertRaisesRegex(pm.MapError, "Exploration outcomes"):
            pm.set_lifecycle(self.base, "EXP-1", "retired", "not equivalent")
        self.assertEqual(pm.read_record(pm.load_project(self.base), "EXP-1")["record"]["outcome"], "failed")

    def test_registry_reports_ambiguous_worktree_locations(self):
        registry = self.root / "registry.json"
        other = self.root / "second-worktree"
        pm.init_project(other, "same logical project", "project-one")
        pm.register_project(self.base, registry)
        pm.register_project(other, registry)
        pm.register_project(other, registry)
        result = pm.resolve_project("project-one", registry, current=self.root)
        self.assertEqual(result["status"], "ambiguous")
        self.assertEqual(len(result["locations"]), 2)
        self.assertEqual(pm.resolve_project("project-one", registry, current=other)["manifest_path"], str(other / "project.yaml"))
        self.assertEqual(pm.resolve_project("project-one", registry, manifest=self.base)["selection"], "explicit")
        self.assertEqual(pm.resolve_project("unknown", registry)["status"], "unresolved")

    def test_parallel_registry_writers_preserve_both_projects(self):
        registry = self.root / "registry.json"
        other = self.root / "other-project"
        pm.init_project(other, "Another project", "project-two")
        helper = self.root / "register_child.py"
        helper.write_text('''import importlib.util, os, pathlib, sys, time
spec = importlib.util.spec_from_file_location("project_map", sys.argv[1])
pm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pm)
root = pathlib.Path(sys.argv[3]).parent
(root / ("ready-" + str(os.getpid()))).write_text("ready")
deadline = time.monotonic() + 8
while len(list(root.glob("ready-*"))) < 2:
    if time.monotonic() > deadline:
        raise RuntimeError("Parallel writer did not arrive")
    time.sleep(0.01)
original = pm._registry
def slow_read(path):
    data = original(path)
    time.sleep(0.25)
    return data
pm._registry = slow_read
pm.register_project(sys.argv[2], sys.argv[3])
''', encoding="utf-8")
        children = [subprocess.Popen([sys.executable, "-X", "utf8", str(helper), str(MODULE), str(base), str(registry)], creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8") for base in (self.base, other)]
        try:
            for child in children:
                out, err = child.communicate(timeout=15)
                self.assertEqual(child.returncode, 0, out + err)
        finally:
            for child in children:
                if child.poll() is None:
                    child.kill()
                    child.communicate()
        registered = json.loads(registry.read_text(encoding="utf-8"))
        self.assertEqual(set(registered["projects"]), {"project-one", "project-two"})
        self.assertFalse(registry.with_name("registry.json.lock").exists())

    def test_unchanged_registration_does_not_rewrite_registry(self):
        from unittest.mock import patch
        registry = self.root / "registry.json"
        self.assertTrue(pm.register_project(self.base, registry)["changed"])
        before = registry.stat().st_mtime_ns
        with patch.object(pm, "_atomic_write", wraps=pm._atomic_write) as write:
            self.assertFalse(pm.register_project(self.base, registry)["changed"])
            write.assert_not_called()
        self.assertEqual(before, registry.stat().st_mtime_ns)

    def test_busy_registry_retains_unknown_lock(self):
        registry = self.root / "registry.json"
        lock = self.root / "registry.json.lock"
        lock.write_text("unknown writer; do not remove", encoding="utf-8")
        with self.assertRaisesRegex(pm.MapError, "registry busy"):
            pm.register_project(self.base, registry, lock_timeout=0.03)
        self.assertEqual(lock.read_text(encoding="utf-8"), "unknown writer; do not remove")
        self.assertFalse(registry.exists())

    def test_external_links_are_thin_and_never_resolved_implicitly(self):
        self.record("caller", relations=[{"relation": "consumes", "to": {"project_id": "unregistered-project", "record_id": "IF-1"}, "reason": "需要它提供的能力"}])
        doc = pm.load_project(self.base)
        self.assertTrue(doc["validation"]["valid"])
        result = pm.related_records(doc, "caller")
        self.assertEqual(result["relations"][0]["to"]["project_id"], "unregistered-project")
        self.assertEqual(len(doc["records"]), 1)

    def test_bounded_read_continues_without_lost_characters(self):
        body = "第一行文字\n第二行文字\n第三行文字\n"
        self.record("long", body)
        doc = pm.load_project(self.base)
        parts, offset = [], 0
        while True:
            result = pm.read_record(doc, "long", offset=offset, max_chars=4, max_lines=1)
            parts.append(result["body"])
            if result["continuation"] is None:
                break
            self.assertGreater(result["continuation"]["offset"], offset)
            offset = result["continuation"]["offset"]
        self.assertEqual("".join(parts), body)
        self.assertEqual(result["receipt"], "opened_partial")

    def test_bound_records_never_overwritten_by_lifecycle_helper(self):
        source = self.base / "source.md"
        source.write_text("# Important\nKeep original\n", encoding="utf-8")
        self.manifest(sources=[{"source_id": "s", "path": "source.md"}], bindings=[{"id": "source", "kind": "module", "source_id": "s"}])
        before = source.read_bytes()
        with self.assertRaisesRegex(pm.MapError, "existing source"):
            pm.set_lifecycle(self.base, "source", "retired", "reason")
        self.assertEqual(source.read_bytes(), before)

    def test_generated_html_not_accepted_as_source(self):
        self.manifest(sources=[{"source_id": "html", "path": "view.html"}])
        with self.assertRaisesRegex(pm.MapError, "generated HTML"):
            pm.load_project(self.base)

    def test_heading_in_fence_does_not_affect_binding(self):
        source = self.base / "source.md"
        source.write_text("# A\n```md\n# A\n```\nbody\n# B\n", encoding="utf-8")
        self.manifest(sources=[{"source_id": "s", "path": "source.md"}], bindings=[{"id": "a", "kind": "object", "source_id": "s", "heading": "A"}])
        record = pm.load_project(self.base)["records"][0]
        self.assertEqual(record["end_line"], 5)

    def test_discovery_stops_at_nearest_map_and_explicit_boundary(self):
        deep = self.base / "src" / "feature"
        deep.mkdir(parents=True)
        found = pm.discover_project(deep, self.root)
        self.assertEqual(found["manifest_path"], str(self.base / "project.yaml"))
        self.assertEqual(pm.discover_project(deep, self.base / "src")["status"], "unresolved")
        conventional = self.root / "other-project" / "docs" / "project"
        pm.init_project(conventional, project_id="another")
        self.assertEqual(pm.discover_project(self.root / "other-project", self.root)["project_id"], "another")

    def test_yaml_date_metadata_is_portable_and_preserved(self):
        path = self.record("date")
        path.write_text("---\nid: date\nkind: module\ntitle: Date\nchecked_at: 2026-09-15\n---\nBody\n", encoding="utf-8")
        doc = pm.load_project(self.base)
        self.assertEqual(doc["records"][0]["checked_at"], "2026-09-15")
        pm.set_lifecycle(self.base, "date", "retired", "New requirement")
        self.assertEqual(pm.load_project(self.base)["records"][0]["checked_at"], "2026-09-15")

    def test_retirement_preserves_body_line_endings(self):
        body = "# Module\r\n\r\nExact body text\r\n"
        self.record("crlf", body)
        pm.set_lifecycle(self.base, "crlf", "retired", "Requirements changed")
        self.assertEqual(pm.read_record(pm.load_project(self.base), "crlf")["body"], body)

    def test_continuation_detects_source_changes(self):
        path = self.record("long", "abcdefg")
        first = pm.read_record(pm.load_project(self.base), "long", max_chars=3)
        path.write_text(path.read_text(encoding="utf-8") + "new", encoding="utf-8")
        with self.assertRaisesRegex(pm.MapError, "sources changed"):
            pm.read_record(pm.load_project(self.base), "long", offset=3, expected_fingerprint=first["continuation"]["fingerprint"])

    def test_heading_keeps_literal_hash_in_name(self):
        self.assertEqual(pm._headings("# C#\n## Closing ###\n"), [(1, 1, "C#"), (2, 2, "Closing")])

    def test_raw_table_excerpt_and_hash_share_load_snapshot(self):
        import hashlib
        source = self.base / "requirements.md"
        original = "| 编号 | 需求 |\r\n| --- | --- |\r\n| R1 | 原始正文 |\r\n"
        source.write_bytes(original.encode("utf-8"))
        self.manifest(sources=[{"source_id": "s", "path": "requirements.md", "format": "markdown-table", "id_column": "编号"}], bindings=[{"id": "R1", "kind": "requirement", "source_id": "s"}])
        doc = pm.load_project(self.base)
        source.write_text("Changed after loading", encoding="utf-8")
        record = doc["records"][0]
        self.assertEqual(record["source_text"], "| R1 | 原始正文 |\r\n")
        self.assertEqual(record["source_sha256"], hashlib.sha256(original.encode("utf-8")).hexdigest())
        self.assertNotEqual(record["source_text"], record["body"])
        self.assertNotIn("source_text", pm.read_record(doc, "R1")["record"])

    def test_same_declared_path_is_read_once_per_load(self):
        from unittest.mock import patch
        self.manifest(sources=[{"source_id": "first", "path": "map.md"}, {"source_id": "second", "path": "map.md"}], bindings=[{"id": "first", "kind": "object", "source_id": "first"}, {"id": "second", "kind": "object", "source_id": "second"}])
        original = Path.read_bytes
        reads = []
        def counted(path):
            reads.append(path)
            return original(path)
        with patch.object(Path, "read_bytes", counted):
            doc = pm.load_project(self.base)
        self.assertEqual(reads.count(self.base / "map.md"), 1)
        self.assertEqual(doc["map_body"], doc["records"][0]["source_text"])
        self.assertEqual(doc["records"][0]["source_sha256"], doc["records"][1]["source_sha256"])

    def test_cross_drive_fingerprint_key_uses_absolute_fallback(self):
        import ntpath
        from pathlib import PureWindowsPath
        from unittest.mock import patch
        with patch.object(pm.os.path, "relpath", ntpath.relpath):
            self.assertEqual(pm._fingerprint_path(PureWindowsPath("D:/external/spec.md"), PureWindowsPath("C:/project/map")), "D:/external/spec.md")
        self.record("external")
        with patch.object(pm.os.path, "relpath", side_effect=ValueError("separate mounts")):
            doc = pm.load_project(self.base)
        self.assertEqual(len(doc["fingerprint"]), 64)
        self.assertTrue(doc["validation"]["valid"])

    def test_read_receipt_includes_scoped_git_context_and_source_hash(self):
        from unittest.mock import patch
        self.record("versioned")
        context = {"git_root": "/map-repository", "git_head": "abc123", "branch": "feature", "dirty": True, "dirty_scope": "Declared map files"}
        with patch.object(pm, "_git_version", return_value=context):
            doc = pm.load_project(self.base)
        receipt = pm.read_record(doc, "versioned", max_chars=3)
        self.assertEqual(receipt["version"]["git_head"], "abc123")
        self.assertTrue(receipt["version"]["dirty"])
        self.assertIn("Map directory checkout only", receipt["version"]["context_scope"])
        self.assertIn("other repositories", receipt["version"]["context_scope"])
        self.assertEqual(len(receipt["record"]["source_sha256"]), 64)

    def test_native_diagram_snapshot_tracks_content_without_rewriting_ir(self):
        import hashlib
        self.record("MOD-queue")
        graph = self.base / "architecture.json"
        ir = {"schema_version": 1, "diagram_type": "architecture", "meta": {"title": "原生架构", "views": [{"id": "reading-view"}]},
              "components": [{"id": "native.queue", "type": "backend", "label": "队列", "custom": {"keep": True}}], "extra": [1, 2]}
        raw = (json.dumps(ir, ensure_ascii=False, indent=2) + "\r\n").encode("utf-8")
        graph.write_bytes(raw)
        self.manifest(archify={"architecture": {"source": "architecture.json", "node_records": {"native.queue": ["MOD-queue"]}, "repo_root": ".."}})
        first = pm.load_project(self.base)
        snapshot = first["diagram_sources"]["architecture"]
        self.assertEqual(snapshot["ir"], ir)
        self.assertEqual(snapshot["source_text"].encode("utf-8"), raw)
        self.assertEqual(snapshot["source_sha256"], hashlib.sha256(raw).hexdigest())
        self.assertEqual(snapshot["source_path"], str(graph))
        self.assertEqual(snapshot["repo_root"], str(self.root))
        self.assertIn({"path": str(graph), "sha256": snapshot["source_sha256"]}, first["source_files"])
        changed = {**ir, "meta": {"title": "后来改变"}}
        graph.write_text(json.dumps(changed), encoding="utf-8")
        second = pm.load_project(self.base)
        self.assertNotEqual(first["fingerprint"], second["fingerprint"])
        self.assertEqual(snapshot["ir"], ir)
        self.assertEqual(snapshot["source_text"].encode("utf-8"), raw)

    def test_native_node_record_bindings_are_many_to_many_and_checked_individually(self):
        self.record("A")
        self.record("B", status="retired")
        graph = self.base / "workflow.json"
        graph.write_text(json.dumps({"nodes": [{"id": "n1"}, {"id": "n2"}, {"id": "n3"}]}), encoding="utf-8")
        self.manifest(archify={"workflow": {"source": "workflow.json", "node_records": {"n1": ["A", "B", "missing", "A", {}], "n2": ["B"], "unknown": ["A"], "n3": "A"}}})
        doc = pm.load_project(self.base)
        snapshot = doc["diagram_sources"]["workflow"]
        self.assertEqual(snapshot["node_records"], {"n1": ["A", "B"], "n2": ["B"]})
        self.assertEqual(snapshot["record_nodes"], {"A": ["n1"], "B": ["n1", "n2"]})
        self.assertEqual({w["code"] for w in snapshot["warnings"]}, {"node_binding_invalid", "record_binding_invalid", "historical_record_binding"})
        self.assertTrue(doc["validation"]["valid"])
        self.assertEqual(pm.read_record(doc, "B")["record"]["status"], "retired")

    def test_missing_or_invalid_native_json_leaves_records_readable(self):
        self.record("A")
        invalid = self.base / "invalid.json"
        invalid.write_text("{broken", encoding="utf-8")
        self.manifest(archify={"architecture": {"source": "invalid.json"}, "workflow": {"source": "missing.json"}})
        doc = pm.load_project(self.base)
        self.assertTrue(doc["validation"]["valid"])
        self.assertEqual(pm.read_record(doc, "A")["record"]["id"], "A")
        for kind, filename in (("architecture", "invalid.json"), ("workflow", "missing.json")):
            snapshot = doc["diagram_sources"][kind]
            self.assertEqual(snapshot["source_path"], str(self.base / filename))
            self.assertIsNone(snapshot["ir"])
            self.assertTrue(snapshot["errors"])
        self.assertEqual({w["code"] for w in doc["validation"]["warnings"]}, {"diagram_source_error"})
        self.assertIsNotNone(doc["diagram_sources"]["architecture"]["source_sha256"])
        self.assertIsNone(doc["diagram_sources"]["workflow"]["source_sha256"])

    def test_native_bom_snapshot_roundtrips_and_shared_source_is_read_once(self):
        import hashlib
        from unittest.mock import patch
        graph = self.base / "shared.json"
        raw = b"\xef\xbb\xbf" + '{"components":[{"id":"a"}],"nodes":[{"id":"w"}],"meta":{"title":"中文"}}\r\n'.encode("utf-8")
        graph.write_bytes(raw)
        self.manifest(archify={"architecture": {"source": "shared.json"}, "workflow": {"source": "shared.json"}})
        original = Path.read_bytes
        reads = []
        def counted(path):
            reads.append(path)
            return original(path)
        with patch.object(Path, "read_bytes", counted):
            doc = pm.load_project(self.base)
        self.assertEqual(reads.count(graph), 1)
        for snapshot in doc["diagram_sources"].values():
            self.assertEqual(snapshot["source_text"].encode("utf-8"), raw)
            self.assertEqual(snapshot["source_sha256"], hashlib.sha256(raw).hexdigest())
            self.assertEqual(snapshot["ir"]["meta"]["title"], "中文")
            self.assertFalse(snapshot["errors"])

    def test_diagram_sources_are_only_explicit_and_do_not_reindex_views(self):
        views = self.base / "views"
        views.mkdir()
        (views / "derived.json").write_text('{"nodes":[]}', encoding="utf-8")
        (self.base / "architecture.json").write_text('{"components":[]}', encoding="utf-8")
        doc = pm.load_project(self.base)
        self.assertEqual(doc["diagram_sources"], {})
        self.assertEqual(len(doc["source_files"]), 2)
        self.assertFalse(doc["validation"]["warnings"])

    def test_export_cannot_overwrite_declared_missing_native_source(self):
        import contextlib
        import io
        target = self.base / "not-created-yet.json"
        self.manifest(archify={"architecture": {"source": target.name}})
        error = io.StringIO()
        with contextlib.redirect_stderr(error):
            code = pm.cli(["export", str(self.base), "--output", str(target)])
        self.assertEqual(code, 2)
        self.assertIn("separate from project source files", error.getvalue())
        self.assertFalse(target.exists())

    def test_unknown_diagram_declaration_reports_warning_without_blocking_map(self):
        self.manifest(archify={"unknown_kind": {"source": "ignore.json"}, "architecture": "wrong shape"})
        doc = pm.load_project(self.base)
        self.assertEqual(set(doc["diagram_sources"]), {"architecture"})
        self.assertTrue(doc["diagram_sources"]["architecture"]["errors"])
        self.assertTrue(doc["validation"]["valid"])
        self.assertIn("diagram_kind_unknown", {w["code"] for w in doc["validation"]["warnings"]})

    def test_map_git_status_is_scoped_to_declared_files(self):
        from unittest.mock import patch
        calls = []
        class Result:
            returncode = 0
            stdout = str(self.root)
        def fake_run(args, **kwargs):
            calls.append(args)
            return Result()
        with patch.object(pm.subprocess, "run", fake_run):
            pm.load_project(self.base)
        status = next(args for args in calls if "status" in args)
        paths = status[status.index("--") + 1:]
        self.assertEqual(set(paths), {str(self.base / "project.yaml"), str(self.base / "map.md")})


if __name__ == "__main__":
    unittest.main()
