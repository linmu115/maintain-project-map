"""Derived human navigation and explicit local-document links, outside LLM reads."""
from __future__ import annotations

from collections import defaultdict
import hashlib
import html
from pathlib import Path
import re
from urllib.parse import unquote, urlencode, urlsplit

from reader_markdown import anchor_id, heading_anchors, heading_slug
from document_archive import is_archived, stub_body


FOLDER_TITLES = {
    "modules": "模块", "module": "模块", "interfaces": "接口", "interface": "接口",
    "integrations": "接入说明", "dependencies": "外部依赖", "adapters": "适配接口",
    "requirements": "需求", "requirement": "需求", "objects": "对象", "object": "对象",
    "implementation": "实际实现", "verification": "验证记录", "decisions": "设计决定",
    "decision": "设计决定", "exploration": "探索", "notes": "说明", "updates": "更新记录", "source-analysis": "源码入口与依赖",
}
TEXT_SUFFIXES = {".md", ".markdown", ".txt", ".rst", ".ts", ".tsx", ".js", ".jsx",
                 ".mjs", ".cjs", ".py", ".json", ".yaml", ".yml", ".toml", ".css",
                 ".html", ".xml", ".sh", ".ps1", ".sql", ".rs", ".go", ".java"}


def build_navigation(data: dict) -> list[dict]:
    """Use real owned directories; bindings stay attached to their source document."""
    base = Path(data["manifest_path"]).resolve().parent / "records"
    root = {"children": [], "folders": {}, "records": []}
    bound = defaultdict(list)
    for record in data.get("records", []):
        path = Path(record["path"]).resolve()
        if record.get("owned") and path.is_relative_to(base):
            cursor, parts = root, path.relative_to(base).parts[:-1]
            for depth, part in enumerate(parts):
                if part not in cursor["folders"]:
                    child = {"key": "/".join(parts[:depth + 1]), "name": part,
                             "children": [], "folders": {}, "records": []}
                    cursor["folders"][part] = child
                    cursor["children"].append(child)
                cursor = cursor["folders"][part]
            cursor["records"].append(record)
        else:
            bound[record.get("source_id") or str(path)].append(record)

    def finish(node):
        entries = node["records"]
        overview = next((r for r in entries if Path(r["path"]).stem.lower() in {"overview", "index", "readme"}), None)
        leaves = [{"record_id": r["id"], "title": "概览" if r is overview else r["title"]}
                  for r in ([overview] if overview else []) + [r for r in entries if r is not overview]]
        children = leaves + [finish(child) for child in node["children"]]
        if "key" not in node:
            return children
        return {"key": "owned/" + node["key"],
                "title": overview["title"] if overview else FOLDER_TITLES.get(node["name"], node["name"]),
                "overview_id": overview["id"] if overview else None, "children": children}

    result = finish(root)
    if bound:
        children = []
        for source, rows in bound.items():
            leaves = [{"record_id": r["id"], "title": r["title"]} for r in rows]
            children.append({"key": "source/" + str(source), "title": Path(rows[0]["path"]).name,
                             "children": leaves} if len(rows) > 1 else leaves[0])
        result.append({"key": "bound", "title": "既有资料", "children": children})
    return result


