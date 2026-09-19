---
{
  "id": "IF-update-record",
  "kind": "interface",
  "title": "一次迭代怎样成为更新记录",
  "status": "current",
  "summary": "明确请求留存后新增有日期的 update 文档；图链接使用图类型和稳定节点 ID。",
  "sources": [
    {
      "path": "maintain-project-map/references/update-records.md",
      "role": "skill-source-authority",
      "workspace_id": "source",
      "reviewed_sha256": "f4360b98d246dba1642cfe5961d232496fcba6ce8f08a9fdd16318f7e7f1b91f",
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
    },
    {
      "path": "maintain-project-map/scripts/reader_content.py",
      "role": "skill-source-authority",
      "workspace_id": "source",
      "reviewed_sha256": "8ad021637190777cb58a5b02b1ed8945031c2d7575576bb977cd32242dafc80e",
      "reviewed_dependencies": [
        {
          "path": "maintain-project-map/scripts/document_archive.py",
          "sha256": "da4f6deaadde3da10c228a46f6ce02d3f5e2e2d3a970664420b05685f622f9e4"
        },
        {
          "path": "maintain-project-map/scripts/reader_markdown.py",
          "sha256": "9c040c241e23ad0e084b5803f12901abfee65273dce0b881ae74a9352290cd39"
        }
      ]
    }
  ],
  "source_review": {
    "reviewed_at": "2026-09-19T08:50:40.438025+00:00",
    "reason": "复核原字节归档规则允许 CRLF 保留；真实 Git 往返验证通过，公共导出和本机读取行为不变。",
    "body_sha256": "25d3c2ed3408d6a6efd765e5589ac64e09b27f11da66ed94c4d74e77e9c85a6a"
  }
}
---

# 一次迭代怎样成为更新记录

输入是开发者明确提出的留存请求和这次迭代已完成的功能变化。输出是一份带唯一 ID、kind: update、title、date、summary 及正文的 Markdown；date 必须是 YYYY-MM-DD。来源指出这次请求，功能细节和验证证据按需链接原记录。

正式格式及例子由 [Skill 的按需说明](../../../../../../../maintain-project-map/references/update-records.md) 提供，本页是面向使用者的入口；不另外维护一份矛盾的 schema。

正文可以写 `[交接位置](map-node:workflow/实际节点ID)` 或 architecture 对应链接。作者先核查图源中的实际 ID；页面遇到已删除的节点会提示，不能把别的节点冒充旧位置。原记录普通链接仍按 [[IF-document-links|文档链接约定]] 处理。

已接入：[[MOD-updates|更新记录阅读]]读取这些文档；[[MOD-document-navigation|文档导航]]把图链接转为当前页定位；[[MOD-archify|图适配]]调用原生相机居中，语义护照中的按钮可打开正式项目条目。
