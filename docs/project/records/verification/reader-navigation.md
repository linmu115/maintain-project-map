---
id: VER-reader-navigation
kind: verification
title: 模块目录与文档导航检查
status: current
summary: 80 项运行检查及 Skill 格式检查通过；真实浏览器核查模块互跳、源码阅读、搜索和连续文档定位。
relations:
  - relation: verifies
    to: {record_id: IMP-reader-navigation}
---

# 模块目录与文档导航检查

2026-09-16：发布仓库 tests 48 项通过，Skill 内 tests 32 项通过；quick_validate 通过。新增通用工作流场景覆盖任意层级目录、绑定既有章节、标准/Wiki 链接、标题重复消歧、源码行定位、范围外文件不打包、来源变化及关系版本/角色保留。不是只用 DSH 固定 ID 做字符串匹配检查。

真实 Codex In-app Browser 在 DSH–Obsidian revised 页面完成 Core 概览 → Sticker 接入 → Core Client → 原始源码阅读，并核查浏览器返回、搜索祖先目录、过滤外目标跳转及 C 模式跨文档定位。截图确认白色/黑色风格、正文链接和独立滚动。模块图的默认缩放与原生源图保持原范围。

未执行插件功能开发、双应用运行或有无地图的多轮开发对照。地图建图耗时、文档规模和 token 数不作为本次改善结论。运行检查只能支持本次机械行为；未来模型的语义判断和后续开发收益仍需相应证据。
