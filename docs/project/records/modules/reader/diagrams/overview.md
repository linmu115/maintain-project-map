---
{
  "id": "MOD-archify",
  "kind": "module",
  "title": "原生图接入与交互适配",
  "status": "current",
  "summary": "调用固定版本 Archify 的校验、交付与图内交互；本 Skill 负责图源登记、记录绑定、嵌入样式和页面往返。",
  "aliases": [
    "Archify 原生图与适配嵌入"
  ],
  "sources": [
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
    },
    {
      "path": "maintain-project-map/references/archify-authoring.md",
      "role": "skill-source-authority",
      "workspace_id": "source",
      "reviewed_sha256": "cea5832f1c7aba661ecf647f35edd6677b6a1e5025a45dd7cb3f0ac6497a917e",
      "reviewed_dependencies": []
    },
    {
      "path": "maintain-project-map/assets/vendor/archify/ATTRIBUTION.md",
      "role": "skill-source-authority",
      "workspace_id": "source",
      "reviewed_sha256": "1219e095b581cacf336d91943de62fc1ad7d6438241cf4a3ce5eb25c94b02155",
      "reviewed_dependencies": []
    },
    {
      "path": "maintain-project-map/scripts/canvas_adapter.py",
      "role": "skill-source-authority",
      "workspace_id": "source",
      "reviewed_sha256": "95ba849e4b7d90f8f072e347665470865e2331dfd1e2d3ad284ebcacfbd53280",
      "reviewed_dependencies": []
    },
    {
      "path": "maintain-project-map/assets/diagram-records.js",
      "role": "skill-source-authority",
      "workspace_id": "source",
      "reviewed_sha256": "99c1dde3809c661661a545234d639ea80edc170ec576ad040d05d441d4438c73",
      "reviewed_dependencies": []
    }
  ],
  "relations": [
    {
      "relation": "provides",
      "to": {
        "record_id": "IF-native-diagram"
      }
    },
    {
      "relation": "implements",
      "to": {
        "record_id": "REQ-native-archify"
      }
    }
  ],
  "source_review": {
    "reviewed_at": "2026-09-19T08:47:36.681089+00:00",
    "reason": "核对新增公共静态导出和归档 Git 原字节保护；147 项完整回归与后续 16 项专项通过。其他来源仅统一 LF，Git 内容差异确认未改逻辑，保留原说明并更新跨系统可复用基线。",
    "body_sha256": "1896ca6c256440d490b4ef27eb62152e1a8c59dd47ef01e93a1b918187d63e5b"
  }
}
---

# 原生图接入与交互适配


结构和流程由作者维护为原生 JSON。[[IF-native-diagram|图源接入约定]]把它们登记到地图，并将节点关联到相关记录；同一记录可对应多个图节点。Archify 原生核心是捆绑的第三方依赖，本模块维护调用和阅读适配。

[archify_adapter.py](../../../../../../maintain-project-map/scripts/archify_adapter.py) 调用捆绑 Archify 的 deliver，核对源与产物摘要，保留原版 HTML 和黑白嵌入版。A/B 外壳负责文档导航；图内搜索、上游/下游、路径与引导沿用原生运行时。

原生代码固定版本及许可见 [Archify 归属说明](../../../../../../maintain-project-map/assets/vendor/archify/ATTRIBUTION.md)。更换上游版本要核对图 schema、交付回执和嵌入交互；不能把项目记录生命周期与 Archify 的状态机图混同。

图失败时展示诊断，正文继续可读。原生校验通过只说明所检查的格式/交付范围，不能证明产品功能满足需求。组合图要表达真实内部功能、边界及接口，不能仅列插件名称。

语义护照承载原“图节点与项目记录”的条目按钮，外层不再重复显示映射抽屉。节点与记录一对多绑定继续复用同一清单；图定位链接调用同一个原生相机，返回还原上一视野，见 [[IMP-passport-updates-history]]。
