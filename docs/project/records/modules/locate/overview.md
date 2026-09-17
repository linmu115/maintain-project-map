---
id: MOD-locate
kind: module
title: 找到当前项目地图
status: current
summary: 按项目名称、别名、ID 或明确位置找到地图；维护本机目录，区分当前工作树、默认位置和失效入口。
relations:
- relation: implements
  to:
    record_id: REQ-map
- relation: flows_to
  to:
    record_id: MOD-records
  reason: 用户请求生成阅读页面时，把明确的地图位置交给记录读取器。
- relation: provides
  to:
    record_id: IF-project-location
sources:
- path: ../../maintain-project-map/scripts/project_map.py
  role: skill-source-authority
- path: ../../maintain-project-map/references/operations.md
  role: skill-source-authority
---

# 找到当前项目地图

项目 ID 是长期身份，本地路径负责到达文件。当前工作树有明确地图时使用它；一个 ID 对应多个可用位置且不能判断上下文时，需要指定位置，不能随便选一份。

用户说“看 Archify 的项目地图”时，先通过名称或别名查本机登记，拿到清单后再围绕问题读取内容。无须用户重新给路径；查询只返回位置和简短元信息，不预载地图正文或开发历程。

注册表保存名称、别名、稳定 ID、位置和明确指定的默认工作副本。重复登记不重复写入；新建、接入、实质更新或搬迁时由 Skill 主动核对。没有后台全盘扫描。默认位置丢失会报告失效，不自动换成旧副本。

目录只接入本 Skill 的项目地图。MRS 软件的开发地图属于项目地图；B/C 题等 MRS 研究地图不在本能力范围。样例、测试、候选与视频导出副本不自动成为当前入口。

代码入口：maintain-project-map/scripts/map_catalog.py 与 project_map.py。实现和核查见 [[IMP-map-catalog]]、[[VER-map-catalog]]。


定位约定见 [[IF-project-location]]；长期身份与工作树的区别见 [[OBJ-map-identity]]。
