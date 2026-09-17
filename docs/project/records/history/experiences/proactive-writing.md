---
id: EXP-proactive-writing
kind: experience
task_id: HIST-proactive-history
title: 主动保存过程，同时保留模型按需读取
date: 2026-09-17
status: current
categories: [improvement, human-correction]
results: [adopted]
modules: [维护指引, 开发历程]
outcome: 地图内容更新触发历程维护；读取范围仍由模型自主选择。
summary: 将写入职责与读取策略分别约束，避免“按需查询”被误解为“只有提醒才记录”。
applicability: 同时面向开发者和 LLM 的项目地图维护，不意味着所有日志都必须复制或预载。
coverage_note: Codex 根据本任务用户要求与实际规则修改整理，复用所属任务来源；无独立实验或失败结论。
related_records: [REQ-development-history, IMP-development-history]
---

# 主动保存过程，同时保留模型按需读取

用户要求每次更新地图主动维护历程。原来的按需读取目标仍然成立，但不能代替写入职责：没人记录新经验，以后也就没有材料可以按需查。

[查看依据：这次要求](history-event:EVT-61d74a2c78af085721ad)

采用的规则是：本次更新交付前同步过程，同一任务续写；经验正文共用，原始依据只保存定位。模型仍可选择不读旧历史，或只查询需要的片段。小改动简记，纯导出不重复记账。

[查看依据：规则修改](history-event:EVT-722252f9d4dd21d5cc0c)

此经验说明提示职责的分配，不证明以后每个任务都会自动遵循。没有来源的原因和失败不得补造。
