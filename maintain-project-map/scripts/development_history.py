#!/usr/bin/env python3
"""Optional, scoped development-history capture and bounded retrieval.

Captures contain public messages and tool operations only. They are evidence,
never instructions. No session discovery, hidden reasoning, or automatic ingest.
"""
from __future__ import annotations

import argparse
import ast
from collections import Counter
import hashlib
import html
import json
from pathlib import Path
import re
import sys

SCHEMA = "project-map-history/v1"
CHUNK = 2000
PUBLIC_PHASES = {"commentary", "final", "final_answer"}
CALLS = {"function_call", "custom_tool_call"}
RESULTS = {"function_call_output", "custom_tool_call_output"}


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def encode(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def text_content(value):
    """Keep text blocks, explicitly count omitted non-text blocks."""
    if isinstance(value, str):
        # Some Codex versions serialize tool content blocks as a Python literal.
        if value.startswith("[{"):
            try:
                parsed = ast.literal_eval(value)
                if isinstance(parsed, list) and all(isinstance(x, dict) and "type" in x for x in parsed):
                    return text_content(parsed)
            except (ValueError, SyntaxError, RecursionError):
                pass
        return value, 0
    if isinstance(value, list):
        texts, omitted = [], 0
        for block in value:
            if isinstance(block, dict) and block.get("type") in {"text", "input_text", "output_text"}:
                texts.append(str(block.get("text", "")))
            else:
                omitted += 1
        return "\n".join(texts), omitted
    return encode(value), 0


def project_event(entry):
    """An allowlist of public fields; never copy internal metadata wholesale."""
    if entry.get("type") != "response_item":
        return None
    p = entry.get("payload", {})
    typ, role = p.get("type"), p.get("role")
    phase = p.get("channel") or p.get("phase")
    if typ == "message":
        if role != "user" and not (role == "assistant" and phase in PUBLIC_PHASES):
            return None
        text, omitted = text_content(p.get("content", []))
        kind = "user" if role == "user" else "assistant"
    elif typ in CALLS | RESULTS:
        text, omitted = text_content(p.get("output", p.get("input", p.get("arguments", ""))))
        kind = "tool_call" if typ in CALLS else "tool_result"
    else:
        return None
    return {"kind": kind, "timestamp": entry.get("timestamp"), "native_id": p.get("id"),
            "call_id": p.get("call_id"), "tool": ".".join(filter(None, [p.get("namespace"), p.get("name")])) or None,
            "phase": phase, "text": text, "omitted_non_text_blocks": omitted}


def import_session(source: Path, destination: Path, start: int, end: int):
    """Index public events by verified source location, without copying payloads."""
    source, destination = source.resolve(), destination.resolve()
    if start < 1 or end < start:
        raise ValueError("Use an explicit, positive inclusive line range.")
    events, scope_hash, thread_id, lines_seen = [], hashlib.sha256(), None, 0
    with source.open("rb") as handle:
        for line_no, raw in enumerate(handle, 1):
            if line_no > end:
                break
            lines_seen = line_no
            if line_no == 1:
                first = json.loads(raw)
                if first.get("type") == "session_meta":
                    thread_id = first.get("payload", {}).get("id")
            if line_no < start:
                continue
            scope_hash.update(raw)
            event = project_event(json.loads(raw))
            if event is None:
                continue
            identity = event["native_id"] or f"line:{line_no}:{digest(raw)}"
            event["id"] = "EVT-" + digest(f"{thread_id or source}\0{identity}".encode())[:20]
            event["source"] = {"path": str(source), "line": line_no, "thread_id": thread_id,
                               "line_sha256": digest(raw), "identity_strength": "native" if event["native_id"] else "line-and-hash"}
            event["text_sha256"] = digest(event["text"].encode())
            events.append(event)
    if lines_seen < end or not events:
        raise ValueError("Requested range is incomplete or contains no public events.")
    ids = [e["id"] for e in events]
    if len(set(ids)) != len(ids):
        raise ValueError("Ambiguous duplicate native event identity in the requested range.")
    calls = {}
    for event in events:
        if event["call_id"]:
            calls.setdefault(event["call_id"], []).append(event)
    unpaired = []
    for call_id, group in calls.items():
        kinds = Counter(e["kind"] for e in group)
        complete = kinds == {"tool_call": 1, "tool_result": 1}
        if not complete:
            unpaired.append({"call_id": call_id, "counts": dict(kinds)})
        for event in group:
            event["pair_ids"] = [other["id"] for other in group if other["id"] != event["id"]] if complete else []
    ledger = ("\n".join(encode(event_meta(e)) for e in events) + "\n").encode()
    coverage = {"source_path": str(source), "thread_id": thread_id, "start_line": start, "end_line": end,
                "source_range_sha256": scope_hash.hexdigest(), "event_count": len(events),
                "counts": dict(Counter(e["kind"] for e in events)), "unpaired_calls": unpaired,
                "start_time": events[0]["timestamp"], "end_time": events[-1]["timestamp"],
                "included": "User messages, public assistant commentary/final answers, tool call and result text",
                "excluded": "Hidden reasoning, system/developer messages, internal metadata, binary/image/audio blocks, events outside this range",
                "limitations": "Reference index only; raw text is read from the original host session on demand. Missing or modified sources cannot be reconstructed. Host truncation remains."}
    meta = {"schema": SCHEMA, "storage": "source-references", "ledger_sha256": digest(ledger), "coverage": coverage}
    if destination.exists():
        old = json.loads((destination / "capture.json").read_text(encoding="utf-8"))
        if old != meta or (destination / "events.jsonl").read_bytes() != ledger:
            raise ValueError("Capture already exists with different contents; use a new capture path. Original evidence was not changed.")
        return {"status": "unchanged", "path": str(destination), "capture_sha256": digest(encode(meta).encode()), **meta}
    destination.mkdir(parents=True)
    (destination / "events.jsonl").write_bytes(ledger)
    (destination / "capture.json").write_text(encode(meta) + "\n", encoding="utf-8")
    return {"status": "created", "path": str(destination), "capture_sha256": digest(encode(meta).encode()), **meta}


def load_capture(base: Path, record: dict):
    declaration = record.get("history", {})
    if not isinstance(declaration, dict) or not isinstance(declaration.get("path"), str):
        raise ValueError(f"{record['id']}: history.path is required, relative to the map directory.")
    root = base.resolve() / "history"
    target = (base / declaration["path"]).resolve()
    if not target.is_relative_to(root) or target == root:
        raise ValueError("History capture must stay within the map's history directory.")
    for name in ("capture.json", "events.jsonl"):
        if not (target / name).resolve().is_relative_to(root):
            raise ValueError("History file escapes the history directory.")
    meta = json.loads((target / "capture.json").read_text(encoding="utf-8"))
    if digest(encode(meta).encode()) != declaration.get("capture_sha256"):
        raise ValueError(f"{record['id']}: capture scope fingerprint mismatch.")
    ledger = (target / "events.jsonl").read_bytes()
    if meta.get("schema") != SCHEMA or digest(ledger) != meta.get("ledger_sha256"):
        raise ValueError("History evidence fingerprint mismatch; recheck the capture.")
    if declaration.get("sha256") != meta["ledger_sha256"]:
        raise ValueError(f"{record['id']}: recorded evidence fingerprint does not match the capture.")
    events = [json.loads(line) for line in ledger.decode().splitlines() if line]
    if len({e["id"] for e in events}) != len(events) or len(events) != meta["coverage"]["event_count"]:
        raise ValueError("Invalid event identity or count in capture.")
    return meta, events


def event_meta(event):
    return {**{k: v for k, v in event.items() if k != "text"},
            "total_chars": len(event["text"]) if "text" in event else event["total_chars"]}


def resolve_events(meta, events):
    """Read only selected source lines, verifying before exposing public text."""
    if all("text" in e for e in events):
        return events
    source = Path(meta["coverage"]["source_path"])
    wanted = {e["source"]["line"]: e for e in events}
    found = {}
    try:
        with source.open("rb") as handle:
            for line_no, raw in enumerate(handle, 1):
                if line_no > max(wanted, default=0):
                    break
                if line_no not in wanted:
                    continue
                indexed = wanted[line_no]
                if digest(raw) != indexed["source"]["line_sha256"]:
                    raise ValueError("原会话的对应内容已改变；请重新核对来源。")
                public = project_event(json.loads(raw))
                if public is None or digest(public["text"].encode()) != indexed["text_sha256"]:
                    raise ValueError("公开事件与来源索引不一致。")
                found[indexed["id"]] = {**indexed, "text": public["text"]}
    except FileNotFoundError as exc:
        raise ValueError("原 Codex 会话已移走或删除；当前仅保留过程叙述与来源定位，无法展开原文。") from exc
    if len(found) != len(events):
        raise ValueError("原会话已不包含所选事件，请核对来源。")
    return [found[e["id"]] for e in events]


def window(event, offset=0, max_chars=CHUNK):
    if not 0 <= offset <= len(event["text"]) or not 1 <= max_chars <= 12000:
        raise ValueError("Invalid character offset or max_chars (1..12000).")
    end = min(offset + max_chars, len(event["text"]))
    return {**event_meta(event), "text": event["text"][offset:end], "offset": offset, "end_offset": end,
            "truncated": end < len(event["text"]), "next_offset": end if end < len(event["text"]) else None}


def find_record(data, task):
    matches = [r for r in data["records"] if r["kind"] == "history" and r["id"] == task]
    if len(matches) != 1:
        raise ValueError("Select one history record by its stable ID.")
    return matches[0]


def search_tasks(data, query="", limit=5, offset=0, expected=None):
    if expected and expected != data["fingerprint"]:
        raise ValueError("Task summaries changed; restart the search.")
    if not 1 <= limit <= 20 or offset < 0:
        raise ValueError("Use limit 1..20 and a nonnegative offset.")
    terms = query.casefold().split()
    rows = []
    for r in data["records"]:
        if r["kind"] != "history":
            continue
        haystack = encode(r).casefold()
        if not all(term in haystack for term in terms):
            continue
        rows.append({k: r.get(k) for k in ["id", "title", "date", "modules", "outcome", "summary", "applicability", "related_records", "path"]})
    rows.sort(key=lambda x: (str(x["date"]), x["id"]), reverse=True)
    end = offset + limit
    return {"tasks": rows[offset:end], "total": len(rows), "next_offset": end if end < len(rows) else None,
            "truncated": end < len(rows), "coverage": "Candidate summaries only; no event payloads or constraints opened.",
            "fingerprint": data["fingerprint"]}


CASE_CATEGORIES = {"debugging": "排错与修复", "improvement": "改进", "verification": "验证",
              "exploration": "方案探索", "human-correction": "人工纠偏"}
CASE_RESULTS = {"failed": "曾未通过", "passed": "验证通过", "adopted": "已采用",
           "not_adopted": "未采用", "pending": "待验证"}


def experience_records(data):
    """Validate the shared records, not their category-specific UI occurrences."""
    tasks = {r["id"]: r for r in data["records"] if r["kind"] == "history"}
    rows = []
    for r in data["records"]:
        if r["kind"] != "experience":
            continue
        if r.get("task_id") not in tasks:
            raise ValueError(f"{r['id']}: task_id must identify a history record in this map.")
        for field, allowed in (("categories", CASE_CATEGORIES), ("results", CASE_RESULTS)):
            values = r.get(field)
            if not isinstance(values, list) or not values or any(not isinstance(v, str) or v not in allowed for v in values) or len(set(values)) != len(values):
                raise ValueError(f"{r['id']}: {field} must be a nonempty list of distinct supported values.")
        for field in ("modules", "related_records"):
            if not isinstance(r.get(field, []), list) or any(not isinstance(v, str) for v in r.get(field, [])):
                raise ValueError(f"{r['id']}: {field} must contain strings.")
        rows.append(r)
    return rows


def search_experiences(data, query="", limit=5, offset=0, expected=None, category="", result="", module="", task=""):
    """Small deduplicated summaries; no source capture or raw event reads."""
    if expected and expected != data["fingerprint"]:
        raise ValueError("Experience summaries changed; restart the search.")
    if not 1 <= limit <= 20 or offset < 0:
        raise ValueError("Use limit 1..20 and a nonnegative offset.")
    if category and category not in CASE_CATEGORIES or result and result not in CASE_RESULTS:
        raise ValueError("Unknown category or result filter.")
    terms, rows = query.casefold().split(), []
    for r in experience_records(data):
        if category and category not in r["categories"] or result and result not in r["results"]:
            continue
        if module and module not in r.get("modules", []) or task and task != r["task_id"]:
            continue
        if not all(t in encode(r).casefold() for t in terms):
            continue
        rows.append({k: r.get(k) for k in ("id", "title", "summary", "task_id", "categories", "results", "modules", "outcome", "applicability", "date", "related_records", "path")})
    rows.sort(key=lambda r: (str(r["date"] or ""), r["id"]), reverse=True)
    end = offset + limit
    return {"experiences": rows[offset:end], "total": len(rows), "next_offset": end if end < len(rows) else None,
            "truncated": end < len(rows), "fingerprint": data["fingerprint"],
            "coverage": "Experience summaries only; categories are views of the same record. No raw events opened."}


def search_events(meta, events, query="", limit=5, offset=0, expected=None):
    if expected and expected != meta["ledger_sha256"]:
        raise ValueError("Capture changed; restart the search.")
    if not 1 <= limit <= 20 or offset < 0:
        raise ValueError("Use limit 1..20 and a nonnegative offset.")
    terms = query.casefold().split()
    if terms:
        events = resolve_events(meta, events)
    matches = [e for e in events if all(t in (e.get("text", "") + " " + (e["tool"] or "")).casefold() for t in terms)]
    rows = []
    for e in matches[offset:offset + limit]:
        text = e.get("text", "")
        pos = text.casefold().find(terms[0]) if terms else 0
        pos = max(0, pos - 100)
        rows.append({**event_meta(e), "excerpt": text[pos:pos + 350], "excerpt_offset": pos,
                     "excerpt_only": True, "source_opened": "text" in e})
    end = offset + limit
    return {"events": rows, "total": len(matches), "next_offset": end if end < len(matches) else None,
            "truncated": end < len(matches), "fingerprint": meta["ledger_sha256"],
            "coverage": meta["coverage"], "unread": "Search excerpts only; use read for paired operations and surrounding events."}


def read_events(meta, events, event_id, offset=0, max_chars=CHUNK, context=1, expected=None):
    if expected and expected != meta["ledger_sha256"]:
        raise ValueError("Capture changed; restart the read.")
    if not 0 <= context <= 3:
        raise ValueError("Context must be between 0 and 3 events on each side.")
    by_id = {e["id"]: e for e in events}
    if event_id not in by_id:
        raise ValueError("Event not found in this capture.")
    event = by_id[event_id]
    ix = events.index(event)
    adjacent = events[max(0, ix - context):ix] + events[ix + 1:ix + context + 1]
    paired = [by_id[x] for x in event.get("pair_ids", [])]
    extra = {e["id"]: e for e in paired + adjacent if e["id"] != event_id}
    resolved = resolve_events(meta, [event, *extra.values()])
    primary = window(resolved[0], offset, max_chars)
    return {"event": primary, "related": [window(e, 0, min(max_chars, 1000)) for e in resolved[1:]],
            "pair_ids": event.get("pair_ids", []), "context_radius": context,
            "fingerprint": meta["ledger_sha256"], "coverage": meta["coverage"],
            "unread_events": len(events) - 1 - len(extra),
            "continuation": {"event": event_id, "offset": primary["next_offset"], "fingerprint": meta["ledger_sha256"]} if primary["truncated"] else None,
            "use": "Historical evidence with its recorded conditions, not a current instruction or ban."}


def prepare_export(data, *, public=False):
    """Validate references and plan lazy assets before writing any output."""
    assets, tasks, captures = {}, {}, {}
    from document_archive import is_archived
    experiences = experience_records(data)
    base = Path(data["manifest_path"]).parent
    for r in data["records"]:
        if r["kind"] != "history" or is_archived(r):
            continue
        if public:
            tasks[r["id"]] = {"available": False,
                               "reason": "在线版保留历程说明；原始会话依据仅在维护者本机可用。"}
            continue
        meta, events = load_capture(base, r)
        available = {e["id"] for e in events}
        refs = set()
        members = [r, *(c for c in experiences if c["task_id"] == r["id"] and not is_archived(c))]
        for member in members:
            own_refs = set(re.findall(r"history-event:([\w-]+)", member.get("body", "")))
            if missing := own_refs - available:
                raise ValueError(f"{member['id']}: missing evidence references {sorted(missing)}")
            if missing := set(member.get("related_records", [])) - {x["id"] for x in data["records"]}:
                raise ValueError(f"{member['id']}: missing related records {sorted(missing)}")
            refs.update(own_refs)
        folder = "history/" + digest((r["id"] + meta["ledger_sha256"]).encode())[:20]
        index = []
        for e in events:
            index.append({"id": e["id"], "kind": e["kind"], "timestamp": e["timestamp"],
                          "tool": e["tool"], "line": e["source"]["line"], "pair_ids": e.get("pair_ids", [])})
        assets[folder + "/index.json"] = index
        captures[folder] = {"map_directory": str(base.resolve()), "record": {"id": r["id"], "history": r["history"]}}
        tasks[r["id"]] = {"folder": folder, "index_file": folder + "/index.json", "coverage": meta["coverage"],
                           "fingerprint": meta["ledger_sha256"], "evidence_ids": sorted(refs),
                           "experience_ids": [c["id"] for c in members[1:]]}
    return {"schema": SCHEMA, "tasks": tasks, "categories": CASE_CATEGORIES, "results": CASE_RESULTS, "_captures": captures}, assets


def read_export_packet(export_dir, target):
    """Serve one bounded source fragment through an explicitly exported binding."""
    match = re.fullmatch(r"(history/[a-f0-9]{20})/(EVT-[a-f0-9]{20})-(\d+)\.json", target)
    if not match:
        raise KeyError("Unlisted history target")
    folder, event_id, offset = match.groups()
    manifest = export_dir / "history-assets.json"
    if manifest.is_symlink():
        raise ValueError("History registry must be a regular file")
    registry = json.loads(manifest.read_text(encoding="utf-8"))
    binding = registry.get("captures", {}).get(folder)
    if not binding:
        raise KeyError("Unlisted capture")
    meta, events = load_capture(Path(binding["map_directory"]), binding["record"])
    selected = [e for e in events if e["id"] == event_id]
    if len(selected) != 1:
        raise KeyError("Unlisted event")
    packet = window(resolve_events(meta, selected)[0], int(offset), CHUNK)
    packet["next_file"] = f"{folder}/{event_id}-{packet['next_offset']}.json" if packet["truncated"] else None
    return packet


def evidence_renderer(fallback, record, descriptor):
    def resolve(label, target, wiki=False):
        if not wiki and target.startswith("history-event:"):
            if descriptor.get("available") is False:
                return '<span class="meta">' + html.escape(label) + '（原始依据仅本机可用）</span>'
            event_id = target.removeprefix("history-event:")
            if event_id not in descriptor.get("evidence_ids", []):
                raise ValueError("Unresolved history evidence reference")
            return ('<a href="#mode=history&amp;task=' + html.escape(record.get("task_id", record["id"]), quote=True)
                    + '&amp;event=' + html.escape(event_id, quote=True) + '" data-history-event="'
                    + html.escape(event_id, quote=True) + '">' + html.escape(label) + '</a>')
        return fallback(label, target, wiki)
    return resolve


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    subs = parser.add_subparsers(dest="command", required=True)
    imp = subs.add_parser("import-session", help="Import an explicitly selected public task range")
    imp.add_argument("source", type=Path)
    imp.add_argument("destination", type=Path)
    imp.add_argument("--start-line", type=int, required=True)
    imp.add_argument("--end-line", type=int, required=True)
    for name in ["search", "cases", "events", "read", "validate"]:
        p = subs.add_parser(name)
        p.add_argument("manifest", type=Path)
        if name in {"events", "read"}:
            p.add_argument("--task", required=True)
        if name != "validate":
            p.add_argument("--fingerprint")
        if name in {"search", "cases", "events"}:
            p.add_argument("--query", default="")
            p.add_argument("--limit", type=int, default=5)
        if name != "validate":
            p.add_argument("--offset", type=int, default=0)
        if name == "read":
            p.add_argument("--event", required=True)
            p.add_argument("--max-chars", type=int, default=CHUNK)
            p.add_argument("--context", type=int, default=1)
        if name == "cases":
            p.add_argument("--category", choices=list(CASE_CATEGORIES), default="")
            p.add_argument("--result", choices=list(CASE_RESULTS), default="")
            p.add_argument("--module", default="")
            p.add_argument("--task", default="")
    args = parser.parse_args(argv)
    try:
        if args.command == "import-session":
            result = import_session(args.source, args.destination, args.start_line, args.end_line)
        else:
            from project_map import load_project
            data = load_project(args.manifest)
            if args.command == "search":
                result = search_tasks(data, args.query, args.limit, args.offset, args.fingerprint)
            elif args.command == "cases":
                result = search_experiences(data, args.query, args.limit, args.offset, args.fingerprint, args.category, args.result, args.module, args.task)
            elif args.command == "validate":
                descriptor, assets = prepare_export(data)
                result = {"valid": True, "task_count": len(descriptor["tasks"]), "experience_count": len(experience_records(data)), "lazy_asset_count": len(assets)}
            else:
                r = find_record(data, args.task)
                meta, events = load_capture(args.manifest.resolve().parent, r)
                result = search_events(meta, events, args.query, args.limit, args.offset, args.fingerprint) if args.command == "events" else read_events(meta, events, args.event, args.offset, args.max_chars, args.context, args.fingerprint)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, KeyError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
