---
{
  "id": "IMP-llm-retrieval",
  "kind": "implementation",
  "title": "LLM 检索与来源定位改进",
  "status": "current",
  "progress": "",
  "summary": "说明已归档；当前说明见 IMP-llm-context",
  "gap": "",
  "relations": [
    {
      "relation": "implements",
      "to": {
        "record_id": "REQ-llm-retrieval"
      }
    }
  ],
  "sources": [
    {
      "workspace_id": "source",
      "path": "maintain-project-map/scripts/record_search.py",
      "role": "implementation"
    },
    {
      "workspace_id": "source",
      "path": "maintain-project-map/scripts/semantic_retrieval.py",
      "role": "implementation"
    },
    {
      "workspace_id": "source",
      "path": "maintain-project-map/scripts/source_locations.py",
      "role": "implementation"
    }
  ],
  "documentation": {
    "state": "archived",
    "reason": "旧说明中关于扫描、符号解析和物理归档尚未实现的陈述已不再适用。",
    "evidence": "已逐项核对 source_inventory、workspace_scanner、code_parsers、document_archive 与查询/阅读入口，143 项回归通过；当前约定写入 IMP-llm-context。",
    "archived_at": "2026-09-19T08:10:58.093643+00:00",
    "archive_path": "archive/records/da6749fdda41-475337b90e8d.md",
    "sha256": "1563edb518f22f1e902f9793a3da1d268ef9a6862e3fe4f8ec19bb7aa2dce852",
    "original_path": "records/implementation/llm-retrieval.md",
    "original_line": 24,
    "original_end_line": 45,
    "map_version": {
      "git_head": "17d5db0627dcb08ddfb7034b654851eeff5eb22a",
      "branch": "codex/llm-map-retrieval",
      "dirty": true
    },
    "successor": "IMP-llm-context",
    "current_gap": false
  }
}
---
这份说明已归档，不代表相关功能退役或需求撤销。

原因：旧说明中关于扫描、符号解析和物理归档尚未实现的陈述已不再适用。

当前说明：[[IMP-llm-context]]。

需要旧正文时显式查看历史；默认查询只返回本提示和替代定位。
