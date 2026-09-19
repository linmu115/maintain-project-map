"""Bound source discovery, map registration gaps and explicit review baselines."""
from __future__ import annotations

import copy
from datetime import datetime, timezone
import json
import os
from pathlib import Path

from code_parsers import sha, symbol_fingerprint
from document_archive import is_archived
from workspace_scanner import MAX_BYTES, git, scan_files, workspace


def cache_path(doc, wid):
    home = Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex")))
    root = Path(os.environ.get("PROJECT_MAP_SOURCE_CACHE", str(home / "project-maps/source")))
    identity = [os.path.normcase(str(Path(doc["manifest_path"]).resolve())), doc["project"]["project_id"], wid]
    return root / (sha(json.dumps(identity)) + ".json")


def cached_state(doc, wid):
    try: return json.loads(cache_path(doc, wid).read_text(encoding="utf-8"))
    except (OSError, ValueError): return {}


def declared_paths(doc, record, wid, root):
    result = []
    for index, source in enumerate(record.get("sources", [])):
        if not isinstance(source, dict) or not source.get("path") or source.get("workspace_id") not in {None, wid}: continue
        base = root if source.get("workspace_id") else Path(doc["manifest_path"]).parent
        candidate = (base / source["path"]).resolve()
        if candidate.is_relative_to(root): result.append((index, candidate.relative_to(root).as_posix()))
    return result


def file_hash(root, name):
    try:
        path = (root / name).resolve()
        if not path.is_relative_to(root) or not path.is_file() or path.stat().st_size > MAX_BYTES: return None
        return sha(path.read_bytes())
    except OSError: return None


def associate(doc, state, previous):
    from system_map import module_records
    from source_locations import resolve_sources
    root, wid = Path(state["root"]), state["workspace_id"]
    _, modules = module_records(doc)
    records = [r for r in doc["records"] if not is_archived(r)]
    by_file, baselines, reviews = {}, {}, []
    old = previous.get("observed_baselines", {}) if previous.get("root") == str(root) else {}
    for record in records:
        paths = [p for _, p in declared_paths(doc, record, wid, root)]
        for path in paths: by_file.setdefault(path, []).append(record["id"])
        if not paths: continue
        dependencies = {d["target_path"] for d in state["dependencies"] if d["path"] in paths and d["target_path"]}
        tracked = {p: state["files"][p]["sha256"] for p in set(paths) | dependencies if p in state["files"]}
        review_stamp = record.get("source_review", {}).get("reviewed_at")
        earlier = old.get(record["id"], {})
        baseline = earlier if earlier.get("reviewed_at") == review_stamp and earlier.get("files") else {"files": tracked, "reviewed_at": review_stamp}
        baselines[record["id"]] = baseline
        # Unreviewed observations can detect change, but never certify correctness.
        changes = [{"workspace_id": wid, "path": p, "reason": "source_changed" if p in paths else "dependency_changed"}
                   for p, digest in baseline["files"].items() if state["files"].get(p, {}).get("sha256") != digest]
        declared = resolve_sources(doc, record, limit=len(record.get("sources", [])))
        for source in declared["resolved_sources"]:
            if source.get("review") == "needs_review":
                changes.append({"workspace_id": source.get("workspace_id"), "path": source.get("path"), "symbol": source.get("symbol"), "reason": source.get("review_reason", "declared_baseline_changed")})
        if changes: reviews.append({"record_id": record["id"], "title": record["title"], "module_id": modules.get(record["id"]), "state": "needs_review", "changes": changes})
    pairs = {(r["from"].get("record_id"), r["to"].get("record_id")) for r in doc["relations"] if r["to"].get("project_id") == doc["project"]["project_id"]}
    gaps, relation_gaps = [], {}
    for name, parsed in state["files"].items():
        if name not in by_file and (parsed["symbols"] or parsed["entries"]): gaps.append({"kind": "unmapped_file", "path": name})
    for dep in state["dependencies"]:
        source_ids, target_ids = by_file.get(dep["path"], []), by_file.get(dep["target_path"], [])
        dep.update(record_ids=source_ids, target_record_ids=target_ids)
        if dep["target_path"] and source_ids and target_ids and not set(source_ids) & set(target_ids) and not any((a, b) in pairs for a in source_ids for b in target_ids):
            key = (dep["path"], dep["target_path"])
            if key not in relation_gaps:
                relation_gaps[key] = {**{k: v for k, v in dep.items() if k not in {"line", "target_symbol"}}, "kind": "unregistered_relation", "occurrences": 0, "sample_lines": []}
            gap = relation_gaps[key]
            gap["occurrences"] += 1
            if dep["line"] not in gap["sample_lines"] and len(gap["sample_lines"]) < 5:
                gap["sample_lines"].append(dep["line"])
    for key in ("entries", "calls", "symbols"):
        for item in state[key]: item["record_ids"] = by_file.get(item["path"], [])
    state.update(observed_baselines=baselines, reviews=reviews, gaps=gaps + list(relation_gaps.values()))
    return state


