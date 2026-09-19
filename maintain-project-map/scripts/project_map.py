#!/usr/bin/env python3
"""A small, live-file project-map reader and bounded command-line interface.

No service, implicit repository scan, Git writes, or implicit external traversal.
Optional local embeddings use a rebuildable vector cache, never cached source text.
System queries summarize explicitly collected maps only when requested.
The public load_project() result is the common input to human reading views.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any

# Support callers loading this standalone script with importlib as well as CLI.
if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))

SCHEMA = "project-map/v1"
HISTORICAL = {"retired", "merged", "superseded", "withdrawn", "archived"}


class MapError(ValueError):
    """A user-actionable input error, rather than an internal traceback."""


def _mapping(text: str, label: str) -> dict:
    try:
        obj = json.loads(text)
    except json.JSONDecodeError:
        try:
            import yaml
        except ImportError as exc:
            raise MapError(f"{label}: YAML requires PyYAML (python -m pip install PyYAML); JSON syntax is also accepted.") from exc
        try:
            class SourceLoader(yaml.SafeLoader):
                pass
            # Dates are metadata text, not Python-only values that would prevent
            # portable JSON export or unrelated lifecycle metadata preservation.
            SourceLoader.yaml_implicit_resolvers = {
                key: [(tag, expr) for tag, expr in items if tag != "tag:yaml.org,2002:timestamp"]
                for key, items in yaml.SafeLoader.yaml_implicit_resolvers.items()
            }
            obj = yaml.load(text, Loader=SourceLoader)
        except yaml.YAMLError as exc:
            raise MapError(f"{label}: invalid YAML: {exc}") from exc
    if not isinstance(obj, dict):
        raise MapError(f"{label}: expected an object/mapping")
    return obj


def _text(path: Path) -> str:
    try:
        return path.read_bytes().decode("utf-8-sig")
    except (OSError, UnicodeError) as exc:
        raise MapError(f"Cannot read UTF-8 file {path}: {exc}") from exc


def manifest_file(value: str | Path) -> Path:
    p = Path(value).expanduser().resolve()
    if p.is_dir():
        p = p / "project.yaml"
    if not p.is_file():
        raise MapError(f"Project manifest not found: {p}")
    return p


def discover_project(start: str | Path = ".", stop: str | Path | None = None) -> dict:
    """Check a few conventional paths per ancestor; never recursively scan.

    --stop is an inclusive project boundary when the harness knows its workspace.
    The first ancestor with a manifest ends discovery, including ambiguity.
    """
    current = Path(start).expanduser().resolve()
    if current.is_file():
        current = current.parent
    boundary = Path(stop).expanduser().resolve() if stop else None
    if boundary and not current.is_relative_to(boundary):
        raise MapError("Discovery start must be inside the explicit stop directory")
    checked = []
    for directory in (current, *current.parents):
        candidates = [directory / "project.yaml", directory / "docs/project/project.yaml", directory / ".project-map/project.yaml"]
        found = []
        for candidate in candidates:
            checked.append(str(candidate))
            if candidate.is_file():
                meta = _mapping(_text(candidate), str(candidate))
                if meta.get("schema") == SCHEMA:
                    found.append({"manifest_path": str(candidate.resolve()), "project_id": meta.get("project_id"), "name": meta.get("name")})
        if found:
            return {"status": "resolved" if len(found) == 1 else "ambiguous", "locations": found,
                    **(found[0] if len(found) == 1 else {}), "checked_count": len(checked), "scope": "Nearest ancestor only; conventional manifest paths"}
        if boundary and directory == boundary:
            break
    return {"status": "unresolved", "locations": [], "checked_count": len(checked), "scope": "Conventional manifest paths through explicit boundary or filesystem root"}


def _resolve_source(base: Path, name: Any) -> Path:
    if not isinstance(name, str) or not name.strip():
        raise MapError("A source path must be a nonempty string")
    p = (base / name).resolve()
    if p.suffix.lower() not in {".md", ".markdown"}:
        raise MapError(f"Only declared Markdown sources are read, not generated HTML: {p}")
    return p


def _list(value: Any, label: str) -> list:
    if value is None:
        return []
    if not isinstance(value, list):
        raise MapError(f"{label} must be an array")
    return value


def _required(meta: dict, key: str, label: str) -> str:
    value = meta.get(key)
    if not isinstance(value, str) or not value.strip():
        raise MapError(f"{label}: {key} must be a nonempty string")
    return value


def _frontmatter(text: str, label: str) -> tuple[dict, str, int]:
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        raise MapError(f"{label}: owned records require YAML frontmatter")
    end = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), None)
    if end is None:
        raise MapError(f"{label}: frontmatter closing --- is missing")
    return _mapping("".join(lines[1:end]), label), "".join(lines[end + 1:]), end + 2


def _headings(text: str) -> list[tuple[int, int, str]]:
    """ATX headings outside fenced code; line indexes are one-based."""
    result, fence = [], None
    for i, line in enumerate(text.splitlines(), 1):
        marker = re.match(r"^\s{0,3}(`{3,}|~{3,})", line)
        if marker:
            seq = marker.group(1)
            if fence is None:
                fence = seq
            elif seq[0] == fence[0] and len(seq) >= len(fence):
                fence = None
            continue
        if fence:
            continue
        m = re.match(r"^\s{0,3}(#{1,6})\s+(.+?)\s*$", line)
        if m:
            result.append((i, len(m.group(1)), re.sub(r"\s+#+\s*$", "", m.group(2))))
    return result


def _heading_body(text: str, heading: str | None, label: str) -> tuple[str, int, int]:
    lines = text.splitlines(keepends=True)
    if heading is None:
        return text, 1, max(1, len(lines))
    heading = re.sub(r"^#+\s*", "", str(heading)).strip()
    headings = _headings(text)
    found = [h for h in headings if h[2] == heading]
    if len(found) != 1:
        raise MapError(f"{label}: heading {heading!r} matched {len(found)} times; use a unique exact heading")
    line, level, _ = found[0]
    end = next((pos - 1 for pos, lev, _ in headings if pos > line and lev <= level), len(lines))
    return "".join(lines[line - 1:end]), line, max(line, end)


def _cells(line: str) -> list[str]:
    # Split unescaped pipes; escaped pipes remain literal cell text.
    return [s.strip().replace(r"\|", "|") for s in re.split(r"(?<!\\)\|", line.strip().strip("|"))]


def _table_body(text: str, column: str, row_id: str, label: str) -> tuple[str, int, int, dict]:
    lines = text.splitlines()
    matches, in_fence = [], None
    i = 0
    while i < len(lines) - 1:
        marker = re.match(r"^\s{0,3}(`{3,}|~{3,})", lines[i])
        if marker:
            seq = marker.group(1)
            if in_fence is None:
                in_fence = seq
            elif seq[0] == in_fence[0] and len(seq) >= len(in_fence):
                in_fence = None
            i += 1
            continue
        if in_fence or "|" not in lines[i]:
            i += 1
            continue
        headers = _cells(lines[i])
        separator = _cells(lines[i + 1])
        if column not in headers or len(headers) != len(separator) or not all(re.fullmatch(r":?-{3,}:?", s) for s in separator):
            i += 1
            continue
        if headers.count(column) != 1:
            raise MapError(f"{label}: duplicate table ID column {column!r}")
        column_index, j = headers.index(column), i + 2
        while j < len(lines) and "|" in lines[j] and lines[j].strip():
            cells = _cells(lines[j])
            if len(cells) == len(headers) and cells[column_index].strip(" `") == row_id:
                fields = dict(zip(headers, cells))
                matches.append(("\n".join(f"{key}: {value}" for key, value in fields.items()), j + 1, j + 1, fields))
            j += 1
        i = j
    if len(matches) != 1:
        raise MapError(f"{label}: table row {row_id!r} matched {len(matches)} times")
    return matches[0]


def _relations(values: Any, label: str) -> list[dict]:
    result = []
    for item in _list(values, label):
        if not isinstance(item, dict):
            raise MapError(f"{label}: each relation must be an object")
        r = copy.deepcopy(item)
        _required(r, "relation", label)
        target = r.get("to")
        if isinstance(target, str):
            target = {"record_id": target}
        if not isinstance(target, dict) or not (target.get("record_id") or target.get("project_id")):
            raise MapError(f"{label}: to needs project_id or record_id")
        for key in ("project_id", "record_id"):
            if key in target:
                _required(target, key, label)
        r["to"] = target
        result.append(r)
    return result


def normalize_relations(relations: list[dict], project_id: str) -> list[dict]:
    """One edge for known inverse spellings; retain distinct roles and qualifiers.

    Source records stay untouched. The query/reader projection combines reasons
    but never merges relations with different versions, mechanisms or evidence.
    """
    inverse = {"provided_by": "provides", "used_by": "consumes",
               "contained_by": "contains", "belongs_to": "contains", "part_of": "contains"}
    grouped = {}
    for declaration in relations:
        relation = copy.deepcopy(declaration)
        for side in ("from", "to"):
            relation[side].setdefault("project_id", project_id)
        if relation["relation"] in inverse:
            relation["relation"] = inverse[relation["relation"]]
            relation["from"], relation["to"] = relation["to"], relation["from"]
        reasons = relation.pop("reasons", None) or [relation.get("reason", "")]
        count = relation.pop("declaration_count", 1)
        key = json.dumps({k: v for k, v in relation.items() if k != "reason"},
                         sort_keys=True, ensure_ascii=False)
        if key not in grouped:
            grouped[key] = (relation, [], 0)
        row, notes, total = grouped[key]
        notes.extend(note for note in reasons if note and note not in notes)
        grouped[key] = row, notes, total + count
    result = []
    for row, notes, count in grouped.values():
        if notes:
            row["reason"] = notes[0]
        if len(notes) > 1:
            row["reasons"] = notes
        if count > 1:
            row["declaration_count"] = count
        result.append(row)
    return result


def _summary(body: str) -> str:
    for line in body.splitlines():
        clean = line.strip()
        if clean and not clean.startswith(("#", "```", "~~~", "|", "---")):
            return clean[:240]
    return ""


def _record(meta: dict, body: str, path: Path, line: int, end: int, owned: bool, source_text: str | None = None) -> dict:
    r = copy.deepcopy(meta)
    _required(r, "id", str(path))
    _required(r, "kind", str(path))
    r.setdefault("title", r["id"])
    _required(r, "title", str(path))
    r.setdefault("summary", _summary(body))
    r.setdefault("status", "current")
    r.setdefault("progress", "")
    r.setdefault("gap", "")
    if r["kind"] in {"update", "history", "experience"}:
        date = _required(r, "date", str(path))
        try:
            if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date):
                raise ValueError("date format")
            datetime.strptime(date, "%Y-%m-%d")
        except ValueError as exc:
            raise MapError(f"{path}: {r['kind']} date must be YYYY-MM-DD") from exc
    if r["kind"] in {"history", "experience"}:
        for field in ("outcome", "applicability", "coverage_note"):
            _required(r, field, str(path))
        for field in ("modules", "related_records"):
            values = _list(r.get(field, []), f"{path}: {field}")
            if not all(isinstance(value, str) for value in values):
                raise MapError(f"{path}: {field} must contain strings")
    if r["kind"] == "experience":
        _required(r, "task_id", str(path))
    if r["kind"] == "history":
        capture = r.get("history")
        if not isinstance(capture, dict) or not isinstance(capture.get("path"), str) or not re.fullmatch(r"[a-f0-9]{64}", str(capture.get("sha256", ""))):
            raise MapError(f"{path}: history.path and history.sha256 are required")
    aliases = _list(r.get("aliases", []), f"{path}: aliases")
    if not all(isinstance(alias, str) for alias in aliases):
        raise MapError(f"{path}: aliases must contain strings")
    r.update(body=body, source_text=body if source_text is None else source_text,
             path=str(path), line=line, end_line=end, aliases=aliases,
             relations=_relations(r.get("relations", []), f"{path}: relations"), owned=owned)
    return r


def _git_version(base: Path, files: list[Path] | None = None, *, include_dirty: bool = True) -> dict:
    def git(*args: str) -> str | None:
        try:
            p = subprocess.run(["git", "-C", str(base), *args], creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0), text=True, encoding="utf-8", errors="replace", capture_output=True, timeout=8, check=False)
            return p.stdout.strip() if p.returncode == 0 else None
        except (OSError, subprocess.TimeoutExpired):
            return None
    root = git("rev-parse", "--show-toplevel")
    if root is None:
        return {"git_root": None, "git_head": None, "branch": None, "dirty": None}
    root_path = Path(root).resolve()
    scoped = [str(p.resolve()) for p in (files or [base]) if p.resolve().is_relative_to(root_path)]
    status = git("status", "--porcelain", "--untracked-files=normal", "--", *scoped) if include_dirty and scoped else None
    return {"git_root": root, "git_head": git("rev-parse", "HEAD"),
            "branch": git("symbolic-ref", "--quiet", "--short", "HEAD"),
            "dirty": bool(status) if status is not None else None,
            "dirty_scope": "Declared map files" if files else "Selected directory"}


def _validation(doc: dict) -> dict:
    errors, warnings, ids = [], [], {}
    for r in doc["records"]:
        if r["id"] in ids:
            errors.append({"code": "duplicate_id", "id": r["id"], "paths": [ids[r["id"]], r["path"]]})
        ids[r["id"]] = r["path"]
        if r["kind"] in {"exploration", "explorations"} and r["status"] in {"retired", "merged"}:
            warnings.append({"code": "exploration_lifecycle", "id": r["id"], "message": "Retired functionality and exploration outcomes are distinct; record outcome separately."})
    local = doc["project"]["project_id"]
    for rel in doc["relations"]:
        for side in ("from", "to"):
            target = rel[side]
            if target.get("project_id", local) == local and target.get("record_id") and target["record_id"] not in ids:
                errors.append({"code": "dangling_local_relation", "side": side, "record_id": target["record_id"], "relation": rel["relation"]})
    return {"valid": not errors, "errors": errors, "warnings": warnings,
            "scope": "Declared sources and owned records only; external targets are not traversed."}


def _fingerprint_path(path: Path, base: Path) -> str:
    try:
        return os.path.relpath(path, base).replace("\\", "/")
    except ValueError:
        # Windows cannot express a relative path between separate drive mounts.
        # Such declared external sources remain valid, location-bound inputs.
        return path.as_posix()


def _diagram_snapshots(project: dict, base: Path, records: list[dict], read: Any, fingerprints: dict) -> tuple[dict, list[dict]]:
    """Load only explicitly declared native IR, preserving its IDs and fields.

    This checks source readability and local navigation bindings, not the full
    upstream IR schema. A diagram failure must not block ordinary map records.
    """
    declarations = project.get("archify")
    if declarations is None:
        return {}, []
    if not isinstance(declarations, dict):
        return {}, [{"code": "diagram_declaration_invalid", "message": "archify must map architecture/workflow to source declarations"}]
    snapshots, diagnostics = {}, []
    local_records: dict[str, list[dict]] = {}
    for record in records:
        local_records.setdefault(record["id"], []).append(record)
    for kind, declaration in declarations.items():
        if kind not in {"architecture", "workflow"}:
            diagnostics.append({"code": "diagram_kind_unknown", "diagram": str(kind), "message": "Only architecture and workflow declarations are read"})
            continue
        snapshot = {"source_path": None, "source_text": None, "source_sha256": None, "ir": None,
                    "node_records": {}, "record_nodes": {}, "warnings": [], "errors": []}
        snapshots[kind] = snapshot
        if not isinstance(declaration, dict):
            snapshot["errors"].append({"code": "declaration_invalid", "message": "Diagram declaration must be an object with a JSON source path"})
            continue
        source = declaration.get("source")
        if not isinstance(source, str) or not source.strip():
            snapshot["errors"].append({"code": "source_path_invalid", "message": "Diagram source must be a nonempty JSON path relative to the manifest"})
        else:
            try:
                source_path = (base / source).resolve()
                snapshot["source_path"] = str(source_path)
                if source_path.suffix.lower() != ".json":
                    snapshot["errors"].append({"code": "source_format_invalid", "message": "Native diagram sources must be JSON files"})
                else:
                    try:
                        snapshot["source_text"] = read(source_path)
                    except MapError as exc:
                        snapshot["errors"].append({"code": "source_unreadable", "message": str(exc)})
                    snapshot["source_sha256"] = fingerprints.get(source_path)
                    if snapshot["source_text"] is not None:
                        try:
                            ir = json.loads(snapshot["source_text"].removeprefix("\ufeff"))
                            if not isinstance(ir, dict):
                                raise ValueError("Native diagram JSON must contain an object")
                            snapshot["ir"] = ir
                        except (json.JSONDecodeError, ValueError) as exc:
                            snapshot["errors"].append({"code": "source_json_invalid", "message": str(exc)})
            except (OSError, ValueError) as exc:
                snapshot["errors"].append({"code": "source_path_invalid", "message": str(exc)})
        if "repo_root" in declaration:
            root = declaration["repo_root"]
            if not isinstance(root, str) or not root.strip():
                snapshot["warnings"].append({"code": "repo_root_invalid", "message": "repo_root must be a nonempty path; ignored"})
            else:
                try:
                    snapshot["repo_root"] = str((base / root).resolve())
                except (OSError, ValueError) as exc:
                    snapshot["warnings"].append({"code": "repo_root_invalid", "message": str(exc)})
        mappings = declaration.get("node_records", {})
        if not isinstance(mappings, dict):
            snapshot["warnings"].append({"code": "node_records_invalid", "message": "node_records must map native node IDs to arrays of local record IDs; ignored"})
            continue
        # Architecture component IDs and workflow node IDs are the native
        # targets in the bundled upstream architecture/workflow schemas.
        native_counts: dict[str, int] = {}
        ir = snapshot["ir"]
        nodes = ir.get("components" if kind == "architecture" else "nodes", []) if ir is not None else []
        if isinstance(nodes, list):
            for node in nodes:
                if isinstance(node, dict) and isinstance(node.get("id"), str):
                    native_counts[node["id"]] = native_counts.get(node["id"], 0) + 1
        for native_id, bound_ids in mappings.items():
            detail = {"node_id": str(native_id)}
            if not isinstance(native_id, str) or native_counts.get(native_id) != 1:
                snapshot["warnings"].append({"code": "node_binding_invalid", **detail, "message": "Native node ID is missing or ambiguous; binding ignored"})
                continue
            if not isinstance(bound_ids, list):
                snapshot["warnings"].append({"code": "record_binding_invalid", **detail, "message": "Binding value must be an array of local record IDs; ignored"})
                continue
            accepted = []
            for record_id in bound_ids:
                matching = local_records.get(record_id, []) if isinstance(record_id, str) else []
                if len(matching) != 1:
                    snapshot["warnings"].append({"code": "record_binding_invalid", **detail, "record_id": record_id,
                                                 "message": "Local record ID is missing, invalid or ambiguous; binding ignored"})
                    continue
                if record_id in accepted:
                    continue
                accepted.append(record_id)
                snapshot["record_nodes"].setdefault(record_id, []).append(native_id)
                if matching[0]["status"] in HISTORICAL:
                    snapshot["warnings"].append({"code": "historical_record_binding", **detail, "record_id": record_id,
                                                 "message": "Binding retained for a historical record; it does not reactivate the record"})
            if accepted:
                snapshot["node_records"][native_id] = accepted
    for kind, snapshot in snapshots.items():
        for level in ("errors", "warnings"):
            for issue in snapshot[level]:
                diagnostics.append({"code": "diagram_source_error" if level == "errors" else "diagram_source_warning",
                                    "diagram": kind, "detail": issue})
    return snapshots, diagnostics


def load_project(manifest_path: str | Path) -> dict:
    """Read a map from live declared files. Generated readers never become sources.

    Structural duplicate/dangling references appear in result['validation'];
    invalid file formats and unresolvable bindings raise MapError.
    """
    manifest = manifest_file(manifest_path)
    base = manifest.parent
    fingerprints: dict[Path, str] = {}
    loaded_text: dict[Path, str] = {}
    read_errors: dict[Path, str] = {}
    utf8_bom: set[Path] = set()

    def read(path: Path) -> str:
        if path in loaded_text:
            return loaded_text[path]
        if path in read_errors:
            raise MapError(read_errors[path])
        try:
            raw = path.read_bytes()
            fingerprints[path] = hashlib.sha256(raw).hexdigest()
            if raw.startswith(b"\xef\xbb\xbf"):
                utf8_bom.add(path)
            value = raw.decode("utf-8-sig")
        except (OSError, UnicodeError) as exc:
            read_errors[path] = f"Cannot read UTF-8 file {path}: {exc}"
            raise MapError(read_errors[path]) from exc
        loaded_text[path] = value
        return value

    def read_diagram(path: Path) -> str:
        value = read(path)
        return ("\ufeff" if path in utf8_bom else "") + value

    project = _mapping(read(manifest), str(manifest))
    if project.get("schema") != SCHEMA:
        raise MapError(f"{manifest}: schema must be {SCHEMA}")
    for key in ("project_id", "name", "kind", "map"):
        _required(project, key, str(manifest))
    map_path = _resolve_source(base, project["map"])
    map_body = read(map_path)
    sources = {}
    from document_archive import is_archived, stub_body
    archived_source_ids = {b.get("source_id") for b in project.get("bindings", []) if is_archived(b) and b.get("documentation", {}).get("archive_path")} - {b.get("source_id") for b in project.get("bindings", []) if not (is_archived(b) and b.get("documentation", {}).get("archive_path"))}
    for source in _list(project.get("sources", []), "sources"):
        if not isinstance(source, dict):
            raise MapError("sources entries must be objects")
        source_id = _required(source, "source_id", "source")
        if source_id in sources:
            raise MapError(f"Duplicate source_id: {source_id}")
        fmt = source.get("format", "markdown")
        if fmt not in {"markdown", "markdown-table"}:
            raise MapError(f"Unsupported source format {fmt!r} for {source_id}")
        path = _resolve_source(base, source.get("path"))
        sources[source_id] = (source, path, None if source_id in archived_source_ids else read(path))

    records = []
    if (base / "records").is_symlink():
        raise MapError("The owned records directory must not be a symlink")
    owned_root = (base / "records").resolve()
    if owned_root.exists():
        for path in sorted(owned_root.rglob("*.md")):
            resolved = path.resolve()
            if not resolved.is_relative_to(owned_root):
                raise MapError(f"Owned record escapes records directory: {path}")
            text = read(resolved)
            meta, body, line = _frontmatter(text, str(path))
            _required(meta, "title", str(path))
            records.append(_record(meta, body, resolved, line, max(line, len(text.splitlines())), True))
    for binding in _list(project.get("bindings", []), "bindings"):
        if not isinstance(binding, dict):
            raise MapError("bindings entries must be objects")
        source_id = binding.get("source_id")
        if source_id not in sources:
            raise MapError(f"Binding {binding.get('id')!r}: unknown source_id {source_id!r}")
        source, path, text = sources[source_id]
        meta = copy.deepcopy(binding)
        if is_archived(meta) and meta.get("documentation", {}).get("archive_path"):
            body = stub_body(meta)
            line = meta["documentation"].get("original_line", 1)
            records.append(_record(meta, body, path, line, line, False, source_text=body))
            continue
        if source.get("format", "markdown") == "markdown-table":
            if "heading" in binding:
                raise MapError("A table binding uses row_id, not heading")
            row_id = str(binding.get("row_id", binding.get("id", "")))
            column = source.get("id_column")
            if not isinstance(column, str) or not column:
                raise MapError(f"Source {source_id}: markdown-table requires id_column")
            body, line, end, fields = _table_body(text, column, row_id, str(path))
            meta["table_fields"] = fields
        else:
            if "row_id" in binding:
                raise MapError("A Markdown binding uses heading, not row_id")
            body, line, end = _heading_body(text, binding.get("heading"), str(path))
        source_text = "".join(text.splitlines(keepends=True)[line - 1:end])
        records.append(_record(meta, body, path, line, end, False, source_text))

    relations = []
    project_id = project["project_id"]
    for record in records:
        record["source_sha256"] = fingerprints.get(Path(record["path"]), hashlib.sha256(json.dumps(record, sort_keys=True).encode()).hexdigest())
        for item in record["relations"]:
            rel = copy.deepcopy(item)
            rel["from"] = {"project_id": project_id, "record_id": record["id"]}
            rel["to"].setdefault("project_id", project_id)
            relations.append(rel)
    for item in _relations(project.get("relations", []), "project relations"):
        rel = copy.deepcopy(item)
        origin = rel.get("from")
        if isinstance(origin, str):
            origin = {"record_id": origin}
        if not isinstance(origin, dict) or not origin.get("record_id"):
            raise MapError("Project relations require from.record_id")
        rel["from"] = origin
        rel["from"].setdefault("project_id", project_id)
        rel["to"].setdefault("project_id", project_id)
        relations.append(rel)
        if origin["project_id"] == project_id:
            for record in records:
                if record["id"] == origin["record_id"]:
                    record["relations"].append({k: copy.deepcopy(v) for k, v in rel.items() if k != "from"})
    diagram_sources, diagram_warnings = _diagram_snapshots(project, base, records, read_diagram, fingerprints)
    fp = hashlib.sha256()
    file_digests = []
    for path, digest in sorted(fingerprints.items(), key=lambda kv: str(kv[0])):
        relative = _fingerprint_path(path, base)
        fp.update(f"{relative}\0{digest}\n".encode("utf-8"))
        file_digests.append({"path": str(path), "sha256": digest})
    version = _git_version(base, list(fingerprints))
    version["context_scope"] = "Map directory checkout only; this Git HEAD does not cover source files in other repositories. Compare declared source_sha256 values for external files."
    result = {"project": project, "manifest_path": str(manifest), "map_path": str(map_path),
              "map_body": map_body, "records": records, "relations": normalize_relations(relations, project_id),
              "version": version, "fingerprint": fp.hexdigest(),
              "source_files": file_digests, "diagram_sources": diagram_sources}
    result["validation"] = _validation(result)
    result["validation"]["warnings"].extend(diagram_warnings)
    if project.get("kind") == "system":
        from system_map import validate_system
        result["validation"]["errors"].extend(validate_system(result))
        result["validation"]["valid"] = not result["validation"]["errors"]
    return result


def _atomic_write(path: Path, text: str, *, overwrite: bool = True) -> None:
    """Replace a known target atomically; refuse directory/symlink write targets."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_symlink() or path.is_dir():
        raise MapError(f"Refusing to replace symlink or directory: {path}")
    if path.exists() and not overwrite:
        raise MapError(f"Refusing to overwrite: {path}")
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as f:
            f.write(text)
            f.flush()
            os.fsync(f.fileno())
        # Non-overwriting init uses exclusive creation to avoid a race.
        if not overwrite:
            try:
                os.link(temporary, path)
            except FileExistsError as exc:
                raise MapError(f"Refusing to overwrite: {path}") from exc
        else:
            os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def init_project(directory: str | Path, name: str | None = None, project_id: str | None = None, kind: str = "software") -> dict:
    """Create only project.yaml/map.md. An existing map is returned unchanged."""
    import uuid
    base = Path(directory).expanduser().resolve()
    manifest = base / "project.yaml"
    if manifest.exists():
        doc = load_project(manifest)
        if project_id and project_id != doc["project"]["project_id"]:
            raise MapError("Existing project ID differs; init never changes a project's identity")
        return {"created": False, "manifest_path": str(manifest), "project_id": doc["project"]["project_id"]}
    if (base / "map.md").exists():
        raise MapError("map.md already exists without a manifest; bind it manually rather than overwrite")
    title = name or base.name
    project = {"schema": SCHEMA, "project_id": project_id or str(uuid.uuid4()), "name": title,
               "kind": kind, "map": "map.md", "sources": [], "bindings": []}
    # JSON is a YAML subset and keeps this zero-dependency initialization simple.
    _atomic_write(base / "map.md", f"# {title}\n\nDescribe the project's purpose, current abilities, and important boundaries here.\n", overwrite=False)
    _atomic_write(manifest, json.dumps(project, ensure_ascii=False, indent=2) + "\n", overwrite=False)
    return {"created": True, "manifest_path": str(manifest), "project_id": project["project_id"]}


