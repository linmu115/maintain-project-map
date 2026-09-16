---
id: MOD-records
kind: module
title: 读取和维护权威记录
status: current
summary: 绑定现有文档章节或表格，读取独立记录及关系，提供有范围的查询与状态维护。
relations:
- relation: implements
  to:
    record_id: REQ-assets
- relation: implements
  to:
    record_id: REQ-maintenance
- relation: implements
  to:
    record_id: REQ-relations
- relation: flows_to
  to:
    record_id: MOD-reader
  reason: 仅在需要阅读页面时，将本次读取的共同内容交给呈现模块。
- relation: provides
  to:
    record_id: IF-record-data
- relation: provides
  to:
    record_id: IF-map-query
sources:
- path: ../../maintain-project-map/scripts/project_map.py
  role: skill-source-authority
- path: ../../maintain-project-map/references/asset-model.md
  role: skill-source-authority
- path: ../../maintain-project-map/references/lifecycle.md
  role: skill-source-authority
---

# 读取和维护权威记录

已有需求文档可以按原章节或表格编号绑定。需要新独立条目时，使用带身份、类型与标题的 Markdown。规范正文仍在原文件维护，搜索与页面读取同一内容。

合并或退役只更新记录本身，并保留原因和后继；不通过记录状态去删除产品代码。失败探索按其适用条件保存，不等同于功能退役。

代码入口：maintain-project-map/scripts/project_map.py。


录入资料先看 [[IF-record-data|记录与绑定约定]]；查询和分页结果见 [[IF-map-query]]。状态与证据的区别见 [[OBJ-evidence]]。
