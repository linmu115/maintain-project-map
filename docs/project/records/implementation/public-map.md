---
{
  "id": "IMP-public-map",
  "kind": "implementation",
  "title": "在线地图发布",
  "status": "current",
  "summary": "从主分支自动生成公共静态地图，仓库首页点击即读；本机原始会话依据不随页面发布。",
  "progress": "implemented",
  "relations": [
    {
      "relation": "implements",
      "to": {
        "record_id": "REQ-public-map"
      }
    }
  ],
  "sources": [
    {
      "workspace_id": "source",
      "path": "maintain-project-map/scripts/render_map.py",
      "role": "implementation",
      "reviewed_sha256": "9c67374bd56a05b84f3e041f0708b494cf70e22fecf3c29993f67a5038a0ec55",
      "reviewed_dependencies": [
        {
          "path": "maintain-project-map/scripts/archify_adapter.py",
          "sha256": "1cb5a7341603996feccfc850ddf29daa4c3bfed62f398af47e53a1f6a66a6964"
        },
        {
          "path": "maintain-project-map/scripts/development_history.py",
          "sha256": "556b088e8d4562f9440a5130f8b1731e70d4ccc5e75c1926be72b8ad7026f8ca"
        },
        {
          "path": "maintain-project-map/scripts/document_archive.py",
          "sha256": "da4f6deaadde3da10c228a46f6ce02d3f5e2e2d3a970664420b05685f622f9e4"
        },
        {
          "path": "maintain-project-map/scripts/project_map.py",
          "sha256": "67aee0a424ef3fe0019e0db34fbc97d9168e2edc6e35ee107faef86a63b49f6a"
        },
        {
          "path": "maintain-project-map/scripts/public_export.py",
          "sha256": "645e9e44bca230bc78f707cd6de054904af4c7672d73329bcbea4b9d9029a1b7"
        },
        {
          "path": "maintain-project-map/scripts/reader_content.py",
          "sha256": "8ad021637190777cb58a5b02b1ed8945031c2d7575576bb977cd32242dafc80e"
        },
        {
          "path": "maintain-project-map/scripts/reader_markdown.py",
          "sha256": "9c040c241e23ad0e084b5803f12901abfee65273dce0b881ae74a9352290cd39"
        },
        {
          "path": "maintain-project-map/scripts/serve_map.py",
          "sha256": "91382ef2456f566e09f80c4a92d5d1bed3e79416f43afb78cc82dc8a2a8ed96b"
        },
        {
          "path": "maintain-project-map/scripts/source_inventory.py",
          "sha256": "9a955c3abda4b41beb79fc713b25c7e3093c2b1fa4844fc9980e7e2d18c22e90"
        },
        {
          "path": "maintain-project-map/scripts/system_map.py",
          "sha256": "c591323f312d35a7428a1e92983f24d2aac23dba3f980cf6bf7838a4856be979"
        }
      ]
    },
    {
      "workspace_id": "source",
      "path": "maintain-project-map/scripts/public_export.py",
      "role": "implementation",
      "reviewed_sha256": "645e9e44bca230bc78f707cd6de054904af4c7672d73329bcbea4b9d9029a1b7",
      "reviewed_dependencies": [
        {
          "path": "maintain-project-map/scripts/reader_content.py",
          "sha256": "8ad021637190777cb58a5b02b1ed8945031c2d7575576bb977cd32242dafc80e"
        }
      ]
    },
    {
      "workspace_id": "source",
      "path": ".github/workflows/project-map-pages.yml",
      "role": "publication",
      "reviewed_sha256": "cdc8f73f274476a690f84d2f3345188d0765a4724c19820e9554dd4cc01a49e8",
      "reviewed_dependencies": []
    }
  ],
  "source_review": {
    "reviewed_at": "2026-09-19T09:01:07.224678+00:00",
    "reason": "复核公共导出只清理路径元数据，保留斜杠开头的正文和源码注释；4 项公共导出检查通过。",
    "body_sha256": "9bb23d5f5e6101e36980a680d1addc32568412282012c0f579d7db98d2a44d1d"
  }
}
---

[打开在线地图](https://linmu115.github.io/maintain-project-map/)。它与仓库中这份地图共用记录、图源和稳定身份，支持文档目录、图节点跳转、返回和归档阅读。

主分支中的 Skill、地图、设计方案或相关研究资料变化时，GitHub Actions 用 Python 和 Node 构建并部署 GitHub Pages。生成页面作为站点产物；清单、Markdown、原生图源和确认归档的正文继续由 Git 维护。发布对应的提交可在 Actions 中核查。

公共导出使用 `--public-root` 明确指定资料边界，输出目录必须为空。声明资料超出根目录即停止，防止混入外部原文；生成元数据的本机路径转换为相对定位。该模式不扫描文档中的秘密，准备发布的正文仍须适合公开。

开发历程保留过程叙述，原始会话、事件索引和本机取证映射不导出。相关位置清楚显示“原始依据仅本机可用”，不让读者点击一个依赖维护者电脑的请求。普通本机阅读和 LLM 查询保持原有能力。系统地图进入本机项目的功能不适用于静态托管，应分别发布所需项目地图。

验证见 [[VER-public-map]]；当前能力与源码发现见 [[IMP-llm-context]]。
