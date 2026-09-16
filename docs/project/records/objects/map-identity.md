---
id: OBJ-map-identity
kind: object
title: 项目、记录与工作树身份
status: current
summary: 项目 ID 与记录 ID 是长期定位，文件夹、工作树和页面只是位置或阅读方式。
sources:
- path: ../../maintain-project-map/references/asset-model.md
  role: skill-source-authority
relations:
- relation: related
  to:
    record_id: IF-project-location
---

# 项目、记录与工作树身份


一项目维护一份逻辑地图；同一项目在多个 Git 工作树中可以有不同版本。注册表帮助把项目 ID 解析为当前位置，图和文档共用记录身份。

文件夹可以表达模块与子模块，不因拆目录就创建新项目。项目范围和成员声明先于目录分组；共享协议或代码依赖不自动建立父子身份。已有独立维护地图的成员或外部提供方通过项目 ID 与必要记录 ID 关联，当前地图只保存自己的介绍与接入说明。

本 Skill 的项目 ID 沿用 `2c64630e-7c8f-465f-97b9-ef6e5916c8aa`。原始设计仍在已有设计方案中；本目录维护地图说明和图源；实现源码在 Skill 的发布仓库，安装目录是运行副本。页面 URL 会随服务变化，不能代替这些身份。
