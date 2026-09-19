"""Small lexical retrieval over already loaded records; no model or index service."""
from __future__ import annotations

import math
import re


FIELD_WEIGHTS = {"id": 12, "title": 8, "aliases": 7, "summary": 3, "body": 1, "date": 2, "kind": .5}
KIND_NAMES = {"module": "模块", "interface": "接口", "implementation": "实现", "requirement": "需求", "decision": "决定", "verification": "验证", "history": "历程", "experience": "经验", "object": "对象", "exploration": "探索", "update": "更新"}
CURRENT_KINDS = {"module", "interface", "implementation"}
BACKGROUND_KINDS = {"history", "experience", "update", "exploration"}


def fields(record):
    result = {key: str(record.get(key, "")) for key in ("id", "title", "summary", "body")}
    result["aliases"] = "\n".join(record.get("aliases", []))
    result["kind"] = record.get("kind", "") + " " + KIND_NAMES.get(record.get("kind"), "")
    if record.get("date"):
        result["date"] = str(record["date"])
    return result


def query_terms(query):
    # Preserve punctuation within symbols, IDs and paths. Spaces separate terms.
    return list(dict.fromkeys(query.casefold().split()))


def _cjk_terms(query):
    terms = []
    for chunk in re.findall(r"[\u3400-\u9fff]+|[^\s\u3400-\u9fff]+", query.casefold()):
        if re.fullmatch(r"[\u3400-\u9fff]{3,}", chunk):
            terms.extend(chunk[i:i + 2] for i in range(len(chunk) - 1))
        elif chunk.strip("?!？！，,。."):
            terms.append(chunk.strip("?!？！，,。."))
    return list(dict.fromkeys(terms))


def _snippet(record, terms, budget=240):
    """Return source text near a hit, never a generated explanation."""
    choices = []
    body = record.get("body", "")
    cursor = 0
    for line in body.splitlines(keepends=True):
        count = sum(term in line.casefold() for term in terms)
        if count:
            choices.append((count, cursor, line))
        cursor += len(line)
    if choices:
        _, offset, value = max(choices, key=lambda item: (item[0], not item[2].lstrip().startswith("#"), -item[1]))
        source_field = "body"
        line_no = record["line"] if "table_fields" in record else record["line"] + body[:offset].count("\n")
    else:
        source_field = next((key for key in ("title", "aliases", "summary", "id", "date", "kind")
                             if any(t in fields(record).get(key, "").casefold() for t in terms)), "summary")
        value, line_no = fields(record).get(source_field, ""), None
    hits = [m.start() for term in terms if (m := re.search(re.escape(term), value, re.IGNORECASE))]
    start = max(0, min(hits, default=0) - 60) if len(value) > budget else 0
    text = value[start:start + budget].strip()
    result = {"field": source_field, "text": ("…" if start else "") + text + ("…" if start + budget < len(value) else "")}
    if line_no is not None:
        result["line"] = line_no
    return result


