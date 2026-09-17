---
id: EXP-evidence-boundaries
kind: experience
title: 如何核对日志按需读取的范围与失效边界
date: 2026-09-17
task_id: HIST-source-reuse
categories: [verification]
results: [passed]
modules: [来源检索, 阅读器]
outcome: 所选实例完成索引与导出核查，测试覆盖来源丢失和改变；不宣称测出了整场会话的 token 降幅。
summary: 通过检查实际导出、有限读取及来源不可用时的行为，区分“文件变小”和“模型少读了多少内容”。
applicability: 当时的 source-references 实现和 MRS 实例；后续修改仍须按受影响行为核查。
coverage_note: 复用 HIST-source-reuse 的测试改动、实例检查与交付说明，只概括公开验证范围。
related_records: [VER-development-history, IF-history-query]
---

# 如何核对日志按需读取的范围与失效边界

## 要核对的问题

去掉副本后，仍需知道证据能否读取、原文改变时是否被发现，以及查询是否仅返回需要的部分。文件缩小只能说明存储变化，不能替代对读取行为的检查。

## 做过的检查

检查增加了从原会话还原分段内容、导出目录不生成原文片段、来源被移走或改变时明确报错等情况。来源丢失使用临时测试材料模拟。这里的错误提示是预期行为，不应记成一次尚未修复的线上故障。

[查看依据：检查实现与配对返回](history-event:EVT-42e66b2198c17828886b)

真实实例核查结果为 126 个事件定位、零个保存原文的字段、一个 20096 字节的页面事件目录；重新索引同一来源返回 unchanged。

[查看依据：真实实例的核查结果](history-event:EVT-f1933799e52fc570e4cb)

## 验证支持什么结论

这些检查支持当时实例的来源复用、有限读取和明确失效行为。最终交付说明记录了 87 项自动检查及实际页面验证，完整覆盖与局限由当前验证记录维护。没有测量或承诺本任务累计输入 token 的减少量，也没有证明所有以后生成的摘要都忠实。

[查看依据：当次验证与交付范围](history-event:EVT-4776191ba9e4f33242cd)
