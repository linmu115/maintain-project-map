---
{
  "id": "IMP-map-catalog",
  "kind": "implementation",
  "title": "本机项目地图目录与名称查找",
  "status": "current",
  "summary": "在原位置注册表上增加名称、别名、分页检查和默认位置，主动登记现有项目地图。",
  "relations": [
    {
      "relation": "implements",
      "to": {
        "record_id": "IF-project-location"
      }
    }
  ],
  "sources": [
    {
      "path": "maintain-project-map/scripts/map_catalog.py",
      "role": "implementation",
      "workspace_id": "source",
      "reviewed_sha256": "626732649f0317a78d49974744029d722d3ab10eb6c41b818e5bb168dd9a404c",
      "reviewed_dependencies": [
        {
          "path": "maintain-project-map/scripts/project_map.py",
          "sha256": "67aee0a424ef3fe0019e0db34fbc97d9168e2edc6e35ee107faef86a63b49f6a"
        }
      ]
    }
  ],
  "source_review": {
    "reviewed_at": "2026-09-19T08:47:20.233334+00:00",
    "reason": "核对新增公共静态导出和归档 Git 原字节保护；147 项完整回归与后续 16 项专项通过。其他来源仅统一 LF，Git 内容差异确认未改逻辑，保留原说明并更新跨系统可复用基线。",
    "body_sha256": "16e39c87ffe0b9237281618551dedefc863a6d058b16a17cc0ea155b7b9de15c"
  }
}
---

# 本机项目地图目录与名称查找

2026-09-17 新增轻量目录命令。注册时读取清单身份与名称，保留别名和多个位置；使用已有独占写锁与原子写入。名称查询只读取当前候选页的清单，不调用全图读取器，不读取日志正文。

明确的工作树优先于默认位置。默认位置不可用时保留候选并要求核对，不用文件修改时间猜测权威副本。原 ID 解析器支持同一默认字段，跨项目链接沿用现有协议。

本机登记了 10 个项目、11 个工作位置；项目地图 Skill 源稿与发布仓库共享一个身份，当前源稿明确设为默认。每台机器的实际路径保存在用户目录的 .codex/project-maps/registry.json，未打包进 Skill。盘点说明位于同目录的 inventory.md。

用户修正了初始范围：本次只维护项目地图，不纳入 MRS 研究地图。研究地图适配试写在安装前移除，未修改 B/C 题或其他研究文件。MRS 软件开发地图仍按普通项目登记。过程见 [[HIST-map-catalog]]，验证见 [[VER-map-catalog]]。
