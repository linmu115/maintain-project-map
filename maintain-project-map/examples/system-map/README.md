# 系统地图示例

这是一套虚构、可移动的阅读与查询示例，不代表真实 DSH 组件的划分。

- `system/` 明确收录 Core、Board、Graph 三张独立地图，只有整体组织图。
- `core/` 维护两类接口的唯一合同。
- `board/`、`graph/` 各自维护接入说明，共享同一 Core 接口，并有交叉关系。
- 外部宿主仅作为关系端点，没有自动收录。

从 Skill 所在目录运行：

```text
python scripts/render_map.py examples/system-map/system/project.yaml
python scripts/project_map.py interfaces examples/system-map/system --limit 5
python scripts/project_map.py impact examples/system-map/system IF-reference --project example-core
```

打开生成回执中的本地 HTTP 链接，在“整体组织”选择项目，再在护照内点击“进入项目”。目标标签页展示完整项目地图。生成的 `views/` 是本机阅读快照，不是维护源。
