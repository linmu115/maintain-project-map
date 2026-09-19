---
{
  "id": "IF-native-diagram",
  "kind": "interface",
  "title": "图源登记、节点绑定与交付",
  "status": "current",
  "summary": "地图登记原生图文件和记录映射；Archify 负责底层格式、校验和图交互。",
  "sources": [
    {
      "path": "maintain-project-map/references/archify-authoring.md",
      "role": "skill-source-authority",
      "workspace_id": "source",
      "reviewed_sha256": "cea5832f1c7aba661ecf647f35edd6677b6a1e5025a45dd7cb3f0ac6497a917e",
      "reviewed_dependencies": []
    },
    {
      "path": "maintain-project-map/assets/vendor/archify/schemas/architecture.schema.json",
      "role": "skill-source-authority",
      "workspace_id": "source",
      "reviewed_sha256": "94568c7ca72c07ac0ee02ee76bd39392874b3a13bb796a127962be68d0f5bc90",
      "reviewed_dependencies": []
    },
    {
      "path": "maintain-project-map/assets/vendor/archify/schemas/workflow.schema.json",
      "role": "skill-source-authority",
      "workspace_id": "source",
      "reviewed_sha256": "2128e82afd2b971fcb7d80ada86fa836bb4a5035b504053b87d3aeefec380e3c",
      "reviewed_dependencies": []
    },
    {
      "path": "maintain-project-map/scripts/archify_adapter.py",
      "role": "skill-source-authority",
      "workspace_id": "source",
      "reviewed_sha256": "1cb5a7341603996feccfc850ddf29daa4c3bfed62f398af47e53a1f6a66a6964",
      "reviewed_dependencies": [
        {
          "path": "maintain-project-map/scripts/canvas_adapter.py",
          "sha256": "95ba849e4b7d90f8f072e347665470865e2331dfd1e2d3ad284ebcacfbd53280"
        }
      ]
    }
  ],
  "relations": [
    {
      "relation": "consumes",
      "to": {
        "record_id": "IF-record-data"
      }
    }
  ],
  "source_review": {
    "reviewed_at": "2026-09-19T08:47:33.955551+00:00",
    "reason": "核对新增公共静态导出和归档 Git 原字节保护；147 项完整回归与后续 16 项专项通过。其他来源仅统一 LF，Git 内容差异确认未改逻辑，保留原说明并更新跨系统可复用基线。",
    "body_sha256": "f1659d53e27b4d87aed9a060512e8d06e432f4b848ad3d1d69ea2bf669dbe420"
  }
}
---

# 图源登记、节点绑定与交付


作者交付架构或工作流 JSON，并在 project.yaml 声明源路径及 node_records。比如一个“提交事务”节点可关联模块、需求和验证的入口，节点本身仍使用原生 ID。

完整地图接入方式见 [Archify 图源维护](../../../../../../../maintain-project-map/references/archify-authoring.md)；底层图格式只以 [架构 schema](../../../../../../../maintain-project-map/assets/vendor/archify/schemas/architecture.schema.json) 和 [工作流 schema](../../../../../../../maintain-project-map/assets/vendor/archify/schemas/workflow.schema.json) 为准。

提供方是本 Skill 的图适配模块，底层能力来自 Archify。输入经原生交付后得到可读图、节点对应与回执；无效源不能被旧图冒充，缺少绑定时明确显示未关联。原版和嵌入版摘要分别保存。

现有 A/B 清单每种类型接入一份主图。更深模块可用原生边界、聚焦视图和文档互链表达；额外图没有自动加入页面的导航功能。普通文本修订不要求重画全部图。
