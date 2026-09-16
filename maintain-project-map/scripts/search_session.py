#!/usr/bin/env python3
"""Bounded lookup of visible messages in an explicitly supplied Codex JSONL file."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys


def visible_message(item: dict, role: str):
    """Read public response messages only; never expose reasoning/tool payloads."""
    if item.get("type") != "response_item":
        return None
    payload = item.get("payload")
    if not isinstance(payload, dict) or payload.get("type") != "message":
        return None
    msg_role = payload.get("role")
    if msg_role not in ("user", "assistant") or role not in ("all", msg_role):
        return None
    if msg_role == "assistant" and payload.get("channel") not in ("final", "commentary"):
        return None
    content = payload.get("content", [])
    if isinstance(content, str):
        text = content
    elif isinstance(content, list):
        text = "\n".join(
            part["text"] for part in content
            if isinstance(part, dict)
            and part.get("type") in ("input_text", "output_text", "text")
            and isinstance(part.get("text"), str)
        )
    else:
        return None
    if not text:
        return None
    return {"message_id": payload.get("id"), "role": msg_role,
            "timestamp": item.get("timestamp"), "text": text}


def lookup(source, *, query=None, message_id=None, line=None, role="user",
           limit=5, max_chars=1200, offset=0):
    source = Path(source).expanduser().resolve(strict=True)
    if not source.is_file():
        raise ValueError("source must be a JSONL file")
    if sum(x is not None for x in (query, message_id, line)) != 1:
        raise ValueError("select exactly one of query, message_id, or line")
    if not 1 <= limit <= 100 or not 1 <= max_chars <= 20000 or offset < 0:
        raise ValueError("limit 1..100, max_chars 1..20000, offset >= 0 required")
    if line is not None and line < 1:
        raise ValueError("line numbers start at 1")
    terms = query.casefold().split() if query is not None else None
    if terms == []:
        raise ValueError("query must contain search text")
    before = source.stat()
    thread_id = None
    seen = set()
    results = []
    matches = 0
    scanned = 0
    invalid = 0
    visible = 0
    source_complete = True
    with source.open("r", encoding="utf-8-sig") as stream:
        for number, raw in enumerate(stream, 1):
            scanned = number
            try:
                item = json.loads(raw)
            except json.JSONDecodeError:
                invalid += 1
                continue
            if not isinstance(item, dict):
                continue
            if item.get("type") == "session_meta" and isinstance(item.get("payload"), dict):
                thread_id = item["payload"].get("id", thread_id)
            if line is not None and number > line:
                source_complete = False
                break
            msg = visible_message(item, role)
            if msg is None:
                continue
            visible += 1
            if line is not None and number != line:
                continue
            if message_id is not None and msg["message_id"] != message_id:
                continue
            if terms is not None and not all(t in msg["text"].casefold() for t in terms):
                continue
            # Native identities deduplicate repeated serialized messages, not similar text.
            key = (thread_id, msg["message_id"]) if msg["message_id"] else (str(source), number)
            if key in seen:
                continue
            seen.add(key)
            matches += 1
            if len(results) >= limit:
                continue
            text = msg.pop("text")
            start = min(offset, len(text))
            if terms and offset == 0:
                folded = text.casefold()
                hit = min(folded.find(t) for t in terms)
                # ASCII/CJK offsets coincide; for expanding case folds use a safe prefix.
                if len(folded) == len(text):
                    start = max(0, hit - min(160, max_chars // 4))
            end = min(len(text), start + max_chars)
            msg.update({"thread_id": thread_id, "path": str(source), "line": number,
                        "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
                        "offset_unit": "unicode_codepoints", "start": start, "end": end,
                        "total_chars": len(text), "text": text[start:end],
                        "truncated": start > 0 or end < len(text),
                        "next_offset": end if end < len(text) else None,
                        "identity_strength": "native" if msg["message_id"] else "file_line_hash"})
            results.append(msg)
    after = source.stat()
    return {"source": str(source), "scope": "visible Codex response messages",
            "role": role, "results": results, "matched_messages": matches,
            "has_more_results": matches > len(results), "scanned_lines": scanned,
            "visible_messages_scanned": visible, "invalid_json_lines": invalid,
            "scanned_to_end": source_complete,
            "source_changed_during_read": (before.st_size, before.st_mtime_ns) !=
                                          (after.st_size, after.st_mtime_ns),
            "note": "A match is a candidate source; verify neighboring context and later revisions."}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, help="Exact Codex JSONL path; never auto-scan history")
    selector = parser.add_mutually_exclusive_group(required=True)
    selector.add_argument("--query")
    selector.add_argument("--message-id")
    selector.add_argument("--line", type=int)
    parser.add_argument("--role", choices=("user", "assistant", "all"), default="user")
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--max-chars", type=int, default=1200)
    parser.add_argument("--offset", type=int, default=0)
    args = parser.parse_args(argv)
    try:
        print(json.dumps(lookup(**vars(args)), ensure_ascii=False, indent=2))
    except (OSError, ValueError, UnicodeError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    raise SystemExit(main())
