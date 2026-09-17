---
id: HIST-proactive-history
kind: history
title: 让地图更新主动带上开发历程
date: 2026-09-17
status: current
modules: [维护指引, 开发历程]
outcome: 已修改入口和详细规则并同步安装版本；主动写入本次过程，保留自主查询。
summary: 用户指出地图更新不能依赖再次提醒才记历程，本次将主动维护设为 Skill 职责，同时限制重复记录和上下文膨胀。
applicability: maintain-project-map 的地图内容维护；不涉及后台采集器和阅读器行为变更。
coverage_note: 2026-09-17 由 Codex 整理。公开来源覆盖本次要求至首次规则修改、安装同步和格式检查，行 365–416，共 17 个事件定位、7 组调用与返回；后续历程整理和 HTML 导出未索引，结果以当前文件和检查记录为准。
history:
  path: history/proactive-history-final-20260917
  sha256: b82092dc5a24df814beec7a2bc70c75f7b123c6352088e49c142fc80735fdcd9
  capture_sha256: 787a2173ac6984c85ce76ed6a7518438db6521abefa3695f6a144e607bac6923
related_records: [REQ-development-history, IMP-development-history, MOD-development-history, VER-development-history]
---

# 让地图更新主动带上开发历程

## 问题与用户修正

此前入口主要在需要解释过程或查询经验时引导读取开发历程，没有明确要求地图更新后主动写入。用户提出每次更新地图时应让 LLM 主动同步，避免依赖再次提醒。

[查看依据：用户要求主动更新历程](history-event:EVT-61d74a2c78af085721ad)

## 调整与保留边界

入口增加交付前的主动同步职责，详细参考规定同一任务续写、短修订简记、有独立价值才提炼经验。只记录实际发生的问题、反馈和转折，不为每个命令生成任务，也不让“记录历程”递归生成另一份历程。

主动写入本次过程与读取旧历史分别处理：没有强制模型先读历史，不全量复制会话，不把工具载荷注入每次上下文。纯浏览、查询和内容不变的重新导出不产生重复记录。

[查看依据：入口、详细规则及自身地图的实际修改](history-event:EVT-722252f9d4dd21d5cc0c)

## 结果

规则已同步到源稿和已安装 Skill，需求、实现与模块说明同步更新。本任务也按新规则加入开发历程。它约束模型使用 Skill 时的维护动作，没有新增自动监听服务；未加载或未遵循 Skill 的执行不能由这份提示保证。

本次是明确要求驱动的规则修订，没有发生可据以记录的方案失败或实验回退。最终格式、来源绑定和导出核对见 [[VER-development-history|开发历程的检查范围]]。
