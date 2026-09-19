---
{
  "id": "MOD-http",
  "kind": "module",
  "title": "本机阅读服务",
  "status": "current",
  "summary": "启动或复用只读预览，为已生成地图返回本机 HTTP 地址。",
  "sources": [
    {
      "path": "maintain-project-map/scripts/serve_map.py",
      "role": "skill-source-authority",
      "workspace_id": "source",
      "reviewed_sha256": "91382ef2456f566e09f80c4a92d5d1bed3e79416f43afb78cc82dc8a2a8ed96b",
      "reviewed_dependencies": [
        {
          "path": "maintain-project-map/scripts/development_history.py",
          "sha256": "556b088e8d4562f9440a5130f8b1731e70d4ccc5e75c1926be72b8ad7026f8ca"
        },
        {
          "path": "maintain-project-map/scripts/system_map.py",
          "sha256": "c591323f312d35a7428a1e92983f24d2aac23dba3f980cf6bf7838a4856be979"
        }
      ]
    },
    {
      "path": "maintain-project-map/references/operations.md",
      "role": "skill-source-authority",
      "workspace_id": "source",
      "reviewed_sha256": "d7c4d10f51271240631bfa6155d8841e9d6524a80cfdf04df54ef409b955f3a6",
      "reviewed_dependencies": []
    }
  ],
  "relations": [
    {
      "relation": "provides",
      "to": {
        "record_id": "IF-http-preview"
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
    "reviewed_at": "2026-09-19T08:47:51.068360+00:00",
    "reason": "核对新增公共静态导出和归档 Git 原字节保护；147 项完整回归与后续 16 项专项通过。其他来源仅统一 LF，Git 内容差异确认未改逻辑，保留原说明并更新跨系统可复用基线。",
    "body_sha256": "0b7733d2e185aea060dcd6402afda855aaa0f1d638ef432035d6b5feaa82154b"
  }
}
---

# 本机阅读服务


[serve_map.py](../../../../../../maintain-project-map/scripts/serve_map.py) 接收已经存在的 HTML 入口，返回本机地址。相同输出位置的服务仍在运行时复用；内容变更后导出并刷新即可。退出或重启后重新启动，地址可能变化。

服务只读指定导出文件和相邻图形，不浏览原始项目目录，不后台维护地图，不调用模型。默认空闲 8 小时退出，可通过状态/停止命令管理。操作说明见 [[IF-http-preview]]。

服务回执属于本机运行状态，不能拿 URL 当项目长期身份。持久位置由 [[MOD-locate|项目登记]] 管理。服务不可用时 HTML 仍是可选离线交付，状态须分别说明。

归档原文以本次导出登记的独立 HTML 提供；服务仍只开放白名单资源，不因增加归档阅读而开放原始项目目录。
