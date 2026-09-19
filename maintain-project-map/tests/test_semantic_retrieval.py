"""Offline behavior tests. Real model smoke checks are separate from this suite."""
import json
from contextlib import closing
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import project_map as pm
import semantic_retrieval as sr
from record_search import compact_response


class FakeEncoder:
    dimensions = 3
    space_id = "test-space-v1"
    model_id = "offline-test-only"

    def __init__(self, cache_root):
        self.cache_root = cache_root
        self.calls = []

    def encode(self, texts, *, query=False):
        self.calls.append((list(texts), query))
        return [[1., .02, .01] if any(t in text for t in ("开机", "启动", "launch")) else [.01, 1., .02] for text in texts]


class SemanticTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.base = self.root / "map"
        pm.init_project(self.base, "查询样例", "same-stable-project", "skill")
        self.encoder = FakeEncoder(self.root / "cache")
        loader = patch.object(sr, "load_encoder", return_value=self.encoder)
        loader.start()
        self.addCleanup(loader.stop)

    def record(self, rid, body, **meta):
        path = self.base / "records" / f"{rid}.md"
        path.parent.mkdir(exist_ok=True)
        data = {"id": rid, "kind": "interface", "title": rid, **meta}
        path.write_bytes(("---\n" + json.dumps(data, ensure_ascii=False) + "\n---\n" + body).encode("utf-8"))
        return path

    def search(self, query="开机后第一步做什么", **kwargs):
        return pm.search_project(pm.load_project(self.base), query, retrieval="hybrid", **kwargs)

    def test_semantic_synonym_and_literal_source_location(self):
        self.record("IF-start", "# 程序起点\n\n调用 launch_main 引导服务。\n", title="启动入口")
        self.record("IF-save", "每日备份数据库。", title="数据留存")
        doc = pm.load_project(self.base)
        self.assertEqual(pm.search_project(doc, "开机后第一步做什么")["results"], [])
        result = self.search()
        hit = result["results"][0]
        self.assertEqual(hit["id"], "IF-start")
        self.assertEqual(hit["retrieved_by"], ["semantic"])
        self.assertEqual(hit["match"], "semantic")
        self.assertIn(hit["snippet"]["text"], pm.read_record(doc, hit["id"])["body"])
        self.assertEqual(hit["snippet"]["line"], next(r["line"] for r in doc["records"] if r["id"] == "IF-start"))
        self.assertEqual(result["retrieval"]["mode"], "hybrid")
        compact = compact_response("search", result)
        self.assertNotIn("diagnostics", compact["retrieval"])
        self.assertNotIn("rrf_score", compact["results"][0])
        self.assertNotIn("semantic_similarity", compact["results"][0])
        self.assertEqual(compact["results"][0]["retrieved_by"], ["semantic"])

    def test_physically_archived_body_is_outside_default_semantic_candidates(self):
        from document_archive import archive_record
        self.record("OLD", "启动 launch UniqueObsoleteBody")
        self.record("NEW", "Current launch contract")
        self.search()
        archive_record(self.base, "OLD", "Superseded explanation", "Compared with NEW", "NEW")
        self.encoder.calls.clear()
        result = self.search()
        self.assertNotIn("OLD", {r["id"] for r in result["results"]})
        self.assertNotIn("UniqueObsoleteBody", str(self.encoder.calls))
        historical = self.search("UniqueObsoleteBody", current_only=False)
        self.assertIn("OLD", {r["id"] for r in historical["results"]})
        self.assertNotIn("OLD", {r["id"] for r in self.search()["results"]})

    def test_same_status_kind_and_module_scope_in_both_channels(self):
        self.record("MOD-one", "模块", kind="module")
        self.record("MOD-two", "模块", kind="module")
        self.record("IF-valid", "启动 launch", module_id="MOD-one")
        self.record("IF-old", "启动 launch", module_id="MOD-one", status="archived")
        self.record("IF-other", "启动 launch", module_id="MOD-two")
        self.record("IMP-one", "启动 launch", module_id="MOD-one", kind="implementation")
        result = self.search("启动", kinds=["interface"], module="MOD-one")
        self.assertEqual([r["id"] for r in result["results"]], ["IF-valid"])
        self.assertEqual(result["results"][0]["retrieved_by"], ["lexical", "semantic"])
        history = self.search("启动", kinds=["interface"], module="MOD-one", current_only=False)
        self.assertEqual({r["id"] for r in history["results"]}, {"IF-valid", "IF-old"})

    def test_changed_deleted_and_archived_records_use_live_text(self):
        path = self.record("IF-start", "launch version one")
        other = self.record("IF-save", "backup version one")
        first = self.search()["retrieval"]["diagnostics"]
        self.assertEqual(first["embedded_chunks"], 2)
        second = self.search()["retrieval"]["diagnostics"]
        self.assertEqual(second["embedded_chunks"], 0)
        self.assertTrue(second["query_reused"])
        self.record("IF-start", "launch version two")
        changed = self.search()
        self.assertEqual(changed["retrieval"]["diagnostics"]["embedded_chunks"], 1)
        self.assertEqual(changed["retrieval"]["diagnostics"]["removed_chunks"], 1)
        self.assertIn("version two", changed["results"][0]["snippet"]["text"])
        other.unlink()
        removed = self.search()
        self.assertEqual([r["id"] for r in removed["results"]], ["IF-start"])
        self.assertEqual(removed["retrieval"]["diagnostics"]["removed_chunks"], 1)
        self.record("IF-start", "launch version two", status="archived")
        self.assertEqual(self.search()["results"], [])
        self.assertEqual(self.search(current_only=False)["results"][0]["status"], "archived")
        self.assertTrue(path.exists())

    def test_filtered_query_does_not_prune_other_live_scope(self):
        self.record("IF-start", "launch version one")
        self.record("IMP-save", "backup version one", kind="implementation")
        self.search()
        scoped = self.search(kinds=["interface"])
        self.assertEqual(scoped["retrieval"]["diagnostics"]["removed_chunks"], 0)
        self.assertEqual(self.search()["retrieval"]["diagnostics"]["embedded_chunks"], 0)

    def test_map_location_and_model_space_isolate_cache(self):
        self.record("IF-start", "launch version one")
        doc = pm.load_project(self.base)
        _, a = sr.semantic_search(doc, doc["records"], "start", encoder=self.encoder)
        other = dict(doc, manifest_path=str(self.root / "other-worktree/project.yaml"))
        _, b = sr.semantic_search(other, other["records"], "start", encoder=self.encoder)
        self.assertNotEqual(a["cache_path"], b["cache_path"])
        self.assertEqual(b["embedded_chunks"], 1)
        self.encoder.space_id = "test-space-v2"
        _, c = sr.semantic_search(doc, doc["records"], "start", encoder=self.encoder)
        self.assertNotEqual(a["cache_path"], c["cache_path"])
        self.assertEqual(c["embedded_chunks"], 1)

    def test_corrupt_cached_vector_is_recomputed_and_invalid_new_vector_fails(self):
        self.record("IF-start", "launch version one")
        first = self.search()["retrieval"]["diagnostics"]
        with closing(sqlite3.connect(first["cache_path"])) as db, db:
            db.execute("UPDATE vectors SET data = ?", (b"bad-vector",))
        self.assertEqual(self.search()["retrieval"]["diagnostics"]["embedded_chunks"], 1)
        self.record("IF-start", "launch version two")
        with patch.object(self.encoder, "encode", return_value=[[float("nan"), 1, 0]]):
            with self.assertRaisesRegex(pm.MapError, "finite-value"):
                self.search()
        with patch.object(self.encoder, "encode", return_value=[[1, 0]]):
            with self.assertRaisesRegex(pm.MapError, "dimension"):
                self.search()

    def test_auto_fallback_explicit_failure_strict_match_and_exact_id(self):
        self.record("IF-start", "launch version one")
        doc = pm.load_project(self.base)
        with patch.object(sr, "load_encoder", side_effect=sr.SemanticError("not_configured", "test missing model")) as mocked:
            result = pm.search_project(doc, "launch", retrieval="auto")
            self.assertEqual(result["retrieval"]["status"], "degraded")
            self.assertEqual(result["retrieval"]["reason_code"], "not_configured")
            self.assertEqual(result["results"][0]["id"], "IF-start")
            with self.assertRaisesRegex(pm.MapError, "Hybrid retrieval unavailable"):
                pm.search_project(doc, "launch", retrieval="hybrid")
            mocked.reset_mock()
            strict = pm.search_project(doc, "开机", retrieval="auto", match="phrase")
            self.assertEqual(strict["results"], [])
            self.assertEqual(strict["retrieval"]["status"], "strict_lexical_match")
            exact = pm.search_project(doc, "IF-start", retrieval="auto")
            self.assertEqual(exact["retrieval"]["status"], "exact_id")
            self.assertEqual(exact["results"][0]["id"], "IF-start")
            mocked.assert_not_called()
        with self.assertRaisesRegex(pm.MapError, "Strict --match"):
            pm.search_project(doc, "launch", retrieval="hybrid", match="all")

    def test_corrupt_database_degrades_auto_without_rewriting_documents(self):
        original = self.record("IF-start", "launch version one")
        before = original.read_bytes()
        diagnostics = self.search()["retrieval"]["diagnostics"]
        Path(diagnostics["cache_path"]).write_bytes(b"invalid sqlite database")
        doc = pm.load_project(self.base)
        result = pm.search_project(doc, "launch", retrieval="auto")
        self.assertEqual(result["retrieval"]["reason_code"], "cache_unavailable")
        self.assertEqual(result["results"][0]["id"], "IF-start")
        with self.assertRaisesRegex(pm.MapError, "Local vector cache unavailable"):
            self.search()
        self.assertEqual(original.read_bytes(), before)

    def test_link_destinations_do_not_replace_live_evidence(self):
        body = "启动说明见 [运行说明](../../deeply/nested/project/path.md)。"
        self.record("IF-start", body)
        doc = pm.load_project(self.base)
        chunk = sr.chunks_for(doc)[0]
        self.assertNotIn("deeply/nested", chunk.embedded)
        self.assertIn("运行说明", chunk.embedded)
        hit = self.search()["results"][0]
        self.assertEqual(hit["snippet"]["text"], body)
        self.assertEqual(hit["snippet"]["line"], doc["records"][0]["line"])

    def test_rrf_arithmetic_dedup_and_exact_name_priority(self):
        a, b, c = [{"id": x, "title": x + " title"} for x in "abc"]
        lexical = [(a, {"match": "all_terms"}), (b, {"match": "all_terms"})]
        semantic = [(b, {"semantic_similarity": .7}), (b, {"semantic_similarity": .99}), (c, {"semantic_similarity": .6})]
        result = sr.fuse(lexical, semantic, "other")
        self.assertEqual([r["id"] for r, _ in result], ["b", "a", "c"])
        self.assertAlmostEqual(result[0][1]["rrf_score"], 1 / 62 + 1 / 61)
        self.assertEqual(result[0][1]["ranks"], {"lexical": 2, "semantic": 1})
        self.assertAlmostEqual(result[2][1]["rrf_score"], 1 / 62)
        self.assertEqual(sr.fuse(lexical, semantic, "a")[0][0]["id"], "a")
        a["aliases"] = ["friendly alias"]
        self.assertEqual(sr.fuse(lexical, semantic, "friendly alias")[0][0]["id"], "a")
        self.assertEqual(sr.fuse(lexical, semantic, "a title")[0][0]["id"], "a")

    def test_fixed_candidate_window_and_pagination(self):
        for index in range(55):
            self.record(f"IF-{index:02}", "launch version one")
        all_hits = self.search(limit=100)
        self.assertEqual(all_hits["total"], 50)
        self.assertEqual(all_hits["retrieval"]["candidate_window"], 50)
        first = self.search(limit=7)
        second = self.search(limit=7, offset=first["next_offset"])
        self.assertEqual(first["results"] + second["results"], all_hits["results"][:14])
        self.assertEqual(self.search(offset=50)["results"], [])

    def test_chunk_offsets_long_sections_and_fenced_headings(self):
        body = "# Actual\n\n" + "启动正文。" * 170 + "\n```python\n# not a heading\npass\n```\n## Other\n备份。"
        self.record("IF-start", body)
        doc = pm.load_project(self.base)
        chunks = sr.chunks_for(doc)
        self.assertGreater(len(chunks), 3)
        self.assertFalse(any(c.heading == "not a heading" for c in chunks))
        covered = set()
        for c in chunks:
            self.assertEqual(body[c.offset:c.offset + len(c.text)], c.text)
            self.assertEqual(c.snippet()["line"], doc["records"][0]["line"] + body[:c.offset].count("\n"))
            covered.update(range(c.offset, c.offset + len(c.text)))
        self.assertTrue(all(i in covered for i, char in enumerate(body) if not char.isspace()))


if __name__ == "__main__":
    unittest.main()
