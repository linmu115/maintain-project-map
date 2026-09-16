---
id: MOD-session
kind: module
title: 查回会话中的可见消息
status: current
summary: 从明确指定的 Codex JSONL 中查找消息，返回身份、位置和读取范围。
relations:
- relation: implements
  to:
    record_id: REQ-source
- relation: provides
  to:
    record_id: IF-visible-session
sources:
- path: ../../maintain-project-map/scripts/search_session.py
  role: skill-source-authority
- path: ../../maintain-project-map/references/retrieval.md
  role: skill-source-authority
---

# 查回会话中的可见消息

优先使用会话宿主已有的读取工具。需要核对原记录时，本地脚本只处理明确指定文件里的可见消息，默认查用户消息，不扫描所有任务。

支持中文关键词、消息 ID、行号与长消息分段。结果给出原身份、文本摘要校验值和准确覆盖范围；模型仍需核对邻近上下文与后续修订。

脚本不暴露内部推理与工具载荷，也不把未知格式当作可见消息。其他宿主的数据使用各自适配方式。

代码入口：maintain-project-map/scripts/search_session.py。


输入范围、可见内容和返回定位信息见 [[IF-visible-session]]。