def source_health(doc, record):
    """Small live warning; existing sources separately expose exact baseline details."""
    if is_archived(record): return None
    from source_locations import resolve_sources
    resolved = resolve_sources(doc, record, limit=len(record.get("sources", [])))
    changes = []
    for item in resolved["resolved_sources"]:
        if item.get("review") == "needs_review":
            changes.append({k: item[k] for k in ("workspace_id", "path", "symbol", "review_reason", "changed_dependencies") if k in item})
    for binding in doc["project"].get("workspaces", []):
        if not isinstance(binding, dict): continue
        wid = binding.get("id")
        if not wid: continue
        root = (Path(doc["manifest_path"]).parent / binding.get("path", "")).resolve()
        state = cached_state(doc, wid)
        baseline = state.get("observed_baselines", {}).get(record["id"], {})
        if state.get("root") != str(root) or baseline.get("reviewed_at") != record.get("source_review", {}).get("reviewed_at"): continue
        for name, expected in baseline.get("files", {}).items():
            if file_hash(root, name) != expected:
                changes.append({"workspace_id": wid, "path": name, "review_reason": "changed_since_source_observation"})
    if changes:
        unique = list({json.dumps(c, sort_keys=True): c for c in changes}.values())
        return {"state": "needs_review", "changes": unique[:8], "total": len(unique), "notice": "源码或已发现依赖变化，尚未判定说明失效；核对后更新基线或归档说明。"}
    return None


def write_report(doc, states):
    from project_map import _registry_writer_lock
    with _registry_writer_lock(Path(doc["manifest_path"])):
        return _write_report(doc, states)


def _write_report(doc, states):
    from project_map import _atomic_write, _frontmatter
    path = Path(doc["manifest_path"]).parent / "records/source-analysis/overview.md"
    if not path.resolve().is_relative_to(Path(doc["manifest_path"]).parent.resolve() / "records"):
        raise ValueError("Source report escapes the map records directory")
    if path.exists():
        meta, _, _ = _frontmatter(path.read_text(encoding="utf-8-sig"), str(path))
        if meta.get("generated_by") != "project-map-source" or is_archived(meta): raise ValueError("Source report path belongs to a user or archived document; refusing to overwrite")
    body = ["# 源码入口与依赖", "", "这里是绑定工作区的静态扫描结果。用于补查入口、依赖和说明缺口；未登记不代表架构错误，静态引用不等于运行时调用。", "", "LLM 阅读入口：`project_map.py source <地图> --kind entrypoint|dependency|call|symbol|gap|review --query <名称或路径>`。结果支持分页，不必加载全量源码。", ""]
    for state in states:
        wid = state["workspace_id"]
        body.extend(["## 工作区 " + wid, "", f"分支 `{state.get('branch')}`，提交 `{state.get('head') or '尚无提交'}`；扫描 {len(state['files'])} 个文件。内容指纹 `{state['fingerprint'][:16]}`。", "", "### 入口", ""])
        for item in state["entries"][:16]: body.append(f"- `{item['path']}` {item.get('line', item.get('declaration', ''))}：{item['kind']} → `{item.get('target_path') or item.get('target') or item.get('symbol')}`")
        if not state["entries"]: body.append("未发现当前解析器支持的显式入口；这不证明项目没有入口。")
        body.extend(["", "### 依赖与待补登记", "", f"提取 {len(state['dependencies'])} 项导入、{len(state['calls'])} 条静态调用/继承线索；待核对登记缺口 {len(state['gaps'])} 项。"])
        local = {}
        for dependency in state["dependencies"]:
            if dependency["target_path"]: local.setdefault((dependency["path"], dependency["target_path"]), dependency)
        local = list(local.values())
        for item in local[:12]: body.append(f"- `{item['path']}:{item['line']}` → `{item['target_path']}`")
        body.extend(["", "### 待复核说明", ""])
        for item in state["reviews"][:16]:
            changed = "、".join(str(c.get("path")) for c in item["changes"][:4])
            body.append(f"- [[{item['record_id']}|{item['title']}]]：{changed}")
        if not state["reviews"]: body.append("本次没有发现相对既有基线的变化；尚无人工核对基线的说明不因此视为有效。")
        errors = sum(len(f["limitations"]) for f in state["files"].values())
        body.extend(["", "### 覆盖范围", "", f"排除或不支持的文件 {len(state['skipped'])} 项，解析限制 {errors} 项。仅扫描当前 Git 工作区，包含未忽略的新文件；不进入子仓库、依赖包或默认排除目录。动态调用、反射、路径别名及未支持语言需另行核对。完整清单通过 `--kind coverage` 查询。", ""])
    metadata = {"id": "SRC-source-inventory", "kind": "note", "title": "源码入口与依赖", "status": "current", "generated_by": "project-map-source", "summary": "绑定 Git 工作区的入口、静态依赖、待补登记与待复核说明；供人和 LLM 按需查阅。"}
    text = "---\n" + json.dumps(metadata, ensure_ascii=False, indent=2) + "\n---\n" + "\n".join(body)
    if not path.exists() or path.read_text(encoding="utf-8") != text:
        path.parent.mkdir(parents=True, exist_ok=True); _atomic_write(path, text)
    return str(path)


