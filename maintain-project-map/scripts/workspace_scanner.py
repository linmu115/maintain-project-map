"""Incremental static evidence from explicitly bound Git worktrees."""
from __future__ import annotations

from collections import defaultdict
import fnmatch
import json
import os
from pathlib import Path
import subprocess

from code_parsers import SUFFIXES, VERSION, parse_source, sha


EXCLUDED = {".git", "node_modules", "vendor", ".venv", "venv", "__pycache__", "dist", "build", "target", "coverage", ".project-map-cache", ".pytest_cache", "views"}
MAX_BYTES = 2 * 1024 * 1024


def git(root, *args):
    proc = subprocess.run(["git", "-C", str(root), *args], capture_output=True, timeout=30,
                          creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    if proc.returncode:
        raise ValueError(proc.stderr.decode("utf-8", errors="replace").strip() or "Git command failed")
    return proc.stdout.decode("utf-8", errors="surrogateescape")


def workspace(doc, wid):
    choices = [w for w in doc["project"].get("workspaces", []) if isinstance(w, dict) and w.get("id") == wid]
    if len(choices) != 1 or not choices[0].get("path"):
        raise ValueError(f"Workspace {wid!r} needs exactly one explicit path binding")
    binding = choices[0]
    root = (Path(doc["manifest_path"]).parent / binding["path"]).resolve()
    top = Path(git(root, "rev-parse", "--show-toplevel").strip()).resolve()
    if root != top:
        raise ValueError(f"Workspace {wid!r} must bind the Git worktree root explicitly: {top}")
    return root, binding


def scan_files(doc, wid, previous=None):
    root, binding = workspace(doc, wid)
    previous = previous or {}
    names = sorted(set(n for n in git(root, "ls-files", "--cached", "--others", "--exclude-standard", "-z").split("\0") if n))
    base = Path(doc["manifest_path"]).parent.resolve()
    candidates, skipped = [], []
    for name in names:
        path = root / name
        if any(part in EXCLUDED for part in Path(name).parts) or any(fnmatch.fnmatchcase(name, pattern) for pattern in binding.get("exclude", [])):
            skipped.append({"path": name, "reason": "excluded"}); continue
        if path.resolve().is_relative_to(base):
            skipped.append({"path": name, "reason": "map_documents"}); continue
        if not path.resolve().is_relative_to(root) or path.is_symlink():
            skipped.append({"path": name, "reason": "symlink_or_outside_workspace"}); continue
        if path.suffix.lower() not in SUFFIXES and path.name not in {"package.json", "pyproject.toml"}:
            skipped.append({"path": name, "reason": "unsupported_file_type"}); continue
        candidates.append(name)
    if len(candidates) > 3000:
        raise ValueError("Source scan exceeds 3000 files; narrow workspace.exclude before scanning")
    files, parsed_count, reused_count = {}, 0, 0
    for name in candidates:
        path = root / name
        if not path.is_file():
            skipped.append({"path": name, "reason": "missing_in_worktree"}); continue
        if path.stat().st_size > MAX_BYTES:
            skipped.append({"path": name, "reason": "size_limit"}); continue
        raw = path.read_bytes()
        digest = sha(raw)
        cached = previous.get("files", {}).get(name, {})
        if cached.get("sha256") == digest and previous.get("parser_version") == VERSION and not any(x["reason"] == "parser_unavailable" for x in cached.get("limitations", [])):
            files[name] = cached; reused_count += 1; continue
        if path.suffix.lower() in SUFFIXES:
            parsed = parse_source(name, raw)
        else:
            parsed = {"language": "manifest", "symbols": [], "imports": [], "calls": [], "entries": [], "limitations": []}
            try:
                if path.name == "package.json":
                    obj = json.loads(raw)
                    for field in ("main", "module", "bin", "exports", "scripts"):
                        def visit(value, pointer):
                            if isinstance(value, str): parsed["entries"].append({"kind": "npm_script" if field == "scripts" else "package_entry", "declaration": pointer, "target": value})
                            elif isinstance(value, dict):
                                for key, child in value.items(): visit(child, pointer + "/" + str(key).replace("~", "~0").replace("/", "~1"))
                            elif isinstance(value, list):
                                for index, child in enumerate(value): visit(child, pointer + "/" + str(index))
                        visit(obj.get(field), "#/" + field)
                else:
                    try: import tomllib
                    except ImportError: import tomli as tomllib
                    obj = tomllib.loads(raw.decode("utf-8-sig"))
                    for field in ("scripts", "gui-scripts"):
                        for key, target in obj.get("project", {}).get(field, {}).items():
                            parsed["entries"].append({"kind": "python_package_entry", "declaration": f"project.{field}.{key}", "target": target})
            except (ValueError, UnicodeError, ImportError) as exc:
                parsed["limitations"].append({"reason": "manifest_parse_failed", "detail": str(exc)[:200]})
        files[name] = {"sha256": digest, **parsed}; parsed_count += 1
    try: head = git(root, "rev-parse", "HEAD").strip()
    except ValueError: head = None
    try: branch = git(root, "symbolic-ref", "--short", "HEAD").strip()
    except ValueError: branch = None
    state = {"workspace_id": wid, "root": str(root), "head": head, "branch": branch,
             "dirty": bool(git(root, "status", "--porcelain", "--untracked-files=normal")), "parser_version": VERSION,
             "files": files, "skipped": skipped, "binding": binding,
             "counts": {"listed": len(names), "scanned": len(files), "parsed": parsed_count, "reused": reused_count, "skipped": len(skipped)}}
    state.update(resolve_evidence(root, binding, files, set(names)))
    state["fingerprint"] = sha(json.dumps({"files": {p: f["sha256"] for p, f in files.items()}, "binding": binding, "skipped": skipped, "parser_version": VERSION}, sort_keys=True))
    return state


def resolve_evidence(root, binding, files, known):
    modules = defaultdict(set)
    file_modules = defaultdict(list)
    roots = binding.get("python_roots", [".", "src"])
    for value in roots:
        prefix = (root / value).resolve()
        if not prefix.is_relative_to(root): raise ValueError("python_roots must stay inside the bound workspace")
        for name in files:
            p = root / name
            if p.suffix not in {".py", ".pyi"} or not p.is_relative_to(prefix): continue
            parts = list(p.relative_to(prefix).with_suffix("").parts)
            if parts[-1] == "__init__": parts.pop()
            if not parts or not all(part.isidentifier() for part in parts): continue
            module = ".".join(parts)
            modules[module].add(name); file_modules[name].append(module)

    def py_target(module):
        hits = sorted(modules.get(module, []))
        return hits[0] if len(hits) == 1 else None

    def js_target(name, spec, html=False):
        if not (spec.startswith(".") or html and not ":" in spec and not spec.startswith("/")):
            return None
        candidate = (root / name).parent / spec
        candidates = [candidate, *(Path(str(candidate) + ext) for ext in (".js", ".ts", ".tsx", ".jsx", ".mjs", ".cjs", ".json")), *(candidate / ("index" + ext) for ext in (".js", ".ts", ".tsx", ".jsx"))]
        if candidate.suffix == ".js": candidates.extend([candidate.with_suffix(".ts"), candidate.with_suffix(".tsx")])
        for p in candidates:
            resolved = p.resolve()
            if resolved.is_relative_to(root):
                rel = resolved.relative_to(root).as_posix()
                if rel in known and p.is_file() and not p.is_symlink(): return rel
        return None

    dependencies, calls, entries, symbols = [], [], [], []
    for name, parsed in files.items():
        aliases = []
        python = parsed["language"] == "python"
        for imp in parsed["imports"]:
            module, target_symbol = imp["module"], imp.get("name", "")
            if python:
                if imp.get("level"):
                    names = sorted(file_modules[name], key=len)
                    parts = (names[0].split(".") if names else [])
                    if Path(name).stem != "__init__": parts = parts[:-1]
                    up = imp["level"] - 1
                    parts = parts[:-up] if up else parts
                    module = ".".join([*parts, *module.split(".")]) if module else ".".join(parts)
                child = py_target(module + "." + target_symbol) if target_symbol and target_symbol != "*" else None
                target = child or py_target(module)
                if child: target_symbol = ""
                if imp.get("alias"): aliases.append((imp.get("scope", ""), imp["alias"], target, target_symbol))
            else:
                target = js_target(name, module, imp.get("kind") == "html_script")
                for b in imp.get("bindings", []): aliases.append((imp.get("scope", ""), b["alias"], target, "" if b["name"] == "*" else b["name"]))
            status = "local" if target else "unresolved_local" if imp.get("level") or module.startswith(".") else "external_or_unresolved"
            dependencies.append({"path": name, "line": imp["line"], "kind": "import", "target": module,
                                 "target_path": target, "target_symbol": target_symbol or None, "resolution": status,
                                 **({"dynamic": True} if imp.get("dynamic") else {})})
        for symbol in parsed["symbols"]: symbols.append({"path": name, **symbol})
        for call in parsed["calls"]:
            target_path, target_symbol = None, None
            root_name, _, tail = call["target"].partition(".")
            eligible = [(scope, alias, p, symbol) for scope, alias, p, symbol in aliases if (call["target"] == alias or call["target"].startswith(alias + ".")) and (not scope or call["caller"] == scope or call["caller"].startswith(scope + "."))]
            if eligible:
                scope, alias, target_path, symbol = max(eligible, key=lambda item: (len(item[0]), len(item[1])))
                tail = call["target"][len(alias):].lstrip(".")
                target_symbol = ".".join(s for s in (symbol, tail) if s)
            else:
                scope_parts = call["caller"].split(".")[:-1]
                possible = [".".join([*scope_parts[:i], call["target"]]) for i in range(len(scope_parts), -1, -1)]
                matched = next((s for s in possible if any(x["name"] == s for x in parsed["symbols"])), None)
                if matched: target_path, target_symbol = name, matched
            calls.append({"path": name, **call, "target_path": target_path, "target_symbol": target_symbol,
                          "resolution": "static_reference" if target_path else "unresolved_dynamic_or_external"})
        for entry in parsed["entries"]:
            target_path, target_symbol = name, entry.get("symbol")
            if entry["kind"] == "python_package_entry":
                module, _, target_symbol = str(entry["target"]).partition(":")
                target_path = py_target(module)
            elif entry["kind"] == "package_entry": target_path = js_target(name, entry["target"], True)
            elif entry["kind"] == "npm_script": target_path = None
            entries.append({"path": name, **entry, "target_path": target_path, "target_symbol": target_symbol})
    return {"dependencies": dependencies, "calls": calls, "entries": entries, "symbols": symbols}
