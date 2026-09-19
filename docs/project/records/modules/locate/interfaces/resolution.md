---
{
  "id": "IF-project-location",
  "kind": "interface",
  "title": "项目名称、ID 与位置解析",
  "status": "current",
  "summary": "支持项目名称与别名查询，区分同名项目、工作树、默认位置和失效路径；解析不加载正文。",
  "sources": [
    {
      "path": "maintain-project-map/references/operations.md",
      "role": "skill-source-authority",
      "workspace_id": "source",
      "reviewed_sha256": "d7c4d10f51271240631bfa6155d8841e9d6524a80cfdf04df54ef409b955f3a6",
      "reviewed_dependencies": []
    },
    {
      "path": "maintain-project-map/scripts/map_catalog.py",
      "role": "skill-source-authority",
      "workspace_id": "source",
      "reviewed_sha256": "626732649f0317a78d49974744029d722d3ab10eb6c41b818e5bb168dd9a404c",
      "reviewed_dependencies": [
        {
          "path": "maintain-project-map/scripts/project_map.py",
          "sha256": "67aee0a424ef3fe0019e0db34fbc97d9168e2edc6e35ee107faef86a63b49f6a"
        }
      ]
    }
  ],
  "relations": [
    {
      "relation": "related",
      "to": {
        "record_id": "OBJ-map-identity"
      }
    }
  ],
  "source_review": {
    "reviewed_at": "2026-09-19T08:47:28.513888+00:00",
    "reason": "核对新增公共静态导出和归档 Git 原字节保护；147 项完整回归与后续 16 项专项通过。其他来源仅统一 LF，Git 内容差异确认未改逻辑，保留原说明并更新跨系统可复用基线。",
    "body_sha256": "c4a9a5f127616a0d968bbf4816f520a2237ad1a06b10857fa4396c36b885ba97"
  }
}
---

# 项目名称、ID 与位置解析


提供项目名称、别名、明确路径或稳定项目 ID，定位模块返回可读取的 project.yaml。比如输入 Archify 就能找到已登记的本机地图；移动仓库后只需沿用 ID 登记新位置，需求和接口的 ID 不必改名。

名称查询依次匹配 ID、完整名称或别名、名称子串。同名但不同 ID 时返回候选。一个 ID 有多个工作树时，优先匹配明确上下文，再选明确指定的默认位置；没有默认且仍有多个合理位置时返回候选。默认位置失效不会回退到旧副本。登记保存元信息，外部项目正文不复制到本地图。

命令与参数见 Skill 的 references/operations.md。map_catalog.py 提供 locate/register/list，默认返回 8 项、最多 50 项，可分页；沿用本机 project-map-registry/v1 注册表，向项目条目添加 aliases 和 preferred_manifest 可选字段。project_map.py resolve 继续支持稳定 ID，并尊重同一默认位置。已知使用方是记录查询和阅读生成；它们拿到位置后才按需读取。缺失或损坏的清单报告该位置不可用，不把可定位等同于内容验证通过。