def source_query(manifest, wid=None, kind="summary", query="", limit=12, offset=0):
    from project_map import load_project, _atomic_write, _registry_writer_lock
    if limit < 1 or limit > 100 or offset < 0: raise ValueError("Source queries allow limit 1..100 and nonnegative offset")
    doc = load_project(manifest)
    ids = [w["id"] for w in doc["project"].get("workspaces", []) if isinstance(w, dict) and w.get("id")]
    if not ids: raise ValueError("No source workspace is bound; use bind-workspace with the actual Git worktree root")
    if len(ids) != len(set(ids)): raise ValueError("Duplicate source workspace IDs")
    if wid and wid not in ids: raise ValueError("Unknown source workspace ID")
    selected = [wid] if wid else ids
    states = []
    for item in selected:
        path = cache_path(doc, item)
        with _registry_writer_lock(path):
            previous = cached_state(doc, item)
            state = associate(doc, scan_files(doc, item, previous), previous)
            _atomic_write(path, json.dumps(state, ensure_ascii=False, indent=2))
        states.append(state)
    # A scoped refresh preserves the other workspaces' last explicit scan.
    display = [next((s for s in states if s["workspace_id"] == item), None) or cached_state(doc, item) for item in ids]
    report = write_report(doc, [s for s in display if s.get("files") is not None])
    rows = []
    keys = {"entrypoint": "entries", "dependency": "dependencies", "call": "calls", "symbol": "symbols", "gap": "gaps", "review": "reviews"}
    for state in states:
        if kind == "summary":
            rows.append({"workspace_id": state["workspace_id"], "root": state["root"], "branch": state["branch"], "head": state["head"], "dirty": state["dirty"], "counts": state["counts"], "entrypoints": len(state["entries"]), "dependencies": len(state["dependencies"]), "registration_gaps": len(state["gaps"]), "needs_review": len(state["reviews"])})
        elif kind == "coverage":
            rows.extend({"workspace_id": state["workspace_id"], **item} for item in state["skipped"])
            rows.extend({"workspace_id": state["workspace_id"], "path": name, **item} for name, value in state["files"].items() for item in value["limitations"])
        else:
            rows.extend({"workspace_id": state["workspace_id"], **{k: v for k, v in item.items() if k != "sha256"}} for item in state[keys[kind]])
    words = query.casefold().split()
    rows = [r for r in rows if all(word in json.dumps(r, ensure_ascii=False).casefold() for word in words)]
    end = offset + limit
    return {"project_id": doc["project"]["project_id"], "kind": kind, "results": rows[offset:end], "total": len(rows), "next_offset": end if end < len(rows) else None, "report": report,
            "coverage": "Static evidence from explicitly bound worktrees; unresolved calls and registration gaps need inspection, not automatic architecture claims."}


