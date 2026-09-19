---
{
  "id": "MOD-document-navigation",
  "kind": "module",
  "title": "目录、Markdown 与文档跳转",
  "status": "current",
  "summary": "文件夹成为人读目录，Markdown 和 Wiki 链接连接记录、章节及明确声明的原资料。",
  "sources": [
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
    },
    {
      "path": "maintain-project-map/references/reading-and-interaction.md",
      "role": "skill-source-authority",
      "workspace_id": "source",
      "reviewed_sha256": "90ad414c114081488af3fad36abbe8bdf18994b7fa4161a8fde5ba13af2a8278",
      "reviewed_dependencies": []
    }
  ],
  "relations": [
    {
      "relation": "consumes",
      "to": {
        "record_id": "IF-record-data"
      }
    },
    {
      "relation": "provides",
      "to": {
        "record_id": "IF-document-links"
      }
    }
  ],
  "source_review": {
    "reviewed_at": "2026-09-19T08:50:34.215938+00:00",
    "reason": "复核原字节归档规则允许 CRLF 保留；真实 Git 往返验证通过，公共导出和本机读取行为不变。",
    "body_sha256": "5cfbaa3c62f4a9e9f8b0d9f04785d7c5e770bdedfd112cb10fa58d6200915737"
  }
}
---

# 目录、Markdown 与文档跳转


[reader_content.py](../../../../../../maintain-project-map/scripts/reader_content.py) 根据真实目录生成 B 层级，并建立路径与记录身份的对应；[reader_markdown.py](../../../../../../maintain-project-map/scripts/reader_markdown.py) 复用 Mistune 解析语法。模块概览提供文件夹的可读名称，搜索保留并展开祖先目录。

提供方正文可跳到消费方接入说明，再返回唯一合同。原始合同或源码只在直接引用且已声明时打包为阅读快照；页面显示来源和独立指纹，不把它变成新的权威记录，也不递归抓取整仓库文档。

链接写法、重名处理和移动文件后的规则见 [[IF-document-links]]。这部分服务阅读导出；LLM 的常规查询仍使用原记录。图形内搜索与路径查询交给 [[MOD-archify|Archify]]，没有重复编写图算法。

页面历史保存上一阅读状态，包含搜索、目录与文档滚动位置；图中的相机和所选卡片通过嵌入桥接恢复。图位置链接可以从更新或普通正文进入相应图并居中卡片，具体使用见 [[IMP-passport-updates-history]]。

当前目录和搜索默认排除归档说明；包含历史时显示短定位，旧正文仅在独立归档页展开。生成的“源码入口与依赖”小栏目沿用目录结构；来源变化的记录显示待复核提示和路径。
