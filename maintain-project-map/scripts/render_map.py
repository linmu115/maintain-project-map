#!/usr/bin/env python3
"""Export one map into an offline human reader. No LLM or web service needed."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import html
import json
import os
from pathlib import Path
import re
import sys
import tempfile
from urllib.parse import urlparse

from archify_adapter import render_diagrams, diagram_targets, protect_targets

ASSETS = Path(__file__).resolve().parent.parent / "assets"


def _inline(text: str) -> str:
    """A small safe Markdown subset: code, emphasis, links. HTML stays text."""
    result = []
    # Parse raw text into independent spans; never re-parse generated markup.
    pattern = re.compile(r"(`[^`]+`|\*\*[^*]+\*\*|\[[^\]]+\]\([^\s)]+\))")
    for span in pattern.split(text):
        if span.startswith("`") and span.endswith("`"):
            result.append("<code>" + html.escape(span[1:-1]) + "</code>")
        elif span.startswith("**") and span.endswith("**"):
            result.append("<strong>" + html.escape(span[2:-2]) + "</strong>")
        elif span.startswith("[") and "](" in span:
            label, destination = span[1:-1].split("](", 1)
            parsed = urlparse(destination)
            # File/relative references are visible locators, not web-server paths.
            if parsed.scheme.lower() in {"https", "http"} and parsed.netloc:
                result.append('<a href="' + html.escape(destination, quote=True) + '" target="_blank" rel="noopener noreferrer">' + html.escape(label) + "</a>")
            else:
                result.append(html.escape(label) + " <code>" + html.escape(destination) + "</code>")
        else:
            result.append(html.escape(span))
    return "".join(result)


def markdown_html(source: str) -> str:
    """Render headings, lists, quotes, tables and fenced code without raw HTML."""
    lines = str(source).splitlines()
    output, paragraph = [], []
    in_code, code, list_type = False, [], None

    def flush_paragraph():
        if paragraph:
            output.append("<p>" + _inline(" ".join(paragraph)) + "</p>")
            paragraph.clear()

    def close_list():
        nonlocal list_type
        if list_type:
            output.append(f"</{list_type}>")
            list_type = None

    i = 0
    while i < len(lines):
        line = lines[i]
        if line.lstrip().startswith("```"):
            flush_paragraph(); close_list()
            if in_code:
                output.append("<pre><code>" + html.escape("\n".join(code)) + "</code></pre>")
                code = []
            in_code = not in_code
        elif in_code:
            code.append(line)
        elif not line.strip():
            flush_paragraph(); close_list()
        elif re.match(r"^#{1,6}\s", line):
            flush_paragraph(); close_list()
            level, title = line.split(" ", 1)
            # Document h1 is a section inside the product page.
            n = min(6, len(level) + 1)
            output.append(f"<h{n}>" + _inline(title) + f"</h{n}>")
        elif "|" in line and i + 1 < len(lines) and re.match(r"^\s*\|?\s*:?-{3,}", lines[i + 1]):
            flush_paragraph(); close_list()
            cells = lambda row: [part.strip() for part in row.strip().strip("|").split("|")]
            output.append("<table><thead><tr>" + "".join("<th>" + _inline(c) + "</th>" for c in cells(line)) + "</tr></thead><tbody>")
            i += 2
            while i < len(lines) and "|" in lines[i] and lines[i].strip():
                output.append("<tr>" + "".join("<td>" + _inline(c) + "</td>" for c in cells(lines[i])) + "</tr>")
                i += 1
            output.append("</tbody></table>")
            continue
        elif (match := re.match(r"^\s*([-*+]\s+|\d+\.\s+)(.+)$", line)):
            flush_paragraph()
            kind = "ol" if match.group(1)[0].isdigit() else "ul"
            if list_type != kind:
                close_list(); output.append(f"<{kind}>"); list_type = kind
            output.append("<li>" + _inline(match.group(2)) + "</li>")
        elif line.startswith("> "):
            flush_paragraph(); close_list()
            output.append("<blockquote>" + _inline(line[2:]) + "</blockquote>")
        else:
            close_list(); paragraph.append(line)
        i += 1
    flush_paragraph(); close_list()
    if in_code:
        output.append("<pre><code>" + html.escape("\n".join(code)) + "</code></pre>")
    return "\n".join(output)


def safe_json(data: dict) -> str:
    return json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")


def export_reader(data: dict, output: Path, mode: str = "a", node: str | None = None, diagrams: bool = True) -> dict:
    output = Path(output).resolve()
    if output.suffix.lower() != ".html":
        raise ValueError("Reader output must have an .html extension.")
    if output.name.lower() in {p.name for p in diagram_targets(output.parent)}:
        raise ValueError("Reader output cannot use a reserved diagram filename.")
    if mode not in {"a", "b", "c"}:
        raise ValueError("Reader mode must be a, b or c.")
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
    payload["map_html"] = markdown_html(data.get("map_body", ""))
    payload["records"] = []
    for record in data.get("records", []):
        item = {**record, "body_html": markdown_html(record.get("body", ""))}
        # Source bytes and fingerprint must come from the same load snapshot.
        # A table binding can project fields into body while source_text retains
        # its original row. Do not read the path again after load_project.
        if "source_text" not in record:
            item["source_text"] = record.get("body", "")
            item["source_note"] = "此快照未提供原文摘录；此处保留加载时的正文。"
        payload["records"].append(item)
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
    parser.add_argument("--mode", choices=["a", "b", "c"], default="a")
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
