"""Small deliberately incomplete archival workflow for an isolated test fixture."""

import argparse
import json
from pathlib import Path


def archive(inputs, output):
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    manifest = []
    for input_name in inputs:
        source = Path(input_name).resolve()
        if source.suffix.lower() not in {".txt", ".md"}:
            raise ValueError(f"Unsupported input: {source}")
        content = source.read_text(encoding="utf-8")
        target = output / source.name
        target.write_text(content, encoding="utf-8")
        manifest.append({"source": str(source), "file": target.name})
    (output / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    parser.add_argument("inputs", nargs="+")
    args = parser.parse_args()
    archive(args.inputs, args.out)
