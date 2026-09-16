---
id: MOD-guidance
kind: module
title: 按需维护与解释
status: current
summary: 模型按当前问题选用指引，维护需求、设计和历史，而不是每轮执行一套固定流程。
sources:
- path: ../../maintain-project-map/SKILL.md
  role: skill-source-authority
- path: ../../maintain-project-map/references/composite-projects.md
  role: skill-source-authority
- path: ../../maintain-project-map/references/lifecycle.md
  role: skill-source-authority
relations:
- relation: implements
  to:
    record_id: REQ-maintenance
- relation: implements
  to:
    record_id: REQ-cost
- relation: provides
  to:
    record_id: IF-skill-use
---

# 按需维护与解释


这个模块决定“此刻需要留下什么认识”。新需求有明确范围时记录要求和来源；决定落地后解释原因；相关实现完成后更新实际行为；过时功能与失败探索分别整理。没有新增长期事实时，可以不写地图。

入口是 [SKILL.md](../../../../../maintain-project-map/SKILL.md)。详细规则按任务分到资产格式、组合项目、生命周期、检索、阅读与评估参考资料；不会要求模型每轮加载全部参考文件。

整理组合项目时，先按用户确认的范围和成员声明确定边界，再按职责与接口选择层级。协议依赖不自动成为父子模块；已有独立地图的外部提供方保留自己的内部结构，本地图说明自己实际接入的能力并链接目标身份。具体指引见 [[IMP-composite-guidance]]。

对话仍发生在原会话里，页面负责阅读。使用方式和边界见 [[IF-skill-use]]；为什么把权威记录与可重建页面分开，见 [[DEC-on-demand]]。
