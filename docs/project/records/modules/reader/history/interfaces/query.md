---
id: IF-history-query
kind: interface
title: 开发历程的候选、事件与展开读取
status: current
summary: 按类别、结果、模块自主查询经验或任务摘要，再展开所选任务的配对原文；所有读取都有范围。
sources:
  - path: ../../maintain-project-map/references/development-history.md
    role: query-contract
---

# 开发历程的候选、事件与展开读取

例如模型正在处理一个可读性错误，可以先查哪些历史任务碰到过类似问题，读相关段落，再决定是否需要当时的检查结果。它不需要先导入整段会话或遵守固定回查流程。

也可以直接用 `development_history.py cases` 查询经验，按工作类别、包含的尝试结果、模块和所属任务筛选。默认返回至多五个去重摘要、适用条件和来源位置；按记录 ID 读经验正文，再用所属 task_id 查询具体事件。经验跨类别共用身份，不会因多个导航入口而重复返回。

`development_history.py search` 返回少量任务候选，不打开原会话。`events --task --query` 在本机读取该任务所索引的公开文本，向调用方只返回有限命中摘录。`read --task --event` 返回目标事件、配对调用/返回及有限邻居，每项标明截断、下一偏移和来源指纹。旧版本失败结果不产生当前禁令。

同一工具调用通过宿主 `call_id` 配对；配对缺失或存在歧义会披露，顺序邻居不代表因果。公开字段采用白名单，隐藏推理和系统指令不进入来源索引。参数范围、样例和存储约定由 Skill 的 [开发历程说明](../../../../../../../maintain-project-map/references/development-history.md) 维护。

HTML 共用相同来源索引，经本机预览服务只请求已绑定事件的有限片段。清单不提供任意文件读取；原会话缺失、行指纹改变或捕获索引改变时拒绝返回不可靠内容。静态分享仅支持叙述阅读，原始依据仍依赖本机宿主会话。