def bind_workspace(manifest, wid, root, python_roots=None, exclude=None):
    from project_map import load_project, manifest_file, _atomic_write, _registry_writer_lock
    if not wid.strip(): raise ValueError("Workspace ID must be nonempty")
    root = Path(root).expanduser().resolve()
    if Path(git(root, "rev-parse", "--show-toplevel").strip()).resolve() != root: raise ValueError("Bind the exact Git worktree root")
    manifest = manifest_file(manifest)
    with _registry_writer_lock(manifest):
        doc = load_project(manifest); project = copy.deepcopy(doc["project"])
        rows = project.setdefault("workspaces", [])
        hits = [w for w in rows if w.get("id") == wid]
        if len(hits) > 1: raise ValueError("Duplicate workspace ID")
        value = copy.deepcopy(hits[0]) if hits else {"id": wid}
        try: value["path"] = Path(os.path.relpath(root, manifest.parent)).as_posix()
        except ValueError: value["path"] = str(root)
        if python_roots is not None: value["python_roots"] = python_roots
        if exclude is not None: value["exclude"] = exclude
        for p in value.get("python_roots", []):
            if not (root / p).resolve().is_relative_to(root): raise ValueError("Python roots must stay inside the worktree")
        project["workspaces"] = [value if w.get("id") == wid else w for w in rows] if hits else [*rows, value]
        if project != doc["project"]: _atomic_write(manifest, json.dumps(project, ensure_ascii=False, indent=2) + "\n")
    return {"workspace": value, "git_root": str(root), "changed": project != doc["project"]}


def review_record_sources(manifest, rid, reason):
    from project_map import load_project, _find, _frontmatter, _atomic_write, manifest_file, _registry_writer_lock
    if not reason.strip(): raise ValueError("Review needs a reason explaining the checked correspondence")
    source_query(manifest)
    manifest = manifest_file(manifest)
    with _registry_writer_lock(manifest):
        doc = load_project(manifest); record = _find(doc, rid)
        if is_archived(record): raise ValueError("An archived explanation cannot be marked current by source review")
        if record["owned"]:
            path = Path(record["path"]); before = path.read_bytes(); meta, body, _ = _frontmatter(before.decode("utf-8-sig"), str(path))
        else:
            path = manifest; before = path.read_bytes(); meta = next(copy.deepcopy(b) for b in doc["project"]["bindings"] if b["id"] == rid); body = None
        checked = 0
        for binding in doc["project"].get("workspaces", []):
            root, _ = workspace(doc, binding["id"]); state = cached_state(doc, binding["id"])
            for index, name in declared_paths(doc, record, binding["id"], root):
                digest = file_hash(root, name)
                if not digest: raise ValueError("Cannot review missing, outside or oversized source: " + name)
                if name in state["files"] and state["files"][name]["sha256"] != digest:
                    raise ValueError("Source changed during review; inspect the new version: " + name)
                source = meta["sources"][index]
                source["workspace_id"], source["path"], source["reviewed_sha256"] = binding["id"], name, digest
                if source.get("symbol"):
                    symbol = symbol_fingerprint(root / name, source["symbol"])
                    if symbol["status"] != "found": raise ValueError("Declared symbol was not uniquely found: " + source["symbol"])
                    source["reviewed_symbol_sha256"] = symbol["sha256"]
                targets = sorted({d["target_path"] for d in state.get("dependencies", []) if d["path"] == name and d["target_path"] and d["target_path"] != name})
                dependencies = []
                for target in targets:
                    value = file_hash(root, target)
                    if not value: raise ValueError("Cannot baseline discovered dependency: " + target)
                    if target in state["files"] and state["files"][target]["sha256"] != value:
                        raise ValueError("Dependency changed during review: " + target)
                    dependencies.append({"path": target, "sha256": value})
                source["reviewed_dependencies"] = dependencies
                checked += 1
        if not checked: raise ValueError("This record has no source inside an explicitly bound workspace")
        meta["source_review"] = {"reviewed_at": datetime.now(timezone.utc).isoformat(), "reason": reason, "body_sha256": sha(record["body"])}
        if record["owned"]: text = "---\n" + json.dumps(meta, ensure_ascii=False, indent=2) + "\n---\n" + body
        else:
            project = copy.deepcopy(doc["project"]); project["bindings"] = [meta if b["id"] == rid else b for b in project["bindings"]]
            text = json.dumps(project, ensure_ascii=False, indent=2) + "\n"
        if path.read_bytes() != before: raise ValueError("Record changed during review")
        _atomic_write(path, text)
    source_query(manifest)
    return {"record_id": rid, "checked_sources": checked, "source_review": meta["source_review"], "feature_status_changed": False}
