---
id: MOD-locate
kind: module
title: 找到当前项目地图
status: current
summary: 通过当前目录、明确清单路径或项目 ID 定位地图，区分多个工作树位置。
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

注册表仅保存位置。一次定位不会递归读取其他项目的内容；同名项目也不会自动合并。

代码入口：maintain-project-map/scripts/project_map.py。


定位约定见 [[IF-project-location]]；长期身份与工作树的区别见 [[OBJ-map-identity]]。
