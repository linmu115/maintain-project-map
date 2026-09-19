"""Local, incremental embeddings over live map records. No network at query time."""
from __future__ import annotations

from dataclasses import dataclass
from contextlib import closing
import hashlib
import json
import math
import os
from pathlib import Path
import re
import sqlite3
import struct
import time


QUERY_INSTRUCTION = "为这个句子生成表示以用于检索相关文章："
ALGORITHM = "bge-cls-l2-v1"
WINDOW = 50
RRF_K = 60


class SemanticError(ValueError):
    def __init__(self, code, message):
        self.code = code
        super().__init__(message)


def codex_home():
    return Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))).expanduser()


def config_file():
    return Path(os.environ.get("PROJECT_MAP_RETRIEVAL_CONFIG", str(codex_home() / "config/project-map-retrieval.json"))).expanduser()


def digest(value):
    return hashlib.sha256(value.encode("utf-8") if isinstance(value, str) else value).hexdigest()


def file_digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest() if hasattr(hashlib, "file_digest") else digest(stream.read())


class LocalEncoder:
    """BGE's documented CLS pooling, L2 normalization and query instruction."""

    def __init__(self, config):
        try:
            import numpy as np
            import onnxruntime as ort
            from tokenizers import Tokenizer
        except ImportError as exc:
            raise SemanticError("missing_runtime", "Local embeddings need requirements-semantic.txt; lexical retrieval remains available.") from exc
        self.np = np
        if config.get("provider") != "bge_onnx" or config.get("schema_version") != 1:
            raise SemanticError("invalid_config", "Expected schema_version 1 and provider bge_onnx.")
        root = Path(config["model_dir"]).expanduser().resolve()
        model, tokenizer = root / "model_optimized.onnx", root / "tokenizer.json"
        hashes = {name: file_digest(path) for name, path in (("model", model), ("tokenizer", tokenizer))}
        for name in hashes:
            if hashes[name] != config.get(name + "_sha256"):
                raise SemanticError("model_changed", f"Local {name} checksum differs from the configured version; rerun setup or verify the model.")
        self.model_id = config.get("model_name", "bge-small-zh-v1.5")
        self.instruction = config.get("query_instruction", QUERY_INSTRUCTION)
        self.space_id = digest(json.dumps({**hashes, "algorithm": ALGORITHM, "instruction": self.instruction}, sort_keys=True))
        self.cache_root = Path(config.get("cache_dir", str(codex_home() / "project-maps/semantic"))).expanduser().resolve()
        self.batch_size = max(1, min(32, int(config.get("batch_size", 16))))
        self.tokenizer = Tokenizer.from_file(str(tokenizer))
        self.tokenizer.enable_truncation(max_length=512)
        self.tokenizer.enable_padding(pad_id=0, pad_token="[PAD]")
        options = ort.SessionOptions()
        options.intra_op_num_threads = max(1, min(8, int(config.get("cpu_threads", 4))))
        options.inter_op_num_threads = 1
        options.log_severity_level = 3
        self.session = ort.InferenceSession(str(model), sess_options=options, providers=["CPUExecutionProvider"])
        self.inputs = {i.name for i in self.session.get_inputs()}
        self.dimensions = self.session.get_outputs()[0].shape[-1]
        if not isinstance(self.dimensions, int) or self.dimensions < 1:
            raise SemanticError("invalid_model", "Embedding model must declare a fixed output dimension.")

    def encode(self, texts, *, query=False):
        result = []
        for start in range(0, len(texts), self.batch_size):
            batch = [(self.instruction + t) if query else t for t in texts[start:start + self.batch_size]]
            encoded = self.tokenizer.encode_batch(batch)
            if any(e.overflowing for e in encoded):
                raise SemanticError("input_too_long", "Embedding input exceeds 512 tokens; use a shorter query or smaller record chunks.")
            values = {"input_ids": [e.ids for e in encoded], "attention_mask": [e.attention_mask for e in encoded], "token_type_ids": [e.type_ids for e in encoded]}
            try:
                output = self.session.run(None, {k: self.np.asarray(v, dtype=self.np.int64) for k, v in values.items() if k in self.inputs})[0]
            except Exception as exc:
                raise SemanticError("inference_failed", f"Local embedding inference failed: {exc}") from exc
            if output.ndim == 3:
                output = output[:, 0]
            if output.ndim != 2:
                raise SemanticError("invalid_model", "Unsupported embedding output shape.")
            for vector in output.tolist():
                result.append(normalize(vector, self.dimensions))
        return result


def load_encoder():
    path = config_file()
    if not path.is_file():
        raise SemanticError("not_configured", "Local semantic retrieval is not configured; run scripts/setup_retrieval.py once to enable it.")
    try:
        return LocalEncoder(json.loads(path.read_text(encoding="utf-8-sig")))
    except SemanticError:
        raise
    except Exception as exc:
        raise SemanticError("local_model_unavailable", f"Local embedding configuration or runtime unavailable: {exc}") from exc