def rank_records(records, query, match="auto", *, hybrid_candidates=False):
    if match not in {"auto", "all", "any", "phrase"}:
        raise ValueError("match must be auto, all, any or phrase")
    q = query.casefold().strip()
    terms = [q] if match == "phrase" else query_terms(q)
    prepared = [(record, {key: value.casefold() for key, value in fields(record).items()}) for record in records]

    def retrieve(tokens, require_all, mode):
        results = []
        for record, values in prepared:
            found = [t for t in tokens if any(t in value for value in values.values())]
            if not found or (require_all and len(found) != len(tokens)):
                continue
            if mode == "cjk_bigrams":
                # This is literal overlap, not synonym or semantic retrieval.
                # Hybrid fusion needs a wider literal candidate pool; otherwise a
                # useful semantic hit with two literal terms can never get both votes.
                minimum = 2 if hybrid_candidates else max(2, math.ceil(len(tokens) * .45))
                if len(found) < minimum:
                    continue
                latin = [t for t in tokens if re.search(r"[a-z0-9]", t)]
                if any(t not in found for t in latin):
                    continue
            exact = q == values["id"]
            named = q == values["title"] or q in [a.casefold() for a in record.get("aliases", [])]
            tier = 0 if exact else 1 if named else 2
            score = sum(FIELD_WEIGHTS[key] * sum(t in value for t in found) for key, value in values.items())
            if q in values["title"] or any(q in a.casefold() for a in record.get("aliases", [])):
                score += 8
            kind_weight = 1.2 if record["kind"] in CURRENT_KINDS else .7 if record["kind"] in BACKGROUND_KINDS else 1
            reasons = [key for key, value in values.items() if any(t in value for t in found)]
            results.append(((tier, -len(found) / len(tokens), -score * kind_weight, record["id"]), record,
                            {"matched_fields": reasons, "matched_terms": found,
                             "match": "exact" if tier < 2 else "all_terms" if len(found) == len(tokens) and mode != "cjk_bigrams" else "partial_terms",
                             "snippet": _snippet(record, found)}))
        return results

    mode = "phrase" if match == "phrase" else "any_terms" if match == "any" else "all_terms"
    results = retrieve(terms, match != "any", mode)
    if not results and match == "auto":
        if re.search(r"[\u3400-\u9fff]{3,}", q):
            mode, terms = "cjk_bigrams", _cjk_terms(q)
            # Discard unseen Chinese cross-word shingles (e.g. 询项), retaining
            # unknown identifiers as constraints. At least two literal hits are
            # still required; this fallback never claims to understand synonyms.
            terms = [t for t in terms if re.search(r"[a-z0-9]", t) or any(t in value for _, values in prepared for value in values.values())]
            results = retrieve(terms, False, mode)
        elif len(terms) > 1:
            mode = "any_terms"
            results = retrieve(terms, False, mode)
    results.sort(key=lambda item: item[0])
    return [(record, info) for _, record, info in results], mode, terms


def compact_response(command, result):
    """CLI view only: keep the library's complete receipts for existing callers."""
    if command == "search":
        keep = ("id", "kind", "title", "status", "progress", "gap", "match", "retrieved_by", "snippet", "documentation", "source_health")
        return {**{k: v for k, v in result.items() if k not in {"results", "fingerprint", "module_id", "kinds", "query_terms", "retrieval"}},
                **({"retrieval": {k: v for k, v in result["retrieval"].items() if k != "diagnostics"}} if "retrieval" in result else {}),
                **({"module_id": result["module_id"]} if result.get("module_id") else {}),
                **({"kinds": result["kinds"]} if result.get("kinds") else {}),
                "results": [{k: r[k] for k in keep if r.get(k) not in (None, "", [])} for r in result["results"]]}
    if command == "read":
        record = result["record"]
        keep = ("id", "kind", "title", "status", "progress", "gap", "lifecycle", "review", "path", "date", "outcome", "applicability", "coverage_note", "module_id", "task_id", "documentation", "source_review")
        out = {"project_id": result["project_id"], "record": {k: record[k] for k in keep if record.get(k) not in (None, "", [])},
               "body": result["body"], "receipt": result["receipt"], "source_lines": result["source_lines"],
               "truncated": result["truncated"], "coverage": result["coverage"],
               "sources": [{k: v for k, v in s.items() if k not in {"path", "workspace_root"} or "resolved_path" not in s} for s in result.get("resolved_sources", [])],
               "map_version": {k: v for k, v in result["version"].items() if k in {"git_head", "branch", "dirty", "context_scope"}}}
        if result.get("sources_truncated"):
            out.update(sources_truncated=True, sources_total=result["sources_total"])
        if result.get("source_health"): out["source_health"] = result["source_health"]
        if result["continuation"]:
            out["continuation"] = {k: v for k, v in result["continuation"].items() if k != "fingerprint"}
            out["continuation"]["offset_unit"] = result["offset_unit"]
        out["metadata_detail"] = "compact; --detail full for relations and other metadata"
        return out
    return result
