---
id: REQ-ethical-reader
kind: requirement
title: Accessible & Ethical 阅读风格与完整引导布局
status: superseded
summary: Ethical 视觉方向已由用户撤回，改用原风格和黄蓝白配色；引导布局修复保留。
---

# Accessible & Ethical 阅读风格与完整引导布局

后续修订：用户要求恢复原风格，视觉方向由 REQ-yellow-blue-reader 替代。下文保留当时要求，不能作为当前样式规格；引导裁切修复继续保留。

2026-09-15，用户要求使用 UI Skill 中的 Ethical 风格重写维护地图样式，并指出截图中的引导标题、轨迹、操作和章节挤在一起。

采用 ui-ux-pro-max 数据库中已核对的 accessible-and-ethical（Accessible & Ethical）风格。通用设计系统搜索推荐了 Swiss 风格，因此不采用该自动匹配作为本次风格依据。

- 延续浅色、低饱和阅读界面，正文与主要控件为 16px，辅助信息为 14px；使用深色文字、清楚的分隔线、3px 键盘焦点及至少 44px 的主要操作目标。
- A/B/C 共享一套颜色和字号规则；保留独立滚动和文档内点选图形操作。提问继续在会话中进行。
- 原生引导章节和播放功能保留，阅读引导默认折叠。展开后文字与章节按实际高度排布，内容较长时整个引导内容区可滚动，不能把每一行压缩后裁切。
- 原生图的节点和图源坐标保持不变；只适配阅读器样式和引导容器。

来源：当前任务的用户请求与截图 codex-clipboard-c6b781cd-d0b6-4d89-a07a-252d533514cf.png。截图问题来自此前下游 28dvh 高度限制与上游网格、内层 overflow:hidden 的叠加。

本要求不宣称已通过完整无障碍标准认证；实际检查范围单独记录。
