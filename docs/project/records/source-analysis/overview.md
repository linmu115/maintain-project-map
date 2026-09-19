---
{
  "id": "SRC-source-inventory",
  "kind": "note",
  "title": "源码入口与依赖",
  "status": "current",
  "generated_by": "project-map-source",
  "summary": "绑定 Git 工作区的入口、静态依赖、待补登记与待复核说明；供人和 LLM 按需查阅。"
}
---
# 源码入口与依赖

这里是绑定工作区的静态扫描结果。用于补查入口、依赖和说明缺口；未登记不代表架构错误，静态引用不等于运行时调用。

LLM 阅读入口：`project_map.py source <地图> --kind entrypoint|dependency|call|symbol|gap|review --query <名称或路径>`。结果支持分页，不必加载全量源码。

## 工作区 source

分支 `codex/llm-map-retrieval`，提交 `17d5db0627dcb08ddfb7034b654851eeff5eb22a`；扫描 28 个文件。内容指纹 `f939b5cbf667a781`。

### 入口

- `maintain-project-map/scripts/development_history.py` 460：python_main_guard → `maintain-project-map/scripts/development_history.py`
- `maintain-project-map/scripts/map_catalog.py` 149：python_main_guard → `maintain-project-map/scripts/map_catalog.py`
- `maintain-project-map/scripts/project_map.py` 1072：python_main_guard → `maintain-project-map/scripts/project_map.py`
- `maintain-project-map/scripts/render_map.py` 186：python_main_guard → `maintain-project-map/scripts/render_map.py`
- `maintain-project-map/scripts/search_session.py` 146：python_main_guard → `maintain-project-map/scripts/search_session.py`
- `maintain-project-map/scripts/serve_map.py` 337：python_main_guard → `maintain-project-map/scripts/serve_map.py`
- `maintain-project-map/scripts/setup_retrieval.py` 78：python_main_guard → `maintain-project-map/scripts/setup_retrieval.py`

### 依赖与待补登记

提取 292 项导入、4684 条静态调用/继承线索；待核对登记缺口 17 项。
- `maintain-project-map/scripts/archify_adapter.py:18` → `maintain-project-map/scripts/canvas_adapter.py`
- `maintain-project-map/scripts/development_history.py:335` → `maintain-project-map/scripts/document_archive.py`
- `maintain-project-map/scripts/development_history.py:440` → `maintain-project-map/scripts/project_map.py`
- `maintain-project-map/scripts/document_archive.py:26` → `maintain-project-map/scripts/project_map.py`
- `maintain-project-map/scripts/document_archive.py:45` → `maintain-project-map/scripts/system_map.py`
- `maintain-project-map/scripts/map_catalog.py:10` → `maintain-project-map/scripts/project_map.py`
- `maintain-project-map/scripts/project_map.py:516` → `maintain-project-map/scripts/document_archive.py`
- `maintain-project-map/scripts/project_map.py:612` → `maintain-project-map/scripts/system_map.py`
- `maintain-project-map/scripts/project_map.py:810` → `maintain-project-map/scripts/record_search.py`
- `maintain-project-map/scripts/project_map.py:825` → `maintain-project-map/scripts/semantic_retrieval.py`
- `maintain-project-map/scripts/project_map.py:838` → `maintain-project-map/scripts/source_inventory.py`
- `maintain-project-map/scripts/project_map.py:878` → `maintain-project-map/scripts/source_locations.py`

### 待复核说明

本次没有发现相对既有基线的变化；尚无人工核对基线的说明不因此视为有效。

### 覆盖范围

排除或不支持的文件 246 项，解析限制 0 项。仅扫描当前 Git 工作区，包含未忽略的新文件；不进入子仓库、依赖包或默认排除目录。动态调用、反射、路径别名及未支持语言需另行核对。完整清单通过 `--kind coverage` 查询。
