---
{
  "id": "IF-record-data",
  "kind": "interface",
  "title": "记录、绑定与语义关系",
  "status": "current",
  "summary": "原文件维护正式内容，地图用身份和绑定连接已有章节、接口与证据。",
  "sources": [
    {
      "path": "maintain-project-map/references/asset-model.md",
      "role": "skill-source-authority",
      "workspace_id": "source",
      "reviewed_sha256": "d50881551dfb02ac4ed9dbb2ea1c8fe7870920abe6da47db832be19823b8103d",
      "reviewed_dependencies": []
    },
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
    }
  ],
  "relations": [
    {
      "relation": "related",
      "to": {
        "record_id": "OBJ-evidence"
      }
    }
  ],
  "source_review": {
    "reviewed_at": "2026-09-19T08:50:43.477581+00:00",
    "reason": "复核原字节归档规则允许 CRLF 保留；真实 Git 往返验证通过，公共导出和本机读取行为不变。",
    "body_sha256": "f8e2a8f835b6d55b8528adb93a6e4fdb37aec1a1200391766b45ae39632b4f81"
  }
}
---

# 记录、绑定与语义关系


项目维护者交付 project.yaml、入口 map.md，以及真正需要独立维护的记录。已经有正式需求书时，可绑定它的唯一标题或表格编号；不要再抄一份完整规格。新的独立记录带稳定 ID、类型、标题及所需状态与来源。

字段的唯一完整约定在 [资产模型](../../../../../../maintain-project-map/references/asset-model.md)。本页帮助理解边界：文件夹服务人读分组，ID 服务长期定位，提供/消费关系表达实际协作，正文链接只帮助阅读。

同一语义关系只声明一次；读取时归一已知反向写法，保留不同版本和角色。一个模块使用某个接口，不说明它的所有功能都调用该接口。实现记录与验证记录分别保存，见 [[OBJ-evidence]]。

已知使用方是 [[MOD-records|记录引擎]]、[[MOD-document-navigation|目录与链接]]、[[MOD-reader|阅读生成]]。绑定标题失效或 ID 重复时修复来源/绑定，不能用旧导出掩盖当前错误。

说明归档使用独立的 documentation 状态，保留原 ID 和功能/需求 status。归档的外部绑定从已保存的记录快照读历史，不再依赖失效的原章节；普通读取只给出短定位，显式历史读取才展开原文。
