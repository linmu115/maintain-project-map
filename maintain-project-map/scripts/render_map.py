#!/usr/bin/env python3
"""Export one map into an offline human reader. No LLM or web service needed."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys
import tempfile

from archify_adapter import render_diagrams, diagram_targets, protect_targets
from reader_content import LocalDocuments, build_navigation
from reader_markdown import markdown_html
from project_map import normalize_relations

ASSETS = Path(__file__).resolve().parent.parent / "assets"


def safe_json(data: dict) -> str:
    return json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")


def export_reader(data: dict, output: Path, mode: str = "a", node: str | None = None, diagrams: bool = True) -> dict:
    output = Path(output).resolve()
    if output.suffix.lower() != ".html":
        raise ValueError("Reader output must have an .html extension.")
    if output.name.lower() in {p.name for p in diagram_targets(output.parent)}:
        raise ValueError("Reader output cannot use a reserved diagram filename.")
    if mode not in {"a", "b"}:
        raise ValueError("Reader mode must be a or b.")
    targets = [output, output.parent / "docs.json"]
    if diagrams:
        targets.extend(diagram_targets(output.parent))
    protect_targets(data, targets)
    output.parent.mkdir(parents=True, exist_ok=True)
    payload = dict(data)
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
        item = {**record, "body_html": markdown_html(record.get("body", ""), links.renderer(record["path"], record["id"]), record["id"])}
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
        payload["diagrams"] = render_diagrams(data, output.parent, node=node)
    else:
        payload["diagrams"] = {kind: {"file": None, "reason": "本次仅导出了阅读文档。"} for kind in ("architecture", "workflow")}
    template = (ASSETS / "reader.html").read_text(encoding="utf-8")
    template = template.replace("__PROJECT_MAP_READER_STYLE__", (ASSETS / "reader.css").read_text(encoding="utf-8"))
    template = template.replace("__PROJECT_MAP_CANVAS_INTERACTION__", (ASSETS / "canvas-interaction.js").read_text(encoding="utf-8"))
    rendered = template.replace("__PROJECT_MAP_DATA__", safe_json(payload))
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
    parser.add_argument("--export-only", action="store_true", help="Only write HTML files; do not start a local HTTP reader")
    args = parser.parse_args(argv)
    try:
        from project_map import load_project
        data = load_project(args.manifest)
        result = export_reader(data, args.output or Path(data["manifest_path"]).parent / "views" / "index.html", args.mode, args.node, not args.no_diagrams)
        if not args.export_only:
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
