from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import re
import sys
import subprocess
import tempfile
import unittest

SCRIPTS = Path(__file__).resolve().parents[1] / "maintain-project-map" / "scripts"
sys.path.insert(0, str(SCRIPTS))
from archify_adapter import render_diagrams, find_node, PIN, VENDOR, diagram_targets
from project_map import HISTORICAL
from render_map import export_reader, markdown_html, safe_json


def fixture(root: Path) -> dict:
    source = root / "module.md"
    source.write_text("# 原记录\n\n用于按需阅读。\n", encoding="utf-8")
    rows = [
        {"id": "MOD-locate", "title": "定位当前项目", "kind": "module", "body": "# 定位当前项目\n\n用稳定项目 ID 定位地图。", "summary": "稳定项目 ID 定位地图。", "status": "current", "aliases": ["找地图"]},
        {"id": "MOD-records", "title": "读取原记录", "kind": "module", "body": "保留原文位置。", "summary": "按需读取目标条目。", "status": "current"},
        {"id": "MOD-reader", "title": "生成阅读页面", "kind": "module", "body": "由同一记录生成 A/B/C。", "summary": "阅读操作不调用模型。", "status": "current", "progress": "已有本地导出。", "gap": "长期真实使用待验证。"},
        {"id": "OLD", "title": "旧自动发布", "kind": "module", "body": "已退役。", "status": "retired"},
        {"id": "CHECK", "title": "验证范围", "kind": "verification", "body": "这是独立验证记录。", "status": "current"},
    ]
    for r in rows:
        r.update(path=str(source), line=1, end_line=3, source_text=source.read_text(encoding="utf-8"))
    rels = [{"from": {"project_id": "map-demo", "record_id": a}, "to": {"project_id": "map-demo", "record_id": b}, "relation": "flows_to", "reason": text} for a, b, text in [("MOD-locate", "MOD-records", "定位后读取"), ("MOD-records", "MOD-reader", "按需生成")]]
    rels.append({"from": {"project_id": "map-demo", "record_id": "MOD-records"}, "to": {"project_id": "other-map", "record_id": "MOD-reader"}, "relation": "uses", "reason": "只保存外部 ID"})
    return {"project": {"schema": "project-map/v1", "project_id": "map-demo", "name": "项目地图", "views": {"workflow_title": "生成项目阅读页面"}}, "manifest_path": str(root / "project.yaml"), "map_body": "# 项目目标\n\n长期理解和维护项目。", "records": rows, "relations": rels, "version": {"git_head": None, "dirty": False}, "fingerprint": "fingerprint-1"}


class ReaderSafetyTests(unittest.TestCase):
    def test_markdown_does_not_execute_html_or_links(self):
        result = markdown_html('# 标题\n\n<script>alert(1)</script>\n\n[bad](javascript:alert) [ok](https://example.com/x)\n\n```html\n<img src=x onerror=alert(2)>\n```')
        self.assertNotIn("<script>", result)
        self.assertNotIn("<img ", result)
        self.assertNotIn('href="javascript:', result)
        self.assertIn('href="https://example.com/x"', result)
        self.assertIn("&lt;script&gt;", result)
        self.assertRegex(result, r"<pre><code(?: [^>]*)?>")

    def test_markdown_preserves_readable_structure(self):
        result = markdown_html('# 对象\n\n**地图**与 `ID`。\n\n- 需求\n- 理由\n\n|对象|作用|\n|---|---|\n|地图|定位|\n')
        for markup in ["<h2>对象</h2>", "<strong>地图</strong>", "<code>ID</code>", "<ul>", "<table>", "<td>定位</td>"]:
            self.assertIn(markup, result)

    def test_json_cannot_escape_script_container(self):
        hostile = '</script><script>window.bad=1</script>\u2028&'
        encoded = safe_json({"body": hostile})
        self.assertNotIn("</script>", encoded)
        self.assertNotIn("\u2028", encoded)
        self.assertEqual(json.loads(encoded)["body"], hostile)

    def test_export_preserves_original_source_and_distinct_records(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data = fixture(root)
            data["records"][0]["body"] = "Projected content differs from original source."
            data["records"][1]["title"] = '</script><script>evil()</script>'
            output = root / "views/index.html"
            export_reader(data, output, mode="b", diagrams=False)
            payload = json.loads((output.parent / "docs.json").read_text(encoding="utf-8"))
            page = output.read_text(encoding="utf-8")
            self.assertEqual(payload["default_mode"], "b")
            self.assertEqual(payload["records"][0]["source_text"], "# 原记录\n\n用于按需阅读。\n")
            self.assertEqual(payload["records"][0]["body"], data["records"][0]["body"])
            self.assertNotIn('</script><script>evil()', page)
            self.assertEqual([r["id"] for r in payload["records"]], [r["id"] for r in data["records"]])
            self.assertEqual(payload["fingerprint"], "fingerprint-1")
            self.assertIn("原记录改变后需重新导出", page)
            self.assertNotIn("fetch(", page)
            self.assertNotIn("window.openai", page)

    def test_snapshot_source_is_not_reread(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); data = fixture(root)
            Path(data["records"][0]["path"]).write_text("changed after load", encoding="utf-8")
            export_reader(data, root / "index.html", diagrams=False)
            payload = json.loads((root / "docs.json").read_text(encoding="utf-8"))
            self.assertEqual(payload["records"][0]["source_text"], "# 原记录\n\n用于按需阅读。\n")

    def test_missing_source_excerpt_is_disclosed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); data = fixture(root)
            del data["records"][0]["source_text"]
            data["records"][0]["path"] = str(root / "missing.md")
            export_reader(data, root / "index.html", diagrams=False)
            payload = json.loads((root / "docs.json").read_text(encoding="utf-8"))
            self.assertIn("此快照未提供原文摘录", payload["records"][0]["source_note"])

    def test_source_collisions_rejected_before_any_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); data = fixture(root)
            with self.assertRaises(ValueError):
                export_reader(data, root / "project.yaml", diagrams=False)
            with self.assertRaises(ValueError):
                export_reader(data, root / "architecture.html")
            source = root / "source.html"
            source.write_text("original content", encoding="utf-8")
            data["records"][0]["path"] = str(source)
            with self.assertRaises(ValueError):
                export_reader(data, source, diagrams=False)
            self.assertEqual(source.read_text(encoding="utf-8"), "original content")
            self.assertFalse((root / "docs.json").exists())
            data["source_files"] = [{"path": str(root / "workflow.json")}]
            with self.assertRaises(ValueError):
                export_reader(data, root / "index.html")


