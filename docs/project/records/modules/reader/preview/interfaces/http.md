---
{
  "id": "IF-http-preview",
  "kind": "interface",
  "title": "阅读入口与预览状态",
  "status": "current",
  "summary": "生成器交付 HTML 入口，预览服务返回可用地址或具体失败状态。",
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
  "source_review": {
    "reviewed_at": "2026-09-19T08:47:48.304674+00:00",
    "reason": "核对新增公共静态导出和归档 Git 原字节保护；147 项完整回归与后续 16 项专项通过。其他来源仅统一 LF，Git 内容差异确认未改逻辑，保留原说明并更新跨系统可复用基线。",
    "body_sha256": "edf35eb42bce6d3049063233e30614813ba28e73eb58ed7d1c2942612f79f303"
  }
}
---

# 阅读入口与预览状态


提供方是本机服务，使用方是阅读生成器和开发者。调用 start 提供已生成入口后，获得当前 URL 与服务状态；status 查询可用性，stop 停止这份阅读服务。完整命令例子以 [本地操作](../../../../../../../maintain-project-map/references/operations.md) 为准。

同一服务运行期间复用地址，刷新读取磁盘上的最新导出；它不会自动从原项目重新生成。页面更新与源记录维护是两个动作。无法启动服务时保留已生成文件，并明确说明没有可用 HTTP 地址。

长期链接应指向项目/记录 ID 与可解析的资料位置。本机 URL 只适合当前阅读，不是发布网站，也不是跨设备共享接口。

## 系统项目进入

系统地图的 __project 入口只接受当前清单明确收录的项目 ID，以及图、记录或节点身份。点击后检查目标当前状态，按需生成完整项目阅读页并在新标签页打开；不同系统可共用同一目标服务，生成过程按目标串行，原系统页保持。失效身份不猜选，失败页显示原因。

已导出的独立归档页通过资源登记允许访问；只接受本次导出列出的归档 HTML，未列出文件和原始归档目录不会因此开放。重新导出时资源清单随之更新。
