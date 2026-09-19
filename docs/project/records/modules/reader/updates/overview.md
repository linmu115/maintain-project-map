---
{
  "id": "MOD-updates",
  "kind": "module",
  "title": "开发者选择留存的更新记录",
  "status": "current",
  "summary": "用户明确要求时留存一轮功能迭代，按日期阅读并跳到相关图卡片。",
  "sources": [
    {
      "path": "maintain-project-map/references/update-records.md",
      "role": "skill-source-authority",
      "workspace_id": "source",
      "reviewed_sha256": "f4360b98d246dba1642cfe5961d232496fcba6ce8f08a9fdd16318f7e7f1b91f",
      "reviewed_dependencies": []
    },
    {
      "path": "maintain-project-map/assets/reader.html",
      "role": "skill-source-authority",
      "workspace_id": "source",
      "reviewed_sha256": "d8a8efae8efe5b4555fa8d896885a0bfde2b444f9f19f5456141e998bb1ed590",
      "reviewed_dependencies": []
    }
  ],
  "relations": [
    {
      "relation": "contained_by",
      "to": {
        "record_id": "MOD-reader"
      }
    },
    {
      "relation": "provides",
      "to": {
        "record_id": "IF-update-record"
      }
    },
    {
      "relation": "implements",
      "to": {
        "record_id": "REQ-passport-updates-history"
      }
    }
  ],
  "source_review": {
    "reviewed_at": "2026-09-19T08:47:56.718776+00:00",
    "reason": "核对新增公共静态导出和归档 Git 原字节保护；147 项完整回归与后续 16 项专项通过。其他来源仅统一 LF，Git 内容差异确认未改逻辑，保留原说明并更新跨系统可复用基线。",
    "body_sha256": "f2aa22b825ff8f37170fd7538293083948e8d63a3769c4b17996abaf1121fdee"
  }
}
---

# 开发者选择留存的更新记录

当你完成一次值得记住的功能迭代，并在会话中明确提出“把这次迭代加入更新记录”，模型才写一条更新。普通开发、地图整理和页面刷新不自动追加。

左侧“更新记录”按日期倒序显示各次迭代，打开一条能读到改变了什么功能、必要的设计背景与限制。与图结构有关时，通过正文链接在本页跳到相应图，并把卡片放在画布中央。顶栏返回可以回到原来的更新位置。

条目保存于同一地图 records/updates 下，kind 为 update，不复制实现和验证文档。格式与写入触发只维护在 [[IF-update-record|更新记录约定]]。阅读器用本地数据展示，日期参与检索；没有常驻写入服务或 LLM 自动生成步骤。