def normalize(vector, dimensions):
    if len(vector) != dimensions or not all(math.isfinite(v) for v in vector):
        raise SemanticError("invalid_vector", "Embedding dimension or finite-value check failed.")
    norm = math.sqrt(sum(v * v for v in vector))
    if not math.isfinite(norm) or norm < 1e-12:
        raise SemanticError("invalid_vector", "Embedding has zero length.")
    return [v / norm for v in vector]


@dataclass
class Chunk:
    record: dict
    text: str
    heading: str
    field: str
    offset: int
    embedded: str

    @property
    def key(self):
        return digest(self.embedded)

    def snippet(self, budget=240):
        value = {"field": self.field, "text": self.text[:budget] + ("…" if len(self.text) > budget else "")}
        if self.field == "body":
            value["line"] = self.record["line"] if "table_fields" in self.record else self.record["line"] + self.record["body"][:self.offset].count("\n")
        if self.heading:
            value["heading"] = self.heading
        return value


def _sections(body):
    """Bounded sections, retaining exact source offsets and ignoring fenced headings."""
    start, cursor, heading, fence = 0, 0, "", None
    for line in body.splitlines(keepends=True):
        stripped = line.lstrip()
        marker = re.match(r"(`{3,}|~{3,})", stripped)
        if marker:
            mark = marker[1]
            if fence is None:
                fence = mark
            elif mark[0] == fence[0] and len(mark) >= len(fence):
                fence = None
        match = re.match(r"#{1,6}\s+(.+?)\s*#*\s*$", line) if fence is None else None
        if match:
            if cursor > start:
                yield start, cursor, heading
            start, heading = cursor, match[1]
        cursor += len(line)
    if cursor > start:
        yield start, cursor, heading


def _paragraphs(body, first, last):
    start = first
    for match in re.finditer(r"\r?\n[ \t]*\r?\n", body[first:last]):
        end = first + match.end()
        # Keep a standalone section heading with its first paragraph.
        value = body[start:end].strip()
        if value and not re.fullmatch(r"#{1,6}\s+[^\r\n]+", value):
            yield start, end
            start = end
    if start < last:
        yield start, last


def _embedding_text(text):
    # Paths in Markdown link destinations can overwhelm short Chinese passages.
    # Keep their labels for embedding, but return the untouched source as evidence.
    text = re.sub(r"!?\[([^\]\n]+)\]\([^\)\n]+\)", r"\1", text)
    return re.sub(r"\[\[([^\]\n]+)\]\]", lambda m: m[1].replace("|", " "), text)


def chunks_for(doc):
    from system_map import module_records
    from record_search import KIND_NAMES
    _, scopes = module_records(doc)
    titles = {r["id"]: r["title"] for r in doc["records"]}
    chunks = []
    for record in doc["records"]:
        context = " / ".join(str(v) for v in (doc["project"].get("name"), titles.get(scopes.get(record["id"])), record["title"], KIND_NAMES.get(record["kind"], record["kind"])) if v)[:120]
        body = record.get("body", "")
        # A summary is live source metadata too; it is never presented as a body hit.
        summary = record.get("summary") or (record["title"] if not body.strip() else "")
        if summary and summary not in body:
            for offset in range(0, len(summary), 272):
                text = summary[offset:offset + 320]
                chunks.append(Chunk(record, text, "", "summary" if record.get("summary") else "title", offset, context + "\n" + _embedding_text(text)))
                if offset + 320 >= len(summary):
                    break
        for section_start, section_end, heading in _sections(body):
            for first, last in _paragraphs(body, section_start, section_end):
                for offset in range(first, last, 272):
                    end = min(offset + 320, last)
                    raw = body[offset:end]
                    text = raw.strip()
                    if text:
                        begin = offset + len(raw) - len(raw.lstrip())
                        prefix = context + (" / " + heading[:40] if heading else "")
                        chunks.append(Chunk(record, text, heading, "body", begin, prefix + "\n" + _embedding_text(text)))
                    if end == last:
                        break
        if len(chunks) > 50000:
            raise SemanticError("map_too_large", "Map exceeds 50,000 semantic chunks; use lexical retrieval or a smaller map.")
    return chunks


def _cached_vector(row, dimensions):
    if row is None:
        return None
    blob, checksum = row
    if not isinstance(blob, bytes) or len(blob) != dimensions * 4 or digest(blob) != checksum:
        return None
    vector = struct.unpack(f"<{dimensions}f", blob)
    if not all(math.isfinite(v) for v in vector) or abs(sum(v * v for v in vector) - 1) > .001:
        return None
    return vector


def _pack(vector, dimensions):
    value = struct.pack(f"<{dimensions}f", *normalize(vector, dimensions))
    return value, digest(value)


