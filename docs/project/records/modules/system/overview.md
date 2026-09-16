---
id: MOD-system
kind: module
title: 系统地图组合与接口汇集
status: current
summary: 面向明确的开发对象收录独立项目地图，派生接口目录和一般图关系，按稳定身份进入目标项目。
relations:
  - relation: implements
    to: {record_id: REQ-system-map}
  - relation: provides
    to: {record_id: IF-system-composition}
  - relation: consumes
    to: {record_id: IF-project-location}
  - relation: consumes
    to: {record_id: IF-record-data}
  - relation: consumes
    to: {record_id: IF-http-preview}
---

# 系统地图组合与接口汇集

系统围绕用户选择的开发对象明确收录项目，例如引用协作系统可以关联几个独立维护的组件地图。收录不复制项目的需求、实现和合同，也不自动沿依赖把所有项目纳入。

项目身份、模块身份和接口身份不要求形成树。同一项目可进入多个系统，多个消费者可指向同一合同，交叉和循环关系照实保存。目录仅帮助阅读。

开发者从系统概览看清边界和整体组织，再从接口与关联查询唯一合同、提供方、接入说明与外部端点。点击图中项目先显示语义护照，从“进入项目”打开独立项目的完整阅读页。模型可以直接进入目标项目的局部查询。

配置和职责见 [[IF-system-composition]]，实际使用见 [[IMP-system-map]]，检查证据另存 [[VER-system-map]]。源码入口为 scripts/system_map.py；页面由 assets/system-reader.js 和现有阅读器呈现。
