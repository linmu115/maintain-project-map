---
id: MOD-updates
kind: module
title: 开发者选择留存的更新记录
status: current
summary: 用户明确要求时留存一轮功能迭代，按日期阅读并跳到相关图卡片。
sources:
- path: ../../maintain-project-map/references/update-records.md
  role: skill-source-authority
- path: ../../maintain-project-map/assets/reader.html
  role: skill-source-authority
relations:
- relation: contained_by
  to:
    record_id: MOD-reader
- relation: provides
  to:
    record_id: IF-update-record
- relation: implements
  to:
    record_id: REQ-passport-updates-history
---

# 开发者选择留存的更新记录

当你完成一次值得记住的功能迭代，并在会话中明确提出“把这次迭代加入更新记录”，模型才写一条更新。普通开发、地图整理和页面刷新不自动追加。

左侧“更新记录”按日期倒序显示各次迭代，打开一条能读到改变了什么功能、必要的设计背景与限制。与图结构有关时，通过正文链接在本页跳到相应图，并把卡片放在画布中央。顶栏返回可以回到原来的更新位置。

条目保存于同一地图 records/updates 下，kind 为 update，不复制实现和验证文档。格式与写入触发只维护在 [[IF-update-record|更新记录约定]]。阅读器用本地数据展示，日期参与检索；没有常驻写入服务或 LLM 自动生成步骤。