class DiagramTests(unittest.TestCase):
    def test_reader_search_recovers_historical_alias_without_hiding_failed_module(self):
        try:
            node = find_node()
        except RuntimeError:
            self.skipTest("Node is unavailable")
        page = (SCRIPTS.parent / "assets/reader.html").read_text(encoding="utf-8")
        # Execute only the actual pure filtering function, with no DOM/browser.
        function = re.search(r"^function visible\(\).*", page, flags=re.M).group(0)
        records = [{"id": "OLD", "title": "旧入口", "aliases": ["分享卡片"], "status": "withdrawn", "kind": "module"}, {"id": "BROKEN", "title": "仍存在的模块", "status": "failed", "kind": "module"}, {"id": "EXP", "title": "失败探索", "kind": "exploration", "status": "current", "outcome": "failed"}]
        script = "const recordOrder=new Map();const records=" + json.dumps(records, ensure_ascii=False) + ";const historical=new Set(" + json.dumps(sorted(HISTORICAL)) + ");let state={history:false,verification:false,query:''};" + function + ";const current=visible().map(r=>r.id);state.query='分享卡片';const matched=visible().map(r=>r.id);process.stdout.write(JSON.stringify({current,matched}));"
        result = subprocess.run([node, "-e", script], capture_output=True, text=True, encoding="utf-8", timeout=10, check=True)
        self.assertEqual(json.loads(result.stdout), {"current": ["BROKEN", "EXP"], "matched": ["OLD"]})

    def test_actual_reader_native_focus_and_embedding_behavior(self):
        node = find_node()
        test_file = Path(__file__).with_name('reader-native-behavior.cjs')
        result = subprocess.run([node, str(test_file)], capture_output=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr.decode('utf-8'))
        page = (SCRIPTS.parent / 'assets/reader.html').read_text(encoding='utf-8')
        executable_script = page.split('<script>')[-1].split('</script>')[0]
        result = subprocess.run([node, '--check'], input=executable_script.encode('utf-8'), capture_output=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr.decode('utf-8'))

    def test_no_declaration_never_adopts_derived_graph_or_invents_structure(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); data = fixture(root)
            views = root / "views"; views.mkdir()
            old = views / "architecture.json"
            old.write_text('{"old":"derived graph"}', encoding="utf-8")
            specs = render_diagrams(data, views)
            self.assertTrue(all(spec["missing"] for spec in specs.values()))
            self.assertEqual(old.read_text(encoding="utf-8"), '{"old":"derived graph"}')

    def test_native_delivery_preserves_authored_sources_and_receipts(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); data = native_fixture(root)
            original = copy.deepcopy(data["diagram_sources"])
            # Rendering must use the frozen snapshot even when disk changes.
            for source in data["diagram_sources"].values():
                Path(source["source_path"]).write_text('changed after load', encoding="utf-8")
            specs = render_diagrams(data, root / "views", node=find_node())
            self.assertEqual(data["diagram_sources"], original)
            for kind in ("architecture", "workflow"):
                spec = specs[kind]
                self.assertEqual(spec.get("file"), kind + ".html", spec.get("reason"))
                raw = (root / "views" / (kind + ".json")).read_bytes()
                self.assertEqual(raw, original[kind]["source_text"].encode())
                self.assertEqual(json.loads(raw), original[kind]["ir"])
                page = (root / "views" / spec["file"]).read_bytes()
                canonical = (root / "views" / spec["canonical_file"]).read_bytes()
                self.assertIn(b'id="project-map-light-theme"', page)
                self.assertNotIn(b'id="project-map-light-theme"', canonical)
                self.assertIn(b'data-theme="light"', page)
                self.assertEqual(spec["record_nodes"], original[kind]["record_nodes"])
                self.assertEqual(spec["archify_commit"], PIN)
                receipt = json.loads((root / "views" / spec["receipt_file"]).read_text(encoding="utf-8"))
                for label, artifact in (("canonical", canonical), ("embedded", page)):
                    self.assertEqual(receipt[label]["sha256"], hashlib.sha256(artifact).hexdigest())
                self.assertEqual(receipt["native_delivery"]["artifact"]["sha256"], receipt["canonical"]["sha256"])
                self.assertEqual(receipt["native_delivery"]["specification"]["sha256"], hashlib.sha256(raw).hexdigest())
                self.assertTrue(receipt["native_delivery"]["ok"])
                self.assertEqual(Path(original[kind]["source_path"]).read_text(encoding="utf-8"), 'changed after load')
            self.assertIn('boundaries', original['architecture']['ir'])
            self.assertIn('groups', original['workflow']['ir'])
            self.assertTrue(any(e.get('role') == 'return' for e in original['workflow']['ir']['edges']))

    def test_native_schema_failure_keeps_docs_and_never_links_stale_artifact(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); data = native_fixture(root)
            data['diagram_sources'].pop('workflow')
            source = data['diagram_sources']['architecture']
            source['ir']['components'][0]['unsupported_field'] = 'invalid'
            source['source_text'] = json.dumps(source['ir'])
            source['source_sha256'] = hashlib.sha256(source['source_text'].encode()).hexdigest()
            views = root / 'views'; views.mkdir()
            (views / 'architecture.html').write_text('old light')
            (views / 'architecture.native.html').write_text('old canonical')
            result = export_reader(data, views / 'index.html', node=find_node())
            spec = result['diagrams']['architecture']
            self.assertIsNone(spec['file'])
            self.assertIsNone(spec['canonical_file'])
            self.assertTrue(spec['errors'])
            self.assertEqual((views / 'architecture.html').read_text(), 'old light')
            self.assertEqual((views / 'architecture.native.html').read_text(), 'old canonical')
            self.assertTrue((views / 'index.html').is_file())

    def test_every_native_sidecar_is_protected_even_for_missing_declared_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); data = fixture(root)
            for target in diagram_targets(root):
                data['diagram_sources'] = {'architecture': {'source_path': str(target)}}
                with self.assertRaises(ValueError):
                    export_reader(data, root / 'index.html')
                with self.assertRaises(ValueError):
                    render_diagrams(data, root)
                self.assertFalse(target.exists())
            self.assertFalse((root / 'docs.json').exists())

    def test_renderer_failure_does_not_reference_stale_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); data = native_fixture(root)
            views = root / "views"; views.mkdir()
            (views / "architecture.html").write_text("old diagram", encoding="utf-8")
            result = export_reader(data, views / "index.html", node=str(root / "missing-node"))
            self.assertTrue((views / "index.html").exists())
            self.assertIsNone(result["diagrams"]["architecture"]["file"])
            self.assertIn("Node executable not found", result["diagrams"]["architecture"]["reason"])


def native_fixture(root):
    data = fixture(root)
    data['diagram_sources'] = {}
    examples = {'architecture': 'web-app.architecture.json', 'workflow': 'agent-tool-call.workflow.json'}
    for kind, example in examples.items():
        raw = (VENDOR / 'examples' / example).read_bytes()
        ir = json.loads(raw)
        source_path = root / ('authored-' + kind + '.json')
        source_path.write_bytes(raw)
        ids = [n['id'] for n in ir['components' if kind == 'architecture' else 'nodes']][:2]
        data['diagram_sources'][kind] = {
            'source_path': str(source_path), 'source_text': raw.decode('utf-8'),
            'source_sha256': hashlib.sha256(raw).hexdigest(), 'ir': ir,
            'node_records': {ids[0]: ['MOD-locate', 'MOD-records'], ids[1]: ['MOD-records']},
            'record_nodes': {'MOD-locate': [ids[0]], 'MOD-records': ids}, 'errors': [], 'warnings': []}
    return data


if __name__ == "__main__":
    unittest.main()
