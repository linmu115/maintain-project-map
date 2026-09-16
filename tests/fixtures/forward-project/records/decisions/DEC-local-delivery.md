---
id: DEC-local-delivery
kind: decision
title: 只维护本地交付
summary: 项目范围收缩为本地归档，自动共享已退出当前工作流。
status: active
relations:
  - relation: derived_from
    to:
      record_id: REQ-local-archive
  - relation: supersedes
    to:
      record_id: MOD-auto-share
---

# 只维护本地交付

取消自动共享是范围选择。项目继续对本地归档和来源回查负责；用户需要分享时自行选择其他工具。

选择理由是让本地整理和后续传播分别由需要它们的使用者决定。旧共享步骤曾经可用，不能据此说它是失败尝试。

来源：[EVT-02 与 EVT-03](../../sources/design-events.md#evt-02--曾经存在的共享能力)。
