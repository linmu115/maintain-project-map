"""Portable metadata and an explicit filesystem boundary for static publication."""
from __future__ import annotations

from pathlib import Path, PureWindowsPath

from reader_content import LocalDocuments


def check_public_scope(data: dict, output: Path, root: Path) -> None:
    if not root.is_dir():
        raise ValueError("Public root must be an existing directory.")
    if output.parent.exists() and any(output.parent.iterdir()):
        raise ValueError("Public export requires an empty output directory; choose a new directory.")
    if data["project"].get("kind") == "system":
        raise ValueError("System-map project launching requires the local reader; publish individual project maps.")
    links = LocalDocuments(data)
    paths = {Path(data["manifest_path"]), links.map_path, *links.allowed}
    paths.update(Path(s["source_path"]) for s in data.get("diagram_sources", {}).values())
    for path in paths:
        if not path.resolve().is_relative_to(root):
            raise ValueError("Public source is outside the declared root: " + str(path))


def portable(value, root: Path, output: Path):
    """Keep repository-relative locators; remove machine-only metadata paths.

    This is not a secret scanner. Authored documents within the public root must
    already be suitable for publication. It only normalizes generated metadata.
    """
    if isinstance(value, dict):
        return {key: portable(item, root, output) for key, item in value.items()}
    if isinstance(value, list):
        return [portable(item, root, output) for item in value]
    if not isinstance(value, str):
        return value
    # Long bodies can contain a generated source locator, so handle both native
    # and slash-separated forms without rewriting their Markdown syntax.
    for base, prefix in ((output, "site"), (root, "repository")):
        for spelling in {str(base), base.as_posix()}:
            value = value.replace(spelling + "\\", prefix + "/").replace(spelling + "/", prefix + "/")
            if value == spelling:
                value = prefix
    if Path(value).is_absolute() or PureWindowsPath(value).is_absolute():
        return "本机位置（未公开）"
    return value


def public_payload(payload: dict, root: Path, output: Path) -> dict:
    payload = {**payload, "publication": {"mode": "public", "evidence": "local-only"}}
    payload.pop("source_files", None)
    payload["records"] = [{k: v for k, v in r.items() if k != "history"} for r in payload["records"]]
    return portable(payload, root, output)
