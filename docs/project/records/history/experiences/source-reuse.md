---
id: EXP-source-reuse
kind: experience
title: 用户指出重复日志后，改为复用原会话
date: 2026-09-17
task_id: HIST-source-reuse
categories: [improvement, human-correction]
results: [adopted]
modules: [开发历程, 来源检索]
outcome: 采用来源索引和按需读取，移除这次试做的重复原文。
summary: 用户把实现从过度保存来源拉回到轻量取证，同时明确磁盘占用和模型上下文需要分别判断。
applicability: 宿主仍保留原会话、地图只需回查选定事件的场景；不适用于要求脱离宿主独立保全全部证据的交付。
coverage_note: 从 HIST-source-reuse 中整理出用户纠偏、实现调整和实际迁移结果；下方三处原始依据覆盖这些判断。
related_records: [REQ-development-history, IMP-development-history, IF-history-query]
---

# 用户指出重复日志后，改为复用原会话

## 遇到了什么问题

第一版为便于核查保存了工具原文和导出片段。用户指出同样的记录已经存在于 Codex 会话，额外保存占空间，也容易让人担心整份日志会再次进入模型上下文。

[查看依据：用户怎样把方向拉回来](history-event:EVT-f9ccb323ce6b71bdd331)

## 怎样调整

实现接受了对重复存储的修正。地图保留过程叙述、关键事件定位和指纹，打开依据或显式查询时才读取原文。原方案具备回查能力，但在用户希望的成本约束下保存过多；不能把这次取舍推广成所有系统都不应保存原始证据。

[查看依据：公开说明的修正理由](history-event:EVT-aa05735ed9997b9418ba)

## 实际得到什么结果

工具返回记录该实例的来源文件从 659263 字节精简为 88702 字节的索引，删除 329 个生成片段。它证明了这次迁移的存储变化，不直接证明每轮模型输入节省了多少 token。

[查看依据：迁移前后实际数据](history-event:EVT-cde2749f67607564ed19)

## 以后怎样参考

当宿主已保存原始记录时，先判断需要的是检索入口还是独立档案，再选择保存方式。当前方式保留核查入口，但原会话不可用时，指纹和索引不能还原原文。模型是否读取仍由任务需要决定。
