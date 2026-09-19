"""Archive obsolete explanations independently of feature / requirement lifecycle."""
from __future__ import annotations

import copy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import uuid


def is_archived(record):
    return (record.get("documentation") or {}).get("state") == "archived" or record.get("status") == "archived"


def stub_body(meta):
    archive = meta.get("documentation", {})
    successor = archive.get("successor")
    text = "这份说明已归档，不代表相关功能退役或需求撤销。\n\n原因：" + archive.get("reason", "原记录标为已归档。") + "\n\n"
    text += "当前说明：[[" + successor + "]]。\n" if successor else "当前说明缺口：尚未登记替代文档，不能沿用旧正文判断当前实现。\n"
    return text + "\n需要旧正文时显式查看历史；默认查询只返回本提示和替代定位。\n"


def historical_record(doc, record):
    from project_map import _frontmatter, _record
    archive = record.get("documentation", {})
    if not archive.get("archive_path"):
        return record
    base = Path(doc["manifest_path"]).parent.resolve()
    root = (base / "archive").resolve()
    if not root.is_relative_to(base): raise ValueError("Archive directory escapes map")
    path = (base / archive["archive_path"]).resolve()
    if not path.is_relative_to(root): raise ValueError("Archive locator escapes archive directory")
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != archive.get("sha256"):
        raise ValueError("Archived snapshot changed; cannot present it as the preserved original")
    meta, body, line = _frontmatter(raw.decode("utf-8-sig"), str(path))
    if meta.get("id") != record["id"]: raise ValueError("Archive record identity mismatch")
    meta["documentation"] = copy.deepcopy(archive)
    meta.pop("table_fields", None)
    result = _record(meta, body, path, line, len(raw.decode("utf-8-sig").splitlines()), False)
    result["source_sha256"] = archive["sha256"]
    result["historical_body"] = True
    from system_map import module_records
    _, modules = module_records(doc)
    if modules.get(record["id"]): result["module_id"] = modules[record["id"]]
    return result


def with_history(doc):
    return {**doc, "records": [historical_record(doc, r) if is_archived(r) else r for r in doc["records"]]}


def preserve_archive_bytes(base):
    """Git must retain the exact archived bytes used by the evidence hash."""
    from project_map import _atomic_write
    path = base / "archive/.gitattributes"
    if not path.resolve().is_relative_to(base.resolve()):
        raise ValueError("Archive attributes escape map")
    original = path.read_text(encoding="utf-8") if path.exists() else ""
    rule = "records/** -text whitespace=cr-at-eol"
    if rule not in original.splitlines():
        _atomic_write(path, original.rstrip("\n") + ("\n" if original else "") + rule + "\n")


def archive_record(manifest, record_id, reason, evidence, successor=None):
    from project_map import load_project, _find, _text, _frontmatter, _atomic_write, manifest_file, _registry_writer_lock
    if not reason.strip() or not evidence.strip():
        raise ValueError("Archiving requires a confirmed-obsolete reason and the evidence checked; source change alone is insufficient")
    manifest = manifest_file(manifest)
    with _registry_writer_lock(manifest):
        doc = load_project(manifest)
        record = _find(doc, record_id)
        if record.get("documentation", {}).get("archive_path"):
            historical_record(doc, record)
            preserve_archive_bytes(manifest.parent)
            return {"record_id": record_id, "changed": False, "documentation": record["documentation"]}
        if successor:
            replacement = _find(doc, successor)
            if successor == record_id or is_archived(replacement) or replacement["status"] in {"retired", "merged", "superseded", "withdrawn"}:
                raise ValueError("Successor must be a different current explanation")
        base = manifest.parent.resolve()
        archive_root = (base / "archive/records").resolve()
        if not archive_root.is_relative_to(base): raise ValueError("Archive directory escapes map")
        path = Path(record["path"])
        if record["owned"]:
            if not path.resolve().is_relative_to((base / "records").resolve()): raise ValueError("Owned record escaped its directory")
            original = path.read_bytes()
            meta, _, _ = _frontmatter(original.decode("utf-8-sig"), str(path))
            owner, owner_before = path, original
        else:
            meta = next(copy.deepcopy(b) for b in doc["project"]["bindings"] if b["id"] == record_id)
            meta["original_source"] = {"path": str(path), "line": record["line"], "end_line": record["end_line"], "source_text": record["source_text"]}
            original = ("---\n" + json.dumps(meta, ensure_ascii=False, indent=2) + "\n---\n" + record["body"]).encode("utf-8")
            owner, owner_before = manifest, manifest.read_bytes()
        stamp = datetime.now(timezone.utc).isoformat()
        filename = hashlib.sha256(record_id.encode()).hexdigest()[:12] + "-" + uuid.uuid4().hex[:12] + ".md"
        target = archive_root / filename
        archive = {"state": "archived", "reason": reason, "evidence": evidence, "archived_at": stamp,
                   "archive_path": target.relative_to(base).as_posix(), "sha256": hashlib.sha256(original).hexdigest(),
                   "original_path": Path(os.path.relpath(path, base)).as_posix() if path.drive == base.drive else str(path), "original_line": record["line"], "original_end_line": record["end_line"],
                   "map_version": {k: doc["version"].get(k) for k in ("git_head", "branch", "dirty")},
                   "successor": successor, "current_gap": not bool(successor)}
        if not record["owned"]: meta.pop("original_source", None)
        meta["documentation"] = archive
        meta["summary"] = "说明已归档；" + ("当前说明见 " + successor if successor else "尚无替代说明，存在当前说明缺口")
        meta["progress"] = ""
        meta["gap"] = "尚无替代说明" if not successor else ""
        if record["owned"]:
            replacement_text = "---\n" + json.dumps(meta, ensure_ascii=False, indent=2) + "\n---\n" + stub_body(meta)
        else:
            project = copy.deepcopy(doc["project"])
            project["bindings"] = [meta if b["id"] == record_id else b for b in project["bindings"]]
            replacement_text = json.dumps(project, ensure_ascii=False, indent=2) + "\n"
        archive_root.mkdir(parents=True, exist_ok=True)
        preserve_archive_bytes(base)
        with target.open("xb") as stream: stream.write(original)
        try:
            if owner.read_bytes() != owner_before: raise ValueError("Record changed during archival; reload and recheck")
            _atomic_write(owner, replacement_text)
        except BaseException:
            target.unlink()
            raise
        return {"record_id": record_id, "changed": True, "documentation": archive,
                "feature_status": record["status"], "original_content_preserved": True, "external_source_modified": False}
