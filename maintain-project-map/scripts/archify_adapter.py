"""Embed the pinned native Archify CLI; never reconstruct an authored graph.

Declared JSON is loaded by project_map into a single source snapshot. Native
validation/delivery owns diagram semantics; this adapter owns light styling,
record bindings and explicit delivery receipts. URL brand assets, if authored,
may use the network through upstream Archify. No model call occurs here.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

from canvas_adapter import adapt_canvas

ASSETS = Path(__file__).resolve().parent.parent / "assets"
VENDOR = Path(__file__).resolve().parent.parent / "assets" / "vendor" / "archify"
PIN = "d673e8300df60a5c8166abe78787fdc78f6b8000"
KINDS = ("architecture", "workflow")
EXTENSIONS = (".json", ".native.html", ".html", ".receipt.json")


def find_node(explicit: str | None = None) -> str:
    if explicit:
        candidate = Path(explicit).expanduser()
        if candidate.is_file():
            return str(candidate.resolve())
        located = shutil.which(explicit)
        if located:
            return located
        raise RuntimeError(f"Node executable not found: {explicit}")
    configured = os.environ.get("PROJECT_MAP_NODE")
    if configured:
        return find_node(configured)
    located = shutil.which("node")
    if located:
        return located
    candidates = [Path.home() / ".cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe"]
    for candidate in candidates:
        if candidate.is_file():
            return str(candidate)
    raise RuntimeError("Archify needs Node.js. Install Node or set PROJECT_MAP_NODE to its executable; record reading remains available.")



LIGHT_OVERRIDE = '<style id="project-map-light-theme">\n' + (VENDOR.parent.parent / "diagram-theme.css").read_text(encoding="utf-8") + "\n</style>"


def _style_export(text: str) -> str:
    """Keep vendor files unchanged; apply an explicit fixed-light downstream skin."""
    text = text.replace('data-theme="dark"', 'data-theme="light"', 1)
    text = text.replace("document.documentElement.setAttribute('data-theme', theme);", "document.documentElement.setAttribute('data-theme', 'light');")
    text = text.replace("html.setAttribute('data-theme', theme);", "theme = 'light'; html.setAttribute('data-theme', 'light');")
    return adapt_canvas(text.replace("</head>", LIGHT_OVERRIDE + "\n</head>", 1))



def diagram_targets(directory: Path) -> list[Path]:
    return [Path(directory) / (kind + ext) for kind in KINDS for ext in EXTENSIONS]


def protect_targets(data: dict, targets: list[Path]) -> None:
    sources = [data.get("manifest_path"), data.get("map_path"),
               *[r.get("path") for r in data.get("records", [])],
               *[r.get("path") for r in data.get("source_files", [])],
               *[r.get("source_path") for r in data.get("diagram_sources", {}).values()]]
    protected = {Path(value).resolve() for value in sources if value}
    for target in targets:
        if target.resolve() in protected:
            raise ValueError(f"Export would overwrite a project source: {target}")
        if target.is_symlink() or target.is_dir():
            raise ValueError(f"Export target must be a regular file: {target}")


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _commit_bundle(staging: Path, output_dir: Path, kind: str) -> None:
    # Prepare all bytes before publishing. Roll back our files on a failed
    # replace; a failed graph must not acquire a misleading partial receipt.
    committed = []
    try:
        for ext in EXTENSIONS:
            name = kind + ext
            target = output_dir / name
            previous = target.read_bytes() if target.exists() else None
            os.replace(staging / name, target)
            committed.append((target, previous))
    except OSError:
        for target, previous in reversed(committed):
            if previous is None:
                target.unlink(missing_ok=True)
            else:
                backup = staging / (target.name + ".restore")
                backup.write_bytes(previous)
                os.replace(backup, target)
        raise


def render_diagrams(data: dict, output_dir: Path, node: str | None = None, reader_file: str = "index.html") -> dict:
    output_dir = Path(output_dir).resolve()
    protect_targets(data, diagram_targets(output_dir))
    output_dir.mkdir(parents=True, exist_ok=True)
    specs = {}
    for kind in KINDS:
        if data["project"].get("kind") == "system" and kind == "workflow":
            continue
        source = data.get("diagram_sources", {}).get(kind)
        if source is None:
            specs[kind] = {"file": None, "missing": True,
                           "reason": "尚未登记原生 Archify 图源；可在 project.yaml 的 archify 中关联已有 JSON。"}
            continue
        ir = source.get("ir") or {}
        bindings = source.get("node_records", {})
        collection = ir.get("components" if kind == "architecture" else "nodes", [])
        spec = {"file": None, "canonical_file": None, "source": "native-archify",
                "source_path": source.get("source_path"), "source_sha256": source.get("source_sha256"),
                "title": ir.get("meta", {}).get("title", kind) if isinstance(ir.get("meta", {}), dict) else kind,
                "archify_commit": PIN, "warnings": list(source.get("warnings", [])),
                "errors": list(source.get("errors", [])), "record_nodes": source.get("record_nodes", {}),
                "nodes": [{"id": item["id"], "label": item.get("label", item["id"]),
                           "record_ids": bindings.get(item["id"], [])}
                          for item in collection if isinstance(item, dict) and isinstance(item.get("id"), str)]
                         if isinstance(collection, list) else []}
        specs[kind] = spec
        if spec["errors"] or source.get("ir") is None:
            spec["reason"] = "原生图源不可用，原记录仍可阅读。"
            continue
        try:
            executable = find_node(node)
            raw = source["source_text"].encode("utf-8")
            if _sha(raw) != source.get("source_sha256"):
                raise ValueError("Diagram snapshot does not match its source hash; reload the map.")
            with tempfile.TemporaryDirectory(prefix=".map-archify-", dir=output_dir) as temporary:
                stage = Path(temporary)
                snapshot = stage / (kind + ".json")
                snapshot.write_bytes(raw)
                canonical = stage / (kind + ".native.html")
                command = [executable, str(VENDOR / "bin/archify.mjs"), "deliver", kind,
                           str(snapshot), str(canonical), "--json"]
                if source.get("repo_root") and kind == "architecture":
                    command.extend(["--repo-root", source["repo_root"]])
                environment = dict(os.environ, ARCHIFY_UPDATE_CHECK_DISABLED="1")
                if os.name == "nt":
                    preload = Path(__file__).with_name("hidden-processes.cjs").as_posix()
                    environment["NODE_OPTIONS"] = (environment.get("NODE_OPTIONS", "") + ' --require="' + preload + '"').strip()
                result = subprocess.run(command, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0), capture_output=True, text=True, encoding="utf-8",
                                        errors="replace", timeout=120,
                                        env=environment)
                try:
                    native_receipt = json.loads(result.stdout)
                except ValueError:
                    native_receipt = {}
                if result.returncode or not native_receipt.get("ok") or not canonical.is_file():
                    spec["errors"].extend(native_receipt.get("diagnostics", []))
                    raise RuntimeError(native_receipt.get("error") or (result.stderr or result.stdout or
                                       "Archify did not produce a verified artifact").strip())
                original = canonical.read_bytes()
                if native_receipt.get("artifact", {}).get("sha256") != _sha(original):
                    raise RuntimeError("Archify receipt does not match canonical artifact bytes.")
                if native_receipt.get("specification", {}).get("sha256") != _sha(raw):
                    raise RuntimeError("Archify receipt does not match source snapshot bytes.")
                by_id = {r["id"]: r for r in data.get("records", [])}
                passport = {"reader": reader_file, "diagram": kind, "nodes": {
                    native_id: [{"id": record_id, "title": by_id[record_id]["title"], "status": by_id[record_id].get("status", "current")}
                                for record_id in record_ids if record_id in by_id]
                    for native_id, record_ids in bindings.items()}}
                passport["projects"] = data.get("system_view", {}).get("node_projects", {}) if kind == "architecture" else {}
                encoded = json.dumps(passport, ensure_ascii=False).replace("<", "\\u003c").replace("&", "\\u0026")
                bridge = (ASSETS / "diagram-records.js").read_text(encoding="utf-8")
                extra = ('<script id="project-map-diagram-data" type="application/json">' + encoded + '</script>\n'
                         '<script id="project-map-diagram-records">' + bridge + '</script>\n')
                styled = _style_export(original.decode("utf-8")).replace("</body>", extra + "</body>", 1).encode("utf-8")
                (stage / (kind + ".html")).write_bytes(styled)
                receipt = {"schema": "project-map/archify-delivery/v1", "archify_commit": PIN,
                           "source": {"path": source["source_path"], "sha256": _sha(raw)},
                           "snapshot": kind + ".json", "native_delivery": native_receipt,
                           "canonical": {"file": canonical.name, "sha256": _sha(original),
                                         "validation": "native-deliver"},
                           "embedded": {"file": kind + ".html", "sha256": _sha(styled),
                                        "adaptation": "project-map-passport-navigation-v7", "visual_review": "not-performed"},
                           "note": "Native receipt paths refer to temporary delivery staging; retained files are named above."}
                (stage / (kind + ".receipt.json")).write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
                _commit_bundle(stage, output_dir, kind)
                spec.update(file=kind + ".html", canonical_file=canonical.name,
                            receipt_file=kind + ".receipt.json", validation=native_receipt["validation"])
        except (OSError, RuntimeError, ValueError, subprocess.TimeoutExpired) as exc:
            # Prior artifacts remain on disk for history, never linked as current.
            spec["file"] = None
            spec["canonical_file"] = None
            spec["reason"] = "图未生成，原记录仍可阅读：" + str(exc)
    return specs
