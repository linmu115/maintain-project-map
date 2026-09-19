---
{
  "id": "MOD-reader",
  "kind": "module",
  "title": "阅读页面：文档、图与本机入口",
  "status": "current",
  "summary": "以同一份记录生成 A/B 页面，目录与正文互链，图形复用 Archify；页面交互不调用模型。",
  "sources": [
    {
      "path": "maintain-project-map/scripts/render_map.py",
      "role": "skill-source-authority",
      "workspace_id": "source",
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
          "sha256": "a688ba62ab937a48a5dd16b6964e79ba298260fcd9be87af977128ee460fb5ef"
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
      "path": "maintain-project-map/assets/reader.html",
      "role": "skill-source-authority",
      "workspace_id": "source",
      "reviewed_sha256": "d8a8efae8efe5b4555fa8d896885a0bfde2b444f9f19f5456141e998bb1ed590",
      "reviewed_dependencies": []
    },
    {
      "path": "maintain-project-map/assets/reader.css",
      "role": "skill-source-authority",
      "workspace_id": "source",
      "reviewed_sha256": "6f2b58c2be86a626cb41dab4e11e2ad892cec3a119a73265bbde5fd07c8222bb",
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
        "record_id": "IF-map-query"
      }
    },
    {
      "relation": "contains",
      "to": {
        "record_id": "MOD-document-navigation"
      }
    },
    {
      "relation": "contains",
      "to": {
        "record_id": "MOD-archify"
      }
    },
    {
      "relation": "contains",
      "to": {
        "record_id": "MOD-http"
      }
    },
    {
      "relation": "implements",
      "to": {
        "record_id": "REQ-reader-navigation"
      }
    },
    {
      "relation": "implements",
      "to": {
        "record_id": "REQ-canvas-reader"
      }
    },
    {
      "relation": "implements",
      "to": {
        "record_id": "REQ-linear-reader"
      }
    },
    {
      "relation": "implements",
      "to": {
        "record_id": "REQ-http-entry"
      }
    }
  ],
  "source_review": {
    "reviewed_at": "2026-09-19T08:50:37.302650+00:00",
    "reason": "复核原字节归档规则允许 CRLF 保留；真实 Git 往返验证通过，公共导出和本机读取行为不变。",
    "body_sha256": "4217b669a21451718df1f80cd29fc597985f2dacd33163538199b307625dc804"
  }
}
---

# 阅读页面：文档、图与本机入口


## 开发者怎样阅读

项目概览分别展示说明与规格、整体组织和功能路径；项目条目围绕一个对象阅读说明、现状和关系。顶栏固定，侧栏与正文独立滚动，默认白色/黑色风格。搜索和目录展开在本地完成。

点击文档内的图窗口后才切换为画布缩放、拖动；点击外部返回文档滚动。边框和视窗固定，只移动内部图形。提问继续通过当前会话，阅读器不另设输入框。

## 内部模块与交接

- [[MOD-document-navigation|目录与正文链接]]：从 records 层级生成目录，用 Mistune 解析 Markdown，并按 ID、章节和已声明来源跳转。
- [[MOD-archify|原生图适配]]：调用已有 Archify 校验/交付，再保留原版和黑白嵌入副本；图节点与记录单独绑定。
- [[MOD-updates|更新记录阅读]]：展示开发者明确选择留存的功能迭代；没有更新时显示空状态。
- [[MOD-http|本机预览]]：只提供已生成页面和图形，复用仍在运行的阅读地址。

生成入口是 [render_map.py](../../../../../maintain-project-map/scripts/render_map.py)，行为约定在 [阅读与交互](../../../../../maintain-project-map/references/reading-and-interaction.md)。记录由 [[IF-map-query|记录引擎]] 加载，图源出错时保留正文和诊断。修改源码后要重新导出并刷新，旧页面只是原来的快照。

语义护照直接连接项目条目，正文图链接居中卡片，顶栏返回恢复图与文档位置，见 [[IMP-passport-updates-history]]。更新条目的写入需要开发者明确请求；生成页面本身不会创建迭代记录。

源码静态发现只增加“源码入口与依赖”小文档栏目；来源发生变化时在条目前显示待复核信息。归档说明默认只保留定位和后继，历史正文分离到明确点击打开的归档页，不进入主 HTML 或 docs.json 的正文。

公开仓库可用 [[IMP-public-map|在线地图发布]] 生成静态阅读站点。文档与图沿用上述入口，开发历程保留叙述并说明原始依据仅本机可用；公共导出不会启动本机服务。
