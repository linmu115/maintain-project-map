#!/usr/bin/env python3
"""Export one map into an offline human reader. No LLM or web service needed."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import hashlib
import html
import os
from pathlib import Path
import sys
import tempfile

from archify_adapter import render_diagrams, diagram_targets, protect_targets
from reader_content import LocalDocuments, build_navigation
from reader_markdown import markdown_html
from project_map import normalize_relations
from development_history import prepare_export, evidence_renderer
from document_archive import is_archived, stub_body, historical_record

ASSETS = Path(__file__).resolve().parent.parent / "assets"
READER_VERSION = "system-map-v1"


def safe_json(data: dict) -> str:
    return json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")


def export_reader(data: dict, output: Path, mode: str = "a", node: str | None = None, diagrams: bool = True, *, public_root: Path | None = None) -> dict:
    output = Path(output).resolve()
    if output.suffix.lower() != ".html":
        raise ValueError("Reader output must have an .html extension.")
    if output.name.lower() in {p.name for p in diagram_targets(output.parent)}:
        raise ValueError("Reader output cannot use a reserved diagram filename.")
    if mode not in {"a", "b"}:
        raise ValueError("Reader mode must be a or b.")
    if public_root is not None:
        from public_export import check_public_scope
        public_root = Path(public_root).resolve()
        check_public_scope(data, output, public_root)
    # Historical originals are separate, explicitly opened pages, never inline data.
    original = data
    data = {**data, "records": [{**r, "body": stub_body(r), "source_text": stub_body(r),
                                "summary": "说明已归档，见替代入口或说明缺口。", "progress": ""}
                               if is_archived(r) else r for r in data["records"]]}
    archive_assets, archive_errors = {}, {}
    archive_links = LocalDocuments(data)
    for record in original["records"]:
        if not is_archived(record): continue
        name = "archive/" + hashlib.sha256(record["id"].encode()).hexdigest()[:20] + ".html"
        try:
            old = historical_record(original, record)
            context = Path(data["manifest_path"]).parent / record.get("documentation", {}).get("original_path", record["path"])
            resolver = archive_links.renderer(context, record["id"])
            body = markdown_html(old["body"], resolver, record["id"])
            body = body.replace('href="#', 'href="../' + html.escape(output.name, quote=True) + '#')
            back = LocalDocuments.link("返回当前说明入口", {"mode": "b", "record": record["id"]}, "record", record["id"])
            back = back.replace('href="#', 'href="../' + html.escape(output.name, quote=True) + '#')
            archive_assets[name] = ('<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>归档说明</title>'
                '<style>body{font:16px/1.75 system-ui,sans-serif;color:#222;background:#fff;max-width:900px;margin:40px auto;padding:0 24px}a{color:inherit}pre{overflow:auto;padding:16px;background:#f7f7f6}h1{font-size:26px}table{border-collapse:collapse}td,th{border:1px solid #ddd;padding:6px 12px}</style>'
                '<main><h1>归档说明 · ' + html.escape(record["title"]) + '</h1><p>此页保留历史原文，不能作为当前实现依据。</p>' + back + '<hr>' + body + '</main></html>')
        except (OSError, ValueError) as exc:
            archive_errors[record["id"]] = str(exc)
        else:
            next(r for r in data["records"] if r["id"] == record["id"])["archive_page"] = name
    history, history_assets = prepare_export(data, public=public_root is not None)
    history_captures = history.pop("_captures")
    targets = [output, output.parent / "docs.json", output.parent / "history-assets.json"]
    targets.extend(output.parent / name for name in history_assets)
    targets.extend(output.parent / name for name in archive_assets)
    if any(not target.resolve().is_relative_to(output.parent) for target in targets):
        raise ValueError("Reader assets must stay within the export directory.")
    if diagrams:
        targets.extend(diagram_targets(output.parent))
    protect_targets(data, targets)
    output.parent.mkdir(parents=True, exist_ok=True)
    payload = dict(data)
    payload["development_history"] = history
    payload["reader_version"] = READER_VERSION
    if data["project"].get("kind") == "system":
        from system_map import compose_system
        payload["system_view"] = compose_system(data)
    # The human reader needs graph results and locators, not another inline copy
    # of the full native JSON source (which already has its own snapshot file).
    payload.pop("diagram_sources", None)
    payload["default_mode"] = mode
    payload["exported_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    links = LocalDocuments(data)
    payload["relations"] = normalize_relations(data.get("relations", []), data["project"]["project_id"])
    payload["navigation"] = build_navigation(data)
    payload["map_html"] = markdown_html(data.get("map_body", ""), links.renderer(links.map_path), "map")
    payload["records"] = []
    for record in data.get("records", []):
        resolver = links.renderer(record["path"], record["id"])
        if record["kind"] in {"history", "experience"} and record.get("task_id", record["id"]) in history["tasks"] and not is_archived(record):
            resolver = evidence_renderer(resolver, record, history["tasks"][record.get("task_id", record["id"])])
        item = {**record, "body_html": markdown_html(record.get("body", ""), resolver, record["id"])}
        from source_inventory import source_health
        health = source_health(data, record)
        if health: item["source_health"] = health
        if record["id"] in archive_errors: item["archive_error"] = archive_errors[record["id"]]
        # Source bytes and fingerprint must come from the same load snapshot.
        # A table binding can project fields into body while source_text retains
        # its original row. Do not read the path again after load_project.
        if "source_text" not in record:
            item["source_text"] = record.get("body", "")
            item["source_note"] = "此快照未提供原文摘录；此处保留加载时的正文。"
        payload["records"].append(item)
    payload["linked_documents"] = links.render_documents(markdown_html)
    protect_targets({**data, "source_files": data.get("source_files", []) + list(links.documents.values())}, targets)
    if diagrams:
        payload["diagrams"] = render_diagrams({**data, "system_view": payload.get("system_view", {})}, output.parent, node=node, reader_file=output.name)
    else:
        payload["diagrams"] = {kind: {"file": None, "reason": "本次仅导出了阅读文档。"} for kind in ("architecture", "workflow")}
    if public_root is not None:
        from public_export import portable, public_payload
        payload = public_payload(payload, public_root, output.parent)
        archive_assets = portable(archive_assets, public_root, output.parent)
        for spec in payload["diagrams"].values():
            if not spec.get("file") or not spec.get("receipt_file"):
                continue
            receipt = output.parent / spec["receipt_file"]
            value = portable(json.loads(receipt.read_text(encoding="utf-8")), public_root, output.parent)
            receipt.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    template = (ASSETS / "reader.html").read_text(encoding="utf-8")
    template = template.replace("__PROJECT_MAP_READER_STYLE__", (ASSETS / "reader.css").read_text(encoding="utf-8"))
    template = template.replace("__PROJECT_MAP_CANVAS_INTERACTION__", (ASSETS / "canvas-interaction.js").read_text(encoding="utf-8"))
    template = template.replace("__PROJECT_MAP_HISTORY__", (ASSETS / "reader-history.js").read_text(encoding="utf-8"))
    template = template.replace("/*__PROJECT_MAP_SYSTEM_READER__*/", (ASSETS / "system-reader.js").read_text(encoding="utf-8"))
    template = template.replace("/*__PROJECT_MAP_DEVELOPMENT_HISTORY__*/", (ASSETS / "development-history.js").read_text(encoding="utf-8"))
    rendered = template.replace("__PROJECT_MAP_DATA__", safe_json(payload))
    for name, value in archive_assets.items():
        target = output.parent / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(value, encoding="utf-8")
    for name, value in history_assets.items():
        target = output.parent / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(safe_json(value) + "\n", encoding="utf-8")
    (output.parent / "history-assets.json").write_text(safe_json({"files": sorted([*history_assets, *archive_assets]), "captures": history_captures}) + "\n", encoding="utf-8")
    with tempfile.NamedTemporaryFile("w", suffix=".html", prefix=".reader-", encoding="utf-8", dir=output.parent, delete=False) as handle:
        handle.write(rendered)
        temp = Path(handle.name)
    try:
        os.replace(temp, output)
    finally:
        if temp.exists():
            temp.unlink()
    # This explicit export is human-readable and contains the same original
    # bodies/locators. Normal LLM retrieval still goes through project_map.py.
    (output.parent / "docs.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"output": str(output), "fingerprint": payload.get("fingerprint"), "diagrams": payload["diagrams"], "exported_at": payload["exported_at"]}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path, help="Project manifest (project.yaml)")
    parser.add_argument("--output", type=Path, help="Default: <manifest directory>/views/index.html")
    parser.add_argument("--mode", choices=["a", "b"], default="a")
    parser.add_argument("--node", help="Node executable for the bundled Archify renderer")
    parser.add_argument("--no-diagrams", action="store_true", help="Export documents only")
    parser.add_argument("--public-root", type=Path, help="Publish a static reader within this explicit source root; output directory must be empty. Implies --export-only and omits local session evidence.")
    parser.add_argument("--export-only", action="store_true", help="Only write HTML files; do not start a local HTTP reader")
    args = parser.parse_args(argv)
    try:
        from project_map import load_project
        data = load_project(args.manifest)
        result = export_reader(data, args.output or Path(data["manifest_path"]).parent / "views" / "index.html", args.mode, args.node, not args.no_diagrams, public_root=args.public_root)
        if not args.export_only and args.public_root is None:
            from serve_map import start_reader
            try:
                result["preview"] = start_reader(result["output"])
                result["url"] = result["preview"]["url"]
            except (OSError, ValueError, RuntimeError) as exc:
                result["preview"] = {"status": "failed", "error": str(exc)}
                print(json.dumps(result, ensure_ascii=False, indent=2))
                return 1
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, RuntimeError) as exc:
        print(f"Could not export map: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    raise SystemExit(main())
