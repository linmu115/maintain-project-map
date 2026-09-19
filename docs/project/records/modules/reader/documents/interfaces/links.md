---
{
  "id": "IF-document-links",
  "kind": "interface",
  "title": "文档链接与章节定位",
  "status": "current",
  "summary": "普通相对链接与 Wiki ID 共用记录身份；标题重名不猜目标，原资料读取有明确范围。",
  "sources": [
    {
      "path": "maintain-project-map/references/reading-and-interaction.md",
      "role": "skill-source-authority",
      "workspace_id": "source",
      "reviewed_sha256": "90ad414c114081488af3fad36abbe8bdf18994b7fa4161a8fde5ba13af2a8278",
      "reviewed_dependencies": []
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
    },
    {
      "path": "maintain-project-map/scripts/reader_markdown.py",
      "role": "skill-source-authority",
      "workspace_id": "source",
      "reviewed_sha256": "9c040c241e23ad0e084b5803f12901abfee65273dce0b881ae74a9352290cd39",
      "reviewed_dependencies": []
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
    "reviewed_at": "2026-09-19T08:50:31.278664+00:00",
    "reason": "复核原字节归档规则允许 CRLF 保留；真实 Git 往返验证通过，公共导出和本机读取行为不变。",
    "body_sha256": "fadd0d39ef06c28cc43f1bec2ac5d175ea6bf804f0288ef555b3a10a95d9043c"
  }
}
---

# 文档链接与章节定位


作者可以写标准 Markdown 相对链接，也可以用 `[[记录ID#章节|显示名称]]`。例如主页的 [[IF-map-query|查询说明]] 直接指向本地图的一份接口介绍，而不会复制正文。

稳定 ID 不随文件移动改变；相对路径在移动时仍需修正。Wiki 可匹配唯一标题、别名或文件名；重名时保留未解析提示，作者用 ID 或完整路径消歧。具体规则以 [阅读与交互](../../../../../../../maintain-project-map/references/reading-and-interaction.md) 为唯一完整说明。

原资料要在来源元数据中声明，正文再链接它。当前阅读快照支持常见文本文件并设单文件 2 MiB 上限；未知、失效或超出范围的目标保留定位信息。它没有任意文件浏览服务。

此接口的使用方是记录作者与 A/B 阅读页面。链接只表示“到这里读”，不证明提供/消费、调用顺序或数据归属。

旧 ID、旧 Markdown 路径在说明归档后先到短定位，再打开当前说明或独立归档原文。若共享原始资料包含已归档章节，整份原文快照会停止展示，保留具体记录入口，避免旧说明混入当前阅读。
