---
id: MOD-auto-share
kind: module
title: 自动共享摘要
summary: 曾可用的共享步骤因范围改变退出；当前交付为本地归档包。
aliases: [分享卡片, 自动发出去, 自动发布]
status: retired
relations:
  - relation: replaced_by
    to:
      record_id: DEC-local-delivery
    reason: 取消自动传播，用户自行选择后续工具。
---

# 自动共享摘要

历史用途：归档后把摘要交给共享插件。样例历史中曾正常使用，后来因只做本地交付而退役。

当前样例入口没有共享调用；后继说明为 [只维护本地交付](../decisions/DEC-local-delivery.md)。这是功能退役，不是一次失败探索。

来源：[EVT-02、EVT-03](../../sources/design-events.md#evt-02--曾经存在的共享能力)。没有真实 Git 历史可引用；历史依据就是这份明确标记的合成事件记录。
