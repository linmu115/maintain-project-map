#!/usr/bin/env python3
"""Explicit one-time installation of the pinned local Chinese embedding model."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import tempfile

from semantic_retrieval import LocalEncoder, QUERY_INSTRUCTION, codex_home, config_file, file_digest


REPOSITORY = "Qdrant/bge-small-zh-v1.5"
REVISION = "46fbe35fd4374a00fee7de77dfddaeb6dd6a2c59"
FILES = {
    "model_optimized.onnx": "1294ea4b6331115a353d81f96b85e8c8d7fdcc284453d5b2fab5b016230aad38",
    "tokenizer.json": "48cea5d44424912a6fd1ea647bf4fe50b55ab8b1e5879c3275f80e339e8fae26",
}


def download_file(path, expected):
    if path.is_file() and file_digest(path) == expected:
        return False
    try:
        import requests
    except ImportError as exc:
        raise ValueError("Model download needs requests from requirements-semantic.txt.") from exc
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, suffix=".part", delete=False) as stream:
            temp = Path(stream.name)
            with requests.get(f"https://huggingface.co/{REPOSITORY}/resolve/{REVISION}/{path.name}", stream=True, timeout=(15, 90)) as response:
                response.raise_for_status()
                for block in response.iter_content(1024 * 1024):
                    stream.write(block)
        if file_digest(temp) != expected:
            raise ValueError(f"Checksum mismatch for {path.name}; the model was not installed.")
        os.replace(temp, path)
        return True
    finally:
        if temp and temp.exists():
            temp.unlink()


def setup(model_dir=None, cache_dir=None, replace=False):
    root = Path(model_dir or codex_home() / "models/project-map/bge-small-zh-v1.5" / REVISION).expanduser().resolve()
    config_path = config_file()
    config = {"schema_version": 1, "provider": "bge_onnx", "model_name": "BAAI/bge-small-zh-v1.5",
              "repository": REPOSITORY, "revision": REVISION, "model_dir": str(root),
              "model_sha256": FILES["model_optimized.onnx"], "tokenizer_sha256": FILES["tokenizer.json"],
              "query_instruction": QUERY_INSTRUCTION, "batch_size": 16, "cpu_threads": 4,
              "cache_dir": str(Path(cache_dir or codex_home() / "project-maps/semantic").expanduser().resolve())}
    if config_path.exists() and not replace:
        existing = json.loads(config_path.read_text(encoding="utf-8-sig"))
        if existing != config:
            raise ValueError("A different local configuration exists; inspect it before explicitly using --replace.")
    downloaded = sum(download_file(root / name, checksum) for name, checksum in FILES.items())
    # Do not enable an installation whose runtime cannot produce an embedding.
    encoder = LocalEncoder(config)
    encoder.encode(["项目入口"], query=True)
    config_path.parent.mkdir(parents=True, exist_ok=True)
    temp = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=config_path.parent, suffix=".tmp", delete=False) as stream:
            temp = Path(stream.name)
            json.dump(config, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
        os.replace(temp, config_path)
    finally:
        if temp and temp.exists():
            temp.unlink()
    return {"enabled": True, "config_path": str(config_path), "model": encoder.model_id,
            "dimensions": encoder.dimensions, "downloaded_files": downloaded, "inference": "local_cpu"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-dir")
    parser.add_argument("--cache-dir")
    parser.add_argument("--replace", action="store_true", help="Replace an inspected existing retrieval configuration")
    args = parser.parse_args()
    try:
        print(json.dumps(setup(args.model_dir, args.cache_dir, args.replace), ensure_ascii=False, indent=2))
    except Exception as exc:
        parser.exit(2, f"Local semantic setup failed: {exc}\n")