def registry_file(value: str | Path | None = None) -> Path:
    return Path(value or os.environ.get("PROJECT_MAP_REGISTRY") or Path.home() / ".codex/project-maps/registry.json").expanduser().absolute()


def _registry(path: Path) -> dict:
    if not path.exists():
        return {"schema": "project-map-registry/v1", "projects": {}}
    data = _mapping(_text(path), str(path))
    if data.get("schema") != "project-map-registry/v1" or not isinstance(data.get("projects"), dict):
        raise MapError(f"Invalid project registry: {path}")
    return data


@contextmanager
def _registry_writer_lock(path: Path, timeout: float = 3.0):
    """Serialize local registry writers using an exclusive, owned lock file.

    A crashed writer leaves a visible lock. We never infer that it is stale or
    remove an unrecognized lock; timeout asks the caller to inspect ownership.
    """
    import uuid
    if timeout < 0:
        raise MapError("Registry lock timeout must be nonnegative")
    path.parent.mkdir(parents=True, exist_ok=True)
    lock = path.with_name(path.name + ".lock")
    deadline = time.monotonic() + timeout
    while True:
        try:
            fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            break
        except FileExistsError as exc:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise MapError(f"Project registry busy: writer lock {lock} still exists after {timeout:g}s. Retry later or inspect the lock owner; no existing lock was removed.") from exc
            time.sleep(min(0.05, remaining))
    token = str(uuid.uuid4())
    payload = json.dumps({"token": token, "pid": os.getpid(), "created_at": datetime.now(timezone.utc).isoformat()})
    try:
        os.write(fd, payload.encode("utf-8"))
        os.fsync(fd)
        yield
    finally:
        os.close(fd)
        # Only clean up the lock created by this invocation, even if another
        # actor replaced its pathname while we were running.
        try:
            if lock.is_file() and not lock.is_symlink() and _text(lock) == payload:
                lock.unlink()
        except FileNotFoundError:
            pass


