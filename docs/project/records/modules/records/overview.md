---
{
  "id": "MOD-records",
  "kind": "module",
  "title": "读取和维护权威记录",
  "status": "current",
  "summary": "绑定现有文档章节或表格，读取独立记录及关系，提供有范围的查询与状态维护。",
  "relations": [
    {
      "relation": "implements",
      "to": {
        "record_id": "REQ-assets"
      }
    },
    {
      "relation": "implements",
      "to": {
        "record_id": "REQ-maintenance"
      }
    },
    {
      "relation": "implements",
      "to": {
        "record_id": "REQ-relations"
      }
    },
    {
      "relation": "flows_to",
      "to": {
        "record_id": "MOD-reader"
      },
      "reason": "仅在需要阅读页面时，将本次读取的共同内容交给呈现模块。"
    },
    {
      "relation": "provides",
      "to": {
        "record_id": "IF-record-data"
      }
    },
    {
      "relation": "provides",
      "to": {
        "record_id": "IF-map-query"
      }
    }
  ],
  "sources": [
    {
      "path": "maintain-project-map/scripts/project_map.py",
      "role": "skill-source-authority",
      "workspace_id": "source",
      "reviewed_sha256": "67aee0a424ef3fe0019e0db34fbc97d9168e2edc6e35ee107faef86a63b49f6a",
      "reviewed_dependencies": [
        {
          "path": "maintain-project-map/scripts/document_archive.py",
          "sha256": "da4f6deaadde3da10c228a46f6ce02d3f5e2e2d3a970664420b05685f622f9e4"
        },
        {
          "path": "maintain-project-map/scripts/record_search.py",
          "sha256": "3b8ed4498616ad797569311d344f0a33436c1f0a54cd37e446d448c885cd258b"
        },
        {
          "path": "maintain-project-map/scripts/semantic_retrieval.py",
          "sha256": "14195cee22caab390ca24ad0ec5d7acdeb700d0497d2fa137eb80f6fba94c331"
        },
        {
          "path": "maintain-project-map/scripts/source_inventory.py",
          "sha256": "9a955c3abda4b41beb79fc713b25c7e3093c2b1fa4844fc9980e7e2d18c22e90"
        },
        {
          "path": "maintain-project-map/scripts/source_locations.py",
          "sha256": "f748ce97270ff5619278a4caf28d07778918ed4fcb601d28ed91f10388e870d0"
        },
        {
          "path": "maintain-project-map/scripts/system_map.py",
          "sha256": "c591323f312d35a7428a1e92983f24d2aac23dba3f980cf6bf7838a4856be979"
        }
      ]
    },
    {
      "path": "maintain-project-map/references/asset-model.md",
      "role": "skill-source-authority",
      "workspace_id": "source",
      "reviewed_sha256": "d50881551dfb02ac4ed9dbb2ea1c8fe7870920abe6da47db832be19823b8103d",
      "reviewed_dependencies": []
    },
    {
      "path": "maintain-project-map/references/lifecycle.md",
      "role": "skill-source-authority",
      "workspace_id": "source",
      "reviewed_sha256": "9befabcebdf7eb4f016279ed10bfe1958ea9f98667f1b1966c723c17ed0d35fd",
      "reviewed_dependencies": []
    }
  ],
  "source_review": {
    "reviewed_at": "2026-09-19T08:50:49.489071+00:00",
    "reason": "复核原字节归档规则允许 CRLF 保留；真实 Git 往返验证通过，公共导出和本机读取行为不变。",
    "body_sha256": "f7ade69f197a71607a2e50501aac2db3334a36a62a6508b7c71f1054a5b256ff"
  }
}
---

# 读取和维护权威记录

已有需求文档可以按原章节或表格编号绑定。需要新独立条目时，使用带身份、类型与标题的 Markdown。规范正文仍在原文件维护，搜索与页面读取同一内容。

合并或退役只更新记录本身，并保留原因和后继；不通过记录状态去删除产品代码。失败探索按其适用条件保存，不等同于功能退役。

代码入口：maintain-project-map/scripts/project_map.py。


录入资料先看 [[IF-record-data|记录与绑定约定]]；查询和分页结果见 [[IF-map-query]]。状态与证据的区别见 [[OBJ-evidence]]。

源码工作区通过显式绑定补查入口与依赖，变化关联到来源记录后提示复核。确认说明失效时将原文归档、在原位置保留后继或说明缺口；功能和有效需求的状态单独保留。当前能力见 [[IMP-llm-context]]。