def semantic_search(doc, candidates, query, *, encoder=None, window=WINDOW):
    """Return one best live excerpt per record; cache holds vectors, never old text."""
    if not candidates:
        return [], {"embedded_chunks": 0, "reused_chunks": 0, "eligible_records": 0}
    ids = {r["id"] for r in candidates}
    if len(ids) != len(candidates):
        raise SemanticError("duplicate_ids", "Semantic retrieval requires unique record IDs.")
    encoder = encoder or load_encoder()
    all_chunks = chunks_for(doc)
    chunks = [c for c in all_chunks if c.record["id"] in ids]
    active = {c.key for c in all_chunks}
    selected = {c.key: c.embedded for c in chunks}
    identity = json.dumps([os.path.normcase(str(Path(doc["manifest_path"]).resolve())), doc["project"]["project_id"], encoder.space_id])
    encoder.cache_root.mkdir(parents=True, exist_ok=True)
    path = encoder.cache_root / (digest(identity) + ".sqlite3")
    try:
        with closing(sqlite3.connect(path, timeout=30)) as db, db:
            db.execute("CREATE TABLE IF NOT EXISTS vectors (key TEXT PRIMARY KEY, data BLOB NOT NULL, checksum TEXT NOT NULL)")
            db.execute("CREATE TABLE IF NOT EXISTS queries (key TEXT PRIMARY KEY, data BLOB NOT NULL, checksum TEXT NOT NULL, used REAL NOT NULL)")
            rows = {key: (data, checksum) for key, data, checksum in db.execute("SELECT key, data, checksum FROM vectors")}
            vectors = {key: _cached_vector(rows.get(key), encoder.dimensions) for key in selected}
            missing = [key for key, value in vectors.items() if value is None]
            if missing:
                embedded = encoder.encode([selected[key] for key in missing])
                if len(embedded) != len(missing):
                    raise SemanticError("invalid_vector", "Embedding response count mismatch.")
                for key, vector in zip(missing, embedded):
                    blob, checksum = _pack(vector, encoder.dimensions)
                    # Use float32 for fresh and cached ranks alike; paging remains stable.
                    vectors[key] = struct.unpack(f"<{encoder.dimensions}f", blob)
                    db.execute("INSERT OR REPLACE INTO vectors VALUES (?, ?, ?)", (key, blob, checksum))
            obsolete = set(rows) - active
            db.executemany("DELETE FROM vectors WHERE key = ?", [(key,) for key in obsolete])
            query_key = digest(query)
            vector = _cached_vector(db.execute("SELECT data, checksum FROM queries WHERE key = ?", (query_key,)).fetchone(), encoder.dimensions)
            query_reused = vector is not None
            if vector is None:
                blob, checksum = _pack(encoder.encode([query], query=True)[0], encoder.dimensions)
                vector = struct.unpack(f"<{encoder.dimensions}f", blob)
                db.execute("INSERT OR REPLACE INTO queries VALUES (?, ?, ?, ?)", (query_key, blob, checksum, time.time()))
            else:
                db.execute("UPDATE queries SET used = ? WHERE key = ?", (time.time(), query_key))
            db.execute("DELETE FROM queries WHERE key NOT IN (SELECT key FROM queries ORDER BY used DESC LIMIT 128)")
    except sqlite3.Error as exc:
        raise SemanticError("cache_unavailable", f"Local vector cache unavailable ({path}): {exc}") from exc
    best = {}
    for chunk in chunks:
        score = sum(a * b for a, b in zip(vectors[chunk.key], vector))
        rid = chunk.record["id"]
        if rid not in best or score > best[rid][0]:
            best[rid] = (score, chunk)
    ranked = sorted(best.values(), key=lambda value: (-value[0], value[1].record["id"]))[:window]
    return [(c.record, {"match": "semantic", "snippet": c.snippet(), "semantic_similarity": score}) for score, c in ranked], {
        "model": encoder.model_id, "space_id": encoder.space_id, "cache_path": str(path), "eligible_records": len(ids),
        "chunks": len(chunks), "embedded_chunks": len(missing), "reused_chunks": len(selected) - len(missing), "removed_chunks": len(obsolete), "query_reused": query_reused}


def fuse(lexical, semantic, query, *, window=WINDOW):
    """Equal-weight RRF over two record rankings, after deduplicating each channel."""
    combined = {}
    for channel, results in (("lexical", lexical), ("semantic", semantic)):
        seen = set()
        for record, info in results:
            rid = record["id"]
            if rid in seen:
                continue
            if len(seen) == window:
                break
            seen.add(rid)
            rank = len(seen)
            item = combined.setdefault(rid, {"record": record, "info": dict(info), "score": 0., "ranks": {}})
            item["score"] += 1 / (RRF_K + rank)
            item["ranks"][channel] = rank
            if channel == "semantic":
                item["info"]["semantic_similarity"] = info["semantic_similarity"]
                if item["info"].get("match") == "partial_terms" and "snippet" in info:
                    item["info"]["snippet"] = {**info["snippet"], "via": "semantic"}
    q = query.casefold().strip()

    def order(item):
        record = item["record"]
        tier = 0 if q == record["id"].casefold() else 1 if q == record["title"].casefold() or q in [a.casefold() for a in record.get("aliases", [])] else 2
        return tier, -item["score"], min(item["ranks"].values()), record["id"]

    return [(item["record"], {**item["info"], "retrieved_by": list(item["ranks"]), "rrf_score": item["score"], "ranks": item["ranks"]}) for item in sorted(combined.values(), key=order)]