def register_project(manifest_path: str | Path, registry: str | Path | None = None, *, lock_timeout: float = 3.0) -> dict:
    doc = load_project(manifest_path)
    path = registry_file(registry)
    pid = doc["project"]["project_id"]
    with _registry_writer_lock(path, lock_timeout):
        data = _registry(path)
        before = copy.deepcopy(data)
        entry = data["projects"].setdefault(pid, {"name": doc["project"]["name"], "locations": []})
        entry["name"] = doc["project"]["name"]
        locations = entry.setdefault("locations", [])
        location = {"manifest_path": doc["manifest_path"]}
        if location not in locations:
            locations.append(location)
        changed = data != before
        if changed:
            _atomic_write(path, json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    return {"project_id": pid, "registry_path": str(path), "locations": locations, "changed": changed}


def resolve_project(project_id: str, registry: str | Path | None = None, *, manifest: str | Path | None = None, current: str | Path | None = None) -> dict:
    if manifest:
        doc = load_project(manifest)
        if doc["project"]["project_id"] != project_id:
            raise MapError("Explicit manifest has a different project_id")
        return {"status": "resolved", "project_id": project_id, "manifest_path": doc["manifest_path"], "selection": "explicit"}
    data = _registry(registry_file(registry))
    entry = data["projects"].get(project_id)
    if entry is None:
        return {"status": "unresolved", "project_id": project_id, "reason": "Project ID is not registered", "locations": []}
    candidates, missing, mismatched = [], [], []
    for item in entry.get("locations", []):
        p = Path(item["manifest_path"]).expanduser().resolve()
        if not p.is_file():
            missing.append(str(p))
            continue
        actual = _mapping(_text(p), str(p))
        if actual.get("project_id") != project_id:
            mismatched.append(str(p))
            continue
        if str(p) not in candidates:
            candidates.append(str(p))
    target = Path(current or Path.cwd()).expanduser().resolve()
    matching = [p for p in candidates if target == Path(p) or target.is_relative_to(Path(p).parent)]
    # A map lives in docs/project/ in many repositories; Git worktree identity is
    # a valid current-location hint but never collapses two matching locations.
    if not matching:
        current_root = _git_version(target if target.is_dir() else target.parent, include_dirty=False).get("git_root")
        if current_root:
            matching = [p for p in candidates if _git_version(Path(p).parent, include_dirty=False).get("git_root") == current_root]
    if len(matching) == 1:
        return {"status": "resolved", "project_id": project_id, "manifest_path": matching[0], "selection": "current_location"}
    preferred = entry.get("preferred_manifest")
    if preferred and not matching:
        preferred = str(Path(preferred).expanduser().resolve())
        if preferred in candidates:
            return {"status": "resolved", "project_id": project_id, "manifest_path": preferred, "selection": "preferred_location"}
        return {"status": "unresolved", "project_id": project_id, "locations": candidates,
                "missing_locations": missing, "mismatched_locations": mismatched,
                "reason": "Preferred location unavailable; choose an explicit manifest/worktree"}
    if len(candidates) == 1:
        return {"status": "resolved", "project_id": project_id, "manifest_path": candidates[0], "selection": "only_location"}
    return {"status": "ambiguous" if candidates else "unresolved", "project_id": project_id,
            "locations": matching or candidates, "missing_locations": missing, "mismatched_locations": mismatched,
            "reason": "Choose an explicit manifest/worktree" if candidates else "No matching live location"}


def _find(doc: dict, record_id: str) -> dict:
    records = [r for r in doc["records"] if r["id"] == record_id]
    if len(records) != 1:
        raise MapError(f"Record ID {record_id!r} matched {len(records)} records")
    return records[0]


def _brief(record: dict) -> dict:
    result = {k: record[k] for k in ("id", "kind", "title", "summary", "status", "progress", "gap", "aliases", "path", "line", "end_line")}
    if record["kind"] == "update":
        result["date"] = record["date"]
    if record.get("documentation"):
        result["documentation"] = record["documentation"]
    return result


def search_project(doc: dict, query: str, limit: int = 8, current_only: bool = True, module: str | None = None, *, kinds: list[str] | None = None, match: str = "auto", offset: int = 0, retrieval: str = "lexical") -> dict:
    q = query.casefold().strip()
    if not q:
        raise MapError("Search needs a nonempty query")
    if limit < 1 or offset < 0:
        raise MapError("limit must be positive and offset nonnegative")
    if retrieval not in {"auto", "lexical", "hybrid"}:
        raise MapError("retrieval must be auto, lexical or hybrid")
    if retrieval == "hybrid" and match != "auto":
        raise MapError("Strict --match modes require lexical retrieval; use --match auto with hybrid.")
    from system_map import module_records
    from record_search import rank_records
    from document_archive import is_archived, with_history
    if not current_only:
        doc = with_history(doc)
    candidates, _ = module_records(doc, module)
    candidates = [r for r in candidates if (not current_only or r["status"] not in HISTORICAL and not is_archived(r)) and (not kinds or r["kind"] in kinds)]
    matches, mode, terms = rank_records(candidates, q, match)
    retrieval_info = {"requested": retrieval, "mode": "lexical", "status": "ready"}
    for _, info in matches:
        info["retrieved_by"] = ["lexical"]
    if retrieval == "auto" and match != "auto":
        retrieval_info["status"] = "strict_lexical_match"
    elif retrieval == "auto" and any(q == r["id"].casefold() for r in candidates):
        retrieval_info["status"] = "exact_id"
    elif retrieval != "lexical" and candidates:
        from semantic_retrieval import SemanticError, semantic_search, fuse, WINDOW, RRF_K
        try:
            semantic, diagnostics = semantic_search(doc, candidates, query.strip())
            lexical, mode, terms = rank_records(candidates, q, match, hybrid_candidates=True)
            matches = fuse(lexical, semantic, q)
            retrieval_info.update(mode="hybrid", candidate_window=WINDOW, rrf_k=RRF_K, diagnostics=diagnostics)
        except (SemanticError, OSError, RuntimeError) as exc:
            if retrieval == "hybrid":
                raise MapError(f"Hybrid retrieval unavailable: {exc}") from exc
            retrieval_info.update(status="degraded", reason=str(exc), reason_code=getattr(exc, "code", "local_unavailable"))
    elif not candidates:
        retrieval_info["status"] = "no_eligible_records"
    end = offset + limit
    from source_inventory import source_health
    results = []
    for record, info in matches[offset:end]:
        result = {**_brief(record), **info}
        health = source_health(doc, record)
        if health: result["source_health"] = health
        results.append(result)
    return {"project_id": doc["project"]["project_id"], "query": query, "scope": "current" if current_only else "current_and_historical", "module_id": module,
            "kinds": kinds or [], "match_mode": mode, "query_terms": terms, "retrieval": retrieval_info,
            "results": results, "total": len(matches), "truncated": len(matches) > end,
            "next_offset": end if len(matches) > end else None,
            "fingerprint": doc["fingerprint"], "coverage": ("Union of top 50 records per retrieval channel; total is candidate count, not all relevant records. Semantic proximity is not verified relevance. " if retrieval_info["mode"] == "hybrid" else "") + "Candidates and excerpts only; read selected IDs for their constraints.",
            **({"next_step": "Try fewer keywords or aliases; inspect modules; use --include-history for old names. No match is not proof of absence."} if not matches else {})}


def read_record(doc: dict, record_id: str, *, offset: int = 0, max_chars: int = 6000, max_lines: int = 120, expected_fingerprint: str | None = None, expected_record_fingerprint: str | None = None, include_history: bool = False) -> dict:
    if expected_fingerprint is not None and expected_fingerprint != doc["fingerprint"]:
        raise MapError("Project sources changed after the previous read; locate the record again before continuing by offset")
    r = _find(doc, record_id)
    from document_archive import is_archived, historical_record, stub_body
    if is_archived(r):
        r = historical_record(doc, r) if include_history else {**r, "body": stub_body(r), "source_text": stub_body(r)}
    from system_map import record_fingerprint
    record_digest = record_fingerprint(r)
    if expected_record_fingerprint is not None and expected_record_fingerprint != record_digest:
        raise MapError("Record or its source changed; locate the record again before continuing")
    body = r["body"]
    if offset < 0 or offset > len(body) or max_chars < 1 or max_lines < 1:
        raise MapError("Read offset must be within the body and limits must be positive")
    remainder = body[offset:]
    text = "".join(remainder.splitlines(keepends=True)[:max_lines])[:max_chars]
    end = offset + len(text)
    truncated = end < len(body)
    first_line = r["line"] + body[:offset].count("\n")
    # Table bodies are a field projection of one original source line.
    projected = "table_fields" in r
    span = {"start": r["line"] if projected else first_line,
            "end": r["end_line"] if projected else first_line + max(0, len(text.splitlines()) - 1),
            "projected": projected}
    metadata = {k: v for k, v in r.items() if k not in {"body", "source_text"}}
    from source_locations import resolve_sources
    from source_inventory import source_health
    health = source_health(doc, r)
    return {"project_id": doc["project"]["project_id"], "record": metadata, "body": text,
            "receipt": "opened_partial" if truncated or offset else "opened_full", "offset_unit": "unicode_code_points",
            "offset": offset, "end_offset": end, "total_chars": len(body), "source_lines": span,
            "truncated": truncated, "record_fingerprint": record_digest,
            "coverage": "Partial body; unread constraints may remain. Continue reading before claiming full coverage." if truncated or offset else "Complete body of this record only; related records and source code are not implied to have been read.",
            "continuation": {"record_id": record_id, "offset": end, "fingerprint": doc["fingerprint"], "record_fingerprint": record_digest, "include_history": include_history} if truncated else None,
            "fingerprint": doc["fingerprint"], "version": doc["version"], **resolve_sources(doc, r), **({"source_health": health} if health else {})}


def related_records(doc: dict, record_id: str, *, limit: int = 30) -> dict:
    _find(doc, record_id)
    pid = doc["project"]["project_id"]
    target = {"project_id": pid, "record_id": record_id}
    relations = [r for r in doc["relations"] if all(r["from"].get(k) == v for k, v in target.items()) or all(r["to"].get(k) == v for k, v in target.items())]
    return {"project_id": pid, "record_id": record_id, "relations": relations[:limit], "total": len(relations),
            "truncated": len(relations) > limit, "scope": "Explicit relations in this map; external targets preserved without traversal"}


def set_lifecycle(manifest_path: str | Path, record_id: str, state: str, reason: str, successor: str | None = None) -> dict:
    if state not in {"retired", "merged"} or not reason.strip():
        raise MapError("Lifecycle changes require retired/merged state and a nonempty reason")
    doc = load_project(manifest_path)
    record = _find(doc, record_id)
    if record["kind"] in {"exploration", "explorations"}:
        raise MapError("Exploration outcomes are distinct from retirement; edit outcome and evidence in the exploration source")
    if not record["owned"]:
        raise MapError("This record binds an existing source. Update its binding metadata deliberately; retire/merge only writes owned records")
    if state == "merged" and not successor:
        raise MapError("Merge requires a successor record ID")
    if successor:
        if successor == record_id:
            raise MapError("A record cannot succeed itself")
        _find(doc, successor)
    owned = (Path(doc["manifest_path"]).parent / "records").resolve()
    path = Path(record["path"])
    if path.is_symlink() or not path.resolve().is_relative_to(owned):
        raise MapError("Refusing to write a record outside the owned records directory")
    original = _text(path)
    metadata, body, _ = _frontmatter(original, str(path))
    metadata["status"] = state
    metadata["lifecycle"] = {**metadata.get("lifecycle", {}), "reason": reason, "changed_at": datetime.now(timezone.utc).isoformat()}
    if successor:
        metadata["lifecycle"]["successor"] = {"record_id": successor}
        rel = {"relation": "superseded_by", "to": {"record_id": successor}, "reason": reason}
        metadata.setdefault("relations", [])
        if not any(r.get("relation") == rel["relation"] and r.get("to") == rel["to"] for r in metadata["relations"]):
            metadata["relations"].append(rel)
    # Preserve unknown metadata and exact Markdown body. JSON inside frontmatter
    # remains valid YAML and avoids lossy coercions during serialization.
    replacement = "---\n" + json.dumps(metadata, ensure_ascii=False, indent=2) + "\n---\n" + body
    if _text(path) != original:
        raise MapError("Record changed during update; retry against its current contents")
    _atomic_write(path, replacement)
    return {"project_id": doc["project"]["project_id"], "record_id": record_id, "status": state,
            "path": str(path), "successor": successor, "body_preserved": True, "code_removed": False}


def _positive(value: str) -> int:
    number = int(value)
    if number < 1:
        raise argparse.ArgumentTypeError("Must be positive")
    return number


def cli(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("init", help="Create a minimal map without scanning or initializing Git")
    p.add_argument("path"); p.add_argument("--name"); p.add_argument("--project-id"); p.add_argument("--kind", default="software")
    p = sub.add_parser("register"); p.add_argument("path"); p.add_argument("--registry")
    p = sub.add_parser("resolve"); p.add_argument("project_id"); p.add_argument("--registry"); p.add_argument("--manifest"); p.add_argument("--current")
    p = sub.add_parser("discover", help="Find the nearest map using conventional paths, without a recursive scan")
    p.add_argument("path", nargs="?", default="."); p.add_argument("--stop", help="Inclusive workspace/project boundary")
    for cmd in ("members", "interfaces", "impact", "modules"):
        descriptions = {"members": "List explicitly collected projects and resolution gaps", "interfaces": "Find canonical contracts and known consumers without loading their bodies", "impact": "List declared relations touching a project or record; not inferred runtime impact", "modules": "List module IDs for scoped search"}
        examples = {"members": "members SYSTEM --limit 5 --offset 5", "interfaces": "interfaces SYSTEM --query Adapter --limit 5", "impact": "impact SYSTEM IF-example --project PROVIDER-ID", "modules": "modules PROJECT --limit 8"}
        p = sub.add_parser(cmd, help=descriptions[cmd], description=descriptions[cmd], epilog="Example: project_map.py " + examples[cmd])
        p.add_argument("path", help="Project or system manifest/directory")
        p.add_argument("--limit", type=_positive, default=8)
        p.add_argument("--offset", type=int, default=0)
        p.add_argument("--registry", help="Optional local project registry")
        if cmd in {"interfaces", "impact"}:
            p.add_argument("--project", help="Owner project ID; never a guessed name")
        if cmd == "interfaces":
            p.add_argument("--query", default="", help="Substring in interface name, ID or summary")
        if cmd == "impact":
            p.add_argument("record_id", nargs="?", help="Omit to query relations for the project")
    for cmd in ("source", "bind-workspace", "review-record", "archive-record"):
        p = sub.add_parser(cmd)
        p.add_argument("path")
        if cmd == "source":
            p.add_argument("--workspace")
            p.add_argument("--kind", choices=("summary", "entrypoint", "dependency", "call", "symbol", "gap", "review", "coverage"), default="summary")
            p.add_argument("--query", default="")
            p.add_argument("--limit", type=_positive, default=12)
            p.add_argument("--offset", type=int, default=0)
        elif cmd == "bind-workspace":
            p.add_argument("workspace_id"); p.add_argument("root")
            p.add_argument("--python-root", action="append")
            p.add_argument("--exclude", action="append")
        else:
            p.add_argument("record_id"); p.add_argument("--reason", required=True)
            if cmd == "archive-record":
                p.add_argument("--evidence", required=True); p.add_argument("--successor")
    for cmd in ("search", "read", "related", "validate", "retire", "merge", "export"):
        p = sub.add_parser(cmd)
        p.add_argument("path", help="Project directory or project.yaml")
        if cmd in {"search", "read"}:
            p.add_argument("--detail", choices=("compact", "full"), default="compact", help="Compact model output by default; full retains all metadata")
        if cmd == "search":
            p.add_argument("query"); p.add_argument("--limit", type=_positive, default=8)
            scope = p.add_mutually_exclusive_group()
            scope.add_argument("--current-only", dest="current_only", action="store_true", default=True, help="Default: exclude retired/superseded/archived records")
            scope.add_argument("--include-history", dest="current_only", action="store_false", help="Also search historical statuses")
            p.add_argument("--module", help="Stable module record ID; locate with modules")
            p.add_argument("--kind", action="append", help="Record type; repeat for multiple types")
            p.add_argument("--match", choices=("auto", "all", "any", "phrase"), default="auto", help="Lexical matching; strict modes select lexical retrieval")
            p.add_argument("--retrieval", choices=("auto", "lexical", "hybrid"), default="auto", help="auto: local hybrid if configured, explicit lexical fallback otherwise; hybrid fails if unavailable")
            p.add_argument("--offset", type=int, default=0)
        if cmd in {"read", "related", "retire", "merge"}:
            p.add_argument("record_id")
        if cmd == "read":
            p.add_argument("--include-history", action="store_true", help="Explicitly open preserved archived content")
            p.add_argument("--offset", type=int, default=0); p.add_argument("--max-chars", type=_positive, default=6000); p.add_argument("--max-lines", type=_positive, default=120)
            p.add_argument("--fingerprint", help="Require the previous read's fingerprint when continuing by offset")
            p.add_argument("--record-fingerprint", help="Check only this record/source; unrelated map edits may continue")
        if cmd == "related":
            p.add_argument("--limit", type=_positive, default=30)
        if cmd in {"retire", "merge"}:
            p.add_argument("--reason", required=True); p.add_argument("--successor", required=cmd == "merge")
        if cmd == "export":
            p.add_argument("--output", required=True, help="Write complete reader data to a JSON file, not model context")
    args = parser.parse_args(argv)
    try:
        code = 0
        if args.command == "init":
            result = init_project(args.path, args.name, args.project_id, args.kind)
        elif args.command == "register":
            result = register_project(args.path, args.registry)
        elif args.command == "resolve":
            result = resolve_project(args.project_id, args.registry, manifest=args.manifest, current=args.current)
            code = 0 if result["status"] == "resolved" else 2
        elif args.command == "discover":
            result = discover_project(args.path, args.stop)
            code = 0 if result["status"] == "resolved" else 2
        elif args.command in {"retire", "merge"}:
            result = set_lifecycle(args.path, args.record_id, "retired" if args.command == "retire" else "merged", args.reason, args.successor)
        elif args.command == "archive-record":
            from document_archive import archive_record
            result = archive_record(args.path, args.record_id, args.reason, args.evidence, args.successor)
        elif args.command in {"source", "bind-workspace", "review-record"}:
            from source_inventory import source_query, bind_workspace, review_record_sources
            if args.command == "source": result = source_query(args.path, args.workspace, args.kind, args.query, args.limit, args.offset)
            elif args.command == "bind-workspace": result = bind_workspace(args.path, args.workspace_id, args.root, args.python_root, args.exclude)
            else: result = review_record_sources(args.path, args.record_id, args.reason)
        else:
            doc = load_project(args.path)
            if args.command == "search":
                result = search_project(doc, args.query, args.limit, args.current_only, args.module, kinds=args.kind, match=args.match, offset=args.offset, retrieval=args.retrieval)
            elif args.command == "read":
                result = read_record(doc, args.record_id, offset=args.offset, max_chars=args.max_chars, max_lines=args.max_lines, expected_fingerprint=args.fingerprint, expected_record_fingerprint=args.record_fingerprint, include_history=args.include_history)
            elif args.command in {"members", "interfaces", "impact", "modules"}:
                from system_map import query_system, module_records, page
                if args.command == "modules":
                    _, scopes = module_records(doc)
                    result = {**page([_brief(r) for r in doc['records'] if r['kind'] == 'module'], args.limit, args.offset), "scope": "Module records; explicit module_id or nearest module overview owns records"}
                else:
                    result = query_system(doc, args.command, registry=args.registry, limit=args.limit, offset=args.offset, project=getattr(args, 'project', None), query=getattr(args, 'query', ''), record=getattr(args, 'record_id', None))
            elif args.command == "related":
                result = related_records(doc, args.record_id, limit=args.limit)
            elif args.command == "validate":
                result = {"project_id": doc["project"]["project_id"], "record_count": len(doc["records"]), **doc["validation"]}
                code = 0 if result["valid"] else 2
            elif args.command == "export":
                output = Path(args.output).expanduser().absolute()
                protected = {Path(x["path"]) for x in doc["source_files"]}
                protected.update(Path(source["source_path"]) for source in doc["diagram_sources"].values() if source["source_path"])
                if output.suffix.lower() != ".json" or output.resolve() in protected:
                    raise MapError("Export needs a .json target separate from project source files")
                _atomic_write(output, json.dumps(doc, ensure_ascii=False, indent=2) + "\n")
                result = {"output": str(output), "record_count": len(doc["records"]), "fingerprint": doc["fingerprint"], "valid": doc["validation"]["valid"]}
        if getattr(args, "detail", None) == "compact":
            from record_search import compact_response
            result = compact_response(args.command, result)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return code
    except (ValueError, OSError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    raise SystemExit(cli())