class LocalDocuments:
    """Resolve records by identity, and snapshot only explicitly referenced sources.

    There is no filesystem HTTP endpoint. Additional documents must be declared
    sources; source-page links never recursively crawl adjacent files.
    """
    def __init__(self, data: dict):
        self.base = Path(data["manifest_path"]).resolve().parent
        self.map_path = Path(data.get("map_path") or self.base / "map.md").resolve()
        self.by_path = defaultdict(list)
        self.by_id, self.names = {}, defaultdict(list)
        self.allowed, self.documents, self.headings = set(), {}, {}
        self.digests = {Path(item["path"]).resolve(): item.get("sha256") for item in data.get("source_files", [])}
        self.allowed.update(self.digests)
        for record in data.get("records", []):
            path = Path(record["path"]).resolve()
            self.by_path[path].append(record)
            self.by_id[record["id"]] = record
            for name in {name.casefold() for name in (record["title"], path.stem, *record.get("aliases", []))}:
                self.names[name].append(record)
            self.allowed.add(path)
            self.headings[record["id"]] = heading_anchors(record.get("body", ""))
            for source in record.get("sources", []):
                value = source.get("path") if isinstance(source, dict) else None
                if value and not urlsplit(value).netloc:
                    root = self.base
                    if source.get("workspace_id"):
                        choices = [w for w in data["project"].get("workspaces", []) if w.get("id") == source["workspace_id"]]
                        if len(choices) != 1: continue
                        root = (self.base / choices[0]["path"]).resolve()
                        if not (root / value).resolve().is_relative_to(root): continue
                    self.allowed.add((root / value).resolve())
        self.map_anchors = heading_anchors(data.get("map_body", ""))

    @staticmethod
    def link(label: str, params: dict, kind: str, identity: str = "", anchor: str = "") -> str:
        if anchor:
            params["anchor"] = anchor
        href = "#" + urlencode(params)
        return ('<a href="' + html.escape(href, quote=True) + '" data-map-' + kind + '="'
                + html.escape(identity, quote=True) + '" data-map-anchor="' + html.escape(anchor, quote=True)
                + '">' + html.escape(label) + '</a>')

    def renderer(self, context_path: str | Path, record_id: str = "", document_id: str = ""):
        context = Path(context_path).resolve()

        def resolve(label, destination, wiki=False):
            if not wiki and destination.startswith("map-node:"):
                kind, separator, node = destination[len("map-node:"):].partition("/")
                if kind in {"architecture", "workflow"} and separator and node.strip():
                    node = unquote(node)
                    href = "#" + urlencode({"mode": "a", "panel": kind, "node": node})
                    return ('<a href="' + html.escape(href, quote=True) + '" data-map-diagram="' + kind
                            + '" data-map-node="' + html.escape(node, quote=True) + '">' + html.escape(label) + '</a>')
                return None
            if wiki:
                name, _, section = destination.partition("#")
                anchor = heading_slug(unquote(section))
                matches = [self.by_id[name]] if name in self.by_id else self.names.get(name.casefold(), [])
                if len(matches) == 1:
                    record = matches[0]
                    return self.link(label, {"mode": "b", "record": record["id"]}, "record", record["id"], anchor)
                if matches:  # An ambiguous title must not pick the first record.
                    return None
                if name and not Path(name).suffix:
                    name += ".md"
                destination = name + ("#" + anchor if section else "")
            try:
                parsed = urlsplit(destination)
            except ValueError:
                return None
            if parsed.netloc or (parsed.scheme and not re.match(r"^[A-Za-z]:[/\\]", destination)) or parsed.query:
                return None
            anchor = unquote(parsed.fragment)
            target = (context.parent / unquote(parsed.path)).resolve() if parsed.path else context
            if target == self.map_path:
                return self.link(label, {"mode": "a", "panel": "spec"}, "home", anchor=anchor)
            candidates = self.by_path.get(target, [])
            if record_id and target == context:
                candidates = [r for r in candidates if r["id"] == record_id]
            owned = [r for r in candidates if r.get("owned")]
            if len(candidates) == 1 and is_archived(candidates[0]):
                return self.link(label, {"mode": "b", "record": candidates[0]["id"]}, "record", candidates[0]["id"])
            matches = [r for r in candidates if anchor and anchor in self.headings[r["id"]]]
            selected = owned[0] if len(owned) == 1 else matches[0] if len(matches) == 1 else None
            if selected:
                return self.link(label, {"mode": "b", "record": selected["id"]}, "record", selected["id"], anchor)
            if target not in self.allowed:
                return None
            identity = "doc-" + hashlib.sha256(str(target).encode()).hexdigest()[:20]
            # Only documents linked by map/record bodies are bundled. Reading a
            # README does not silently export its entire chain of local links.
            if document_id and identity not in self.documents:
                return None
            if identity not in self.documents:
                item = {"id": identity, "path": str(target), "title": target.name,
                        "record_ids": [r["id"] for r in self.by_path.get(target, [])]}
                try:
                    if target.suffix.lower() not in TEXT_SUFFIXES:
                        raise ValueError("此文件类型尚未提供内置阅读。")
                    if target.stat().st_size > 2 * 1024 * 1024:
                        raise ValueError("此资料超过单份阅读快照范围，请按来源位置读取。")
                    raw = target.read_bytes()
                    digest = hashlib.sha256(raw).hexdigest()
                    if self.digests.get(target) and digest != self.digests[target]:
                        raise ValueError("来源在地图加载后发生变化，请重新加载并导出。")
                    body = raw.decode("utf-8-sig")
                    # A shared external document may contain an archived binding.
                    # Never leak its old section through the raw-document view.
                    if any(is_archived(r) for r in candidates):
                        raise ValueError("此原始资料含已归档说明；请按记录 ID 打开当前说明，或显式查看归档原文。")
                    item.update(body=body, source_sha256=digest,
                                format="markdown" if target.suffix.lower() in {".md", ".markdown"} else "code")
                except (OSError, UnicodeError, ValueError) as exc:
                    item["error"] = str(exc)
                self.documents[identity] = item
            return self.link(label, {"mode": "b", "record": record_id, "document": identity}, "document", identity, anchor)

        return resolve

    def render_documents(self, markdown):
        for identity, item in self.documents.items():
            if item.get("error"):
                item["body_html"] = '<p class="empty">' + html.escape(item["error"]) + '</p>'
            elif item["format"] == "markdown":
                item["body_html"] = markdown(item["body"], self.renderer(item["path"], document_id=identity), identity)
            else:
                lines = item["body"].splitlines()
                item["body_html"] = '<pre class="source-code"><code>' + ''.join(
                    '<span class="source-line" data-anchor="L' + str(i) + '" id="' + anchor_id(identity, "L" + str(i))
                    + '"><span class="line-number" aria-hidden="true">' + str(i) + '</span>' + html.escape(line) + '</span>'
                    for i, line in enumerate(lines, 1)) + '</code></pre>'
        return list(self.documents.values())
