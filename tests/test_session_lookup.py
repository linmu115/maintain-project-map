import importlib.util
import json
from pathlib import Path

import pytest

MODULE_PATH = Path(__file__).parents[1] / "maintain-project-map/scripts/search_session.py"
spec = importlib.util.spec_from_file_location("session_lookup", MODULE_PATH)
session = importlib.util.module_from_spec(spec)
spec.loader.exec_module(session)


def write_log(tmp_path, items):
    path = tmp_path / "session.jsonl"
    path.write_text("\n".join(json.dumps(x, ensure_ascii=False) for x in items), encoding="utf-8")
    return path


def msg(text, identity="m1", role="user", channel=None):
    return {"type": "response_item", "payload": {"type": "message", "role": role,
            "channel": channel, "id": identity, "content": [{"type": "input_text", "text": text}]}}


def test_chinese_middle_match_bounded_and_source_identity(tmp_path):
    path = write_log(tmp_path, [{"type": "session_meta", "payload": {"id": "thread-1"}},
                              msg("前" * 3000 + "跨项目引用" + "后" * 3000)])
    out = session.lookup(path, query="跨项目引用", max_chars=200)
    hit = out["results"][0]
    assert hit["thread_id"] == "thread-1" and hit["message_id"] == "m1"
    assert hit["line"] == 2 and "跨项目引用" in hit["text"]
    assert hit["truncated"] and len(hit["text"]) <= 200
    continuation = session.lookup(path, message_id="m1", offset=hit["next_offset"], max_chars=200)
    assert continuation["results"][0]["start"] == hit["end"]


def test_never_returns_reasoning_or_tool_payloads(tmp_path):
    path = write_log(tmp_path, [msg("主题 用户"), msg("主题 hidden", "m2", "assistant", "analysis"),
                              msg("主题 unclassified", "m3", "assistant"),
                              msg("主题 visible", "m4", "assistant", "final"),
                              {"type": "response_item", "payload": {"type": "reasoning", "text": "主题 secret"}}])
    text = json.dumps(session.lookup(path, query="主题", role="all"), ensure_ascii=False)
    assert "visible" in text and "hidden" not in text and "secret" not in text and "unclassified" not in text


def test_deduplicate_ids_not_similar_message_content(tmp_path):
    path = write_log(tmp_path, [msg("旧称"), msg("旧称"), msg("旧称", "m2")])
    out = session.lookup(path, query="旧称", limit=1)
    assert out["matched_messages"] == 2 and out["has_more_results"]


def test_line_fallback_and_exact_text_offsets(tmp_path):
    path = write_log(tmp_path, [msg("🗺️地图定义", identity=None)])
    hit = session.lookup(path, line=1, offset=2, max_chars=2)["results"][0]
    assert hit["text"] == "地图" and hit["identity_strength"] == "file_line_hash"


def test_empty_search_rejected(tmp_path):
    path = write_log(tmp_path, [])
    with pytest.raises(ValueError, match="search text"):
        session.lookup(path, query=" ")
