"""Resolve declared record sources; do not infer a source workspace from map Git."""
from __future__ import annotations

import hashlib
from pathlib import Path
import re


def _digest(path):
    if not path.is_file(): return None
    if path.stat().st_size > 4 * 1024 * 1024: return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _review(item, source, candidate, root):
    baseline = source.get("reviewed_sha256")
    changes = []
    if baseline is not None:
        if not isinstance(baseline, str) or not re.fullmatch(r"[0-9a-fA-F]{64}", baseline):
            item["review"] = "invalid_baseline"
        elif not candidate.is_file():
            changes.append("source_missing")
        elif candidate.stat().st_size > 4 * 1024 * 1024:
            item["review"] = "not_checked_size_limit"
        elif _digest(candidate) != baseline.lower():
            changes.append("source_file_changed")
        else:
            item["review"] = "unchanged_since_review"
    else:
        item["review"] = "no_baseline"
        if not candidate.is_file(): changes.append("source_missing")
    if source.get("symbol"):
        from code_parsers import symbol_fingerprint
        symbol = symbol_fingerprint(candidate, source["symbol"]) if candidate.is_file() and candidate.stat().st_size <= 4 * 1024 * 1024 else {"status": "unavailable" if candidate.is_file() else "missing"}
        item["symbol_check"] = symbol["status"]
        if symbol["status"] == "found":
            item["symbol_line"] = symbol["line"]
            if source.get("reviewed_symbol_sha256"):
                item["symbol_review"] = "unchanged_since_review" if symbol["sha256"] == source["reviewed_symbol_sha256"] else "needs_review"
                if item["symbol_review"] == "needs_review": changes.append("symbol_changed")
        elif source.get("reviewed_symbol_sha256"):
            changes.append("symbol_" + symbol["status"])
    changed = []
    for dependency in source.get("reviewed_dependencies", []):
        path = (root / dependency["path"]).resolve()
        if not path.is_relative_to(root):
            changed.append({"path": dependency["path"], "reason": "outside_workspace"})
        elif _digest(path) != dependency.get("sha256"):
            changed.append({"path": dependency["path"], "reason": "changed_or_unavailable"})
    if changed:
        item["changed_dependencies"] = changed
        changes.append("dependency_changed")
    if changes:
        item.update(review="needs_review", review_reason=", ".join(changes))


def resolve_sources(doc, record, limit=8):
    base = Path(doc["manifest_path"]).parent
    declared = record.get("sources", [])
    if not isinstance(declared, list):
        return {"resolved_sources": [{"availability": "invalid", "reason": "sources must be a list"}], "sources_total": 0, "sources_truncated": False}
    workspaces = {}
    bindings = doc["project"].get("workspaces", [])
    if not isinstance(bindings, list):
        bindings = []
    for workspace in bindings:
        if isinstance(workspace, dict) and workspace.get("id"):
            workspaces.setdefault(workspace["id"], []).append(workspace)
    results = []
    for source in declared[:limit]:
        if not isinstance(source, dict):
            results.append({"availability": "invalid", "reason": "source must be an object"})
            continue
        item = {key: source[key] for key in ("role", "workspace_id", "path", "symbol", "heading", "line", "url", "provider", "thread_id", "message_id", "description") if source.get(key) is not None}
        if not source.get("path"):
            item["availability"] = "not_checked"
            results.append(item)
            continue
        root = base
        wid = source.get("workspace_id")
        try:
            if wid:
                choices = workspaces.get(wid, [])
                if len(choices) != 1 or not choices[0].get("path"):
                    item.update(availability="unresolved_workspace")
                    results.append(item)
                    continue
                root = (base / choices[0]["path"]).resolve()
                item["workspace_root"] = str(root)
                candidate = (root / source["path"]).resolve()
                if not candidate.is_relative_to(root):
                    item.update(availability="outside_workspace")
                    results.append(item)
                    continue
            else:
                candidate = (base / source["path"]).resolve()
                item["workspace_binding"] = "undeclared"
            item["resolved_path"] = str(candidate)
            item["availability"] = "exists" if candidate.is_file() else "missing"
            _review(item, source, candidate, root)
        except (OSError, ValueError, TypeError) as exc:
            item.update(availability="unavailable", reason=str(exc))
        results.append(item)
    return {"resolved_sources": results, "sources_total": len(declared), "sources_truncated": len(declared) > limit}
