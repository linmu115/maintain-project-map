---
id: MOD-archive
kind: module
title: 归档步骤
summary: 读取本地文本材料，写入副本和来源清单。
status: active
progress: implemented
relations:
  - relation: implements
    to:
      record_id: REQ-local-archive
  - relation: provides
    to:
      record_id: IF-archive-package
  - relation: related_to
    to:
      project_id: aa9565fb-cb09-4597-a84e-502d1416c02c
      record_id: IF-read-archive
    reason: 可选阅读 Skill 读取归档包；本样例未提供或登记它的地图。
---

# 归档步骤

入口：[archive.py](../../workflow/archive.py)。负责读取文本并交付归档包；来源定义与输入保护要求由归档规格约束。

外部阅读 Skill 通过目标项目 ID 与条目 ID 引用。目前本机样例没有登记这个目标，无法核查其实现。这个引用不要求导入对方整张地图，也不证明下游已兼容未来变更。
