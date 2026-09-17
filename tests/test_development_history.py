from pathlib import Path
import copy
import json
import sys
import tempfile
import unittest
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1] / "maintain-project-map/scripts"
sys.path.insert(0, str(SCRIPTS))
import development_history as dh
from render_map import export_reader


class HistoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.session = self.root / "session.jsonl"
        self.rows = [{"type": "session_meta", "payload": {"id": "thread"}}]
        def event(payload):
            return {"type": "response_item", "timestamp": "2026-09-17T03:26:00Z", "payload": payload}
        self.rows += [
            event({"type": "message", "role": "system", "content": [{"type": "input_text", "text": "system-secret"}]}),
            event({"type": "message", "role": "user", "id": "u", "content": [{"type": "input_text", "text": "Fix reading"}]}),
            event({"type": "reasoning", "text": "hidden-secret"}),
            event({"type": "message", "role": "assistant", "channel": "analysis", "content": [{"type": "output_text", "text": "analysis-secret"}]}),
            event({"type": "message", "role": "assistant", "phase": "commentary", "id": "m", "content": [{"type": "output_text", "text": "Trying layout"}]}),
            event({"type": "custom_tool_call", "name": "exec", "id": "c", "call_id": "pair", "input": "change(width=176)"}),
            event({"type": "custom_tool_call_output", "id": "r", "call_id": "pair", "output": [{"type": "input_text", "text": "UNIQUE-RAW-OUTPUT " + "测试🦉" * 1600}, {"type": "image", "data": "binary-secret"}]}),
            event({"type": "message", "role": "assistant", "phase": "final_answer", "id": "f", "content": [{"type": "output_text", "text": "Fixed within tested limits"}]}),
        ]
        self.write_source()
        self.capture = self.root / "history/test"
        self.imported = dh.import_session(self.session, self.capture, 2, len(self.rows))
        self.record = {"id": "HIST-test", "kind": "history", "title": "Reading layout", "date": "2026-09-17", "modules": ["reader"],
                       "summary": "Corrected a small label", "status": "current", "outcome": "delivered", "applicability": "test-v1", "related_records": [],
                       "path": str(self.root / "record.md"), "owned": True, "coverage_note": "Selected task only",
                       "history": {"path": "history/test", "sha256": self.imported["ledger_sha256"], "capture_sha256": self.imported["capture_sha256"]}}
        self.meta, self.events = dh.load_capture(self.root, self.record)
        self.call = next(e for e in self.events if e["kind"] == "tool_call")
        self.result = next(e for e in self.events if e["kind"] == "tool_result")
        self.result_text = dh.resolve_events(self.meta, [self.result])[0]["text"]
        self.record["body"] = f"# Reading layout\n\nA readable narrative.\n\n[View result](history-event:{self.result['id']})"
        self.data = {"project": {"name": "History test", "project_id": "test", "kind": "skill"}, "manifest_path": str(self.root / "project.yaml"),
                     "records": [self.record], "map_body": "A map", "relations": [], "fingerprint": "test-fingerprint", "version": {}}

    def write_source(self):
        self.session.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in self.rows) + "\n", encoding="utf-8")

    def add_experience(self, identity="EXP-label", **overrides):
        case = {"id": identity, "kind": "experience", "task_id": self.record["id"], "title": "Tiny text is unreadable",
                "date": "2026-09-17", "categories": ["debugging", "verification"], "results": ["failed", "passed"],
                "modules": ["reader"], "summary": "First failed, then verified within the same viewport", "outcome": "Corrected",
                "applicability": "test-v1", "coverage_note": "One selected layout issue", "related_records": [],
                "path": str(self.root / (identity + ".md")), "owned": True, "status": "current",
                "body": f"A layout experience.\n\n[Actual feedback](history-event:{self.result['id']})", **overrides}
        self.data["records"].append(case)
        return case

    def test_experience_facets_deduplicate_and_preserve_failed_attempt(self):
        self.add_experience()
        self.add_experience("EXP-other", categories=["improvement"], results=["pending"], modules=["storage"], summary="Storage reuse")
        with patch.object(dh, "load_capture", side_effect=AssertionError("should not open capture")), patch.object(dh, "resolve_events", side_effect=AssertionError("should not read raw text")):
            for category in ("debugging", "verification"):
                found = dh.search_experiences(self.data, category=category, result="failed", module="reader")
                self.assertEqual([r["id"] for r in found["experiences"]], ["EXP-label"])
                self.assertNotIn("body", found["experiences"][0])
            self.assertEqual(dh.search_experiences(self.data, query="viewport")["total"], 1)
            first = dh.search_experiences(self.data, limit=1)
            second = dh.search_experiences(self.data, limit=1, offset=first["next_offset"])
            self.assertNotEqual(first["experiences"][0]["id"], second["experiences"][0]["id"])
        with self.assertRaises(ValueError):
            dh.search_experiences(self.data, expected="old")

    def test_experiences_share_the_parent_capture_and_lazy_evidence(self):
        self.add_experience()
        self.add_experience("EXP-other", categories=["verification"])
        descriptor, assets = dh.prepare_export(self.data)
        self.assertEqual(len(assets), 1)
        self.assertEqual(descriptor["tasks"][self.record["id"]]["experience_ids"], ["EXP-label", "EXP-other"])
        output = self.root / "views/index.html"
        export_reader(self.data, output, diagrams=False)
        text = output.read_text(encoding="utf-8")
        self.assertIn("A layout experience.", text)
        self.assertNotIn("UNIQUE-RAW-OUTPUT", text)
        self.session.unlink()
        self.assertEqual(dh.search_experiences(self.data)["total"], 2)
        export_reader(self.data, output, diagrams=False)

    def test_invalid_experience_binding_prevents_partial_export(self):
        case = self.add_experience()
        output = self.root / "existing.html"
        output.write_text("existing", encoding="utf-8")
        for field, bad in (("task_id", "HIST-missing"), ("categories", ["debugging", "debugging"]), ("results", ["invented"]), ("body", "[wrong](history-event:EVT-wrong)")):
            saved = case[field]
            case[field] = bad
            with self.assertRaises(ValueError):
                export_reader(self.data, output, diagrams=False)
            self.assertEqual(output.read_text(encoding="utf-8"), "existing")
            case[field] = saved

    def test_public_allowlist_and_native_pairing(self):
        self.assertEqual(len(self.events), 5)
        self.assertEqual(self.call["pair_ids"], [self.result["id"]])
        raw = (self.capture / "events.jsonl").read_text(encoding="utf-8")
        for secret in ["system-secret", "hidden-secret", "analysis-secret", "binary-secret"]:
            self.assertNotIn(secret, raw)
        self.assertEqual(self.result["omitted_non_text_blocks"], 1)
        self.assertEqual(self.meta["coverage"]["unpaired_calls"], [])

    def test_repeat_import_is_idempotent_and_source_change_refused(self):
        before = (self.capture / "events.jsonl").read_bytes()
        self.assertEqual(dh.import_session(self.session, self.capture, 2, len(self.rows))["status"], "unchanged")
        self.rows[-1]["payload"]["content"][0]["text"] = "Changed"
        self.write_source()
        with self.assertRaises(ValueError):
            dh.import_session(self.session, self.capture, 2, len(self.rows))
        self.assertEqual(before, (self.capture / "events.jsonl").read_bytes())

    def test_missing_pair_is_reported_and_incomplete_range_refused(self):
        partial = dh.import_session(self.session, self.root / "history/partial", 3, 7)
        self.assertEqual(partial["coverage"]["unpaired_calls"][0]["call_id"], "pair")
        with self.assertRaises(ValueError):
            dh.import_session(self.session, self.root / "bad", 1, 999)
        self.assertFalse((self.root / "bad").exists())

    def test_bounded_reads_reconstruct_unicode_and_always_offer_pair(self):
        offset, fragments = 0, []
        while True:
            result = dh.read_events(self.meta, self.events, self.result["id"], offset, 111, 0, self.meta["ledger_sha256"])
            self.assertEqual(result["related"][0]["id"], self.call["id"])
            self.assertLessEqual(len(result["event"]["text"]), 111)
            fragments.append(result["event"]["text"])
            if result["continuation"] is None:
                break
            offset = result["continuation"]["offset"]
        self.assertEqual("".join(fragments), self.result_text)
        with self.assertRaises(ValueError):
            dh.read_events(self.meta, self.events, self.result["id"], expected="wrong")

    def test_search_is_bounded_and_task_search_does_not_open_events(self):
        with patch.object(Path, "read_bytes", side_effect=AssertionError("unexpected event read")):
            found = dh.search_tasks(self.data, "reader")
        self.assertEqual(found["total"], 1)
        self.assertNotIn("text", found["tasks"][0])
        found = dh.search_events(self.meta, self.events, "UNIQUE-RAW-OUTPUT", 1)
        self.assertEqual(found["events"][0]["id"], self.result["id"])
        self.assertLessEqual(len(found["events"][0]["excerpt"]), 350)
        all_events = dh.search_events(self.meta, self.events, limit=2)
        self.assertEqual(all_events["next_offset"], 2)
        self.assertEqual(dh.search_events(self.meta, self.events, limit=2, offset=2)["events"][0]["id"], self.call["id"])

    def test_capture_tamper_and_path_escape_fail(self):
        escaped = copy.deepcopy(self.record)
        escaped["history"]["path"] = "../outside"
        with self.assertRaises(ValueError):
            dh.load_capture(self.root, escaped)
        (self.capture / "events.jsonl").write_text("tampered", encoding="utf-8")
        with self.assertRaises(ValueError):
            dh.load_capture(self.root, self.record)

    def test_scope_change_and_task_search_continuation_are_detected(self):
        with self.assertRaises(ValueError):
            dh.search_tasks(self.data, expected="old-fingerprint")
        meta = json.loads((self.capture / "capture.json").read_text(encoding="utf-8"))
        meta["coverage"]["source_path"] = "a different source"
        (self.capture / "capture.json").write_text(json.dumps(meta), encoding="utf-8")
        with self.assertRaises(ValueError):
            dh.load_capture(self.root, self.record)

    def test_export_is_lazy_and_chunks_reconstruct_original_text(self):
        output = self.root / "views/index.html"
        export_reader(self.data, output, diagrams=False)
        for path in [output, output.parent / "docs.json"]:
            self.assertNotIn("UNIQUE-RAW-OUTPUT", path.read_text(encoding="utf-8"))
        docs = json.loads((output.parent / "docs.json").read_text(encoding="utf-8"))
        descriptor = docs["development_history"]["tasks"]["HIST-test"]
        path = f"{descriptor['folder']}/{self.result['id']}-0.json"
        parts = []
        while path:
            self.assertFalse((output.parent / path).exists(), "Raw text must not be copied to export assets")
            part = dh.read_export_packet(output.parent, path)
            self.assertLessEqual(len(part["text"]), dh.CHUNK)
            parts.append(part["text"])
            path = part["next_file"]
        self.assertEqual("".join(parts), self.result_text)
        self.assertNotIn("UNIQUE-RAW-OUTPUT", (self.capture / "events.jsonl").read_text(encoding="utf-8"))

    def test_source_loss_keeps_narrative_but_prevents_unverifiable_raw_read(self):
        self.session.unlink()
        output = self.root / "views/index.html"
        export_reader(self.data, output, diagrams=False)
        self.assertIn("A readable narrative", output.read_text(encoding="utf-8"))
        self.assertEqual(dh.search_tasks(self.data)["total"], 1)
        self.assertEqual(dh.search_events(self.meta, self.events)["total"], 5)
        with self.assertRaisesRegex(ValueError, "原 Codex 会话"):
            dh.read_events(self.meta, self.events, self.result["id"])

    def test_source_modification_is_detected_on_demand(self):
        self.rows[7]["payload"]["output"][0]["text"] = "Changed behind the index"
        self.write_source()
        with self.assertRaisesRegex(ValueError, "原会话的对应内容已改变"):
            dh.read_events(self.meta, self.events, self.result["id"])

    def test_broken_evidence_prevents_export_before_overwrite(self):
        output = self.root / "index.html"
        output.write_text("existing", encoding="utf-8")
        self.record["body"] += "\n[missing](history-event:EVT-missing)"
        with self.assertRaises(ValueError):
            export_reader(self.data, output, diagrams=False)
        self.assertEqual(output.read_text(encoding="utf-8"), "existing")


if __name__ == "__main__":
    unittest.main()
