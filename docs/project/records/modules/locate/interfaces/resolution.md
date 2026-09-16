---
id: IF-project-location
kind: interface
title: 项目 ID 与位置解析
status: current
summary: 同一项目跨目录和工作树保留身份；解析只返回位置，不递归加载对方地图。
sources:
- path: ../../maintain-project-map/references/operations.md
  role: skill-source-authority
- path: ../../maintain-project-map/scripts/project_map.py
  role: skill-source-authority
relations:
- relation: related
  to:
    record_id: OBJ-map-identity
---

# 项目 ID 与位置解析


提供一个明确的地图路径、当前工作目录，或稳定项目 ID，定位模块返回可读取的 project.yaml。比如移动仓库后只需更新位置登记，需求和接口的 ID 不必改名。

一个 ID 有多个工作树时，优先匹配明确上下文；仍有多个合理位置就返回候选，不能随便选一个。登记只保存位置，外部项目的正文不复制到本地图。

命令与参数以 [本地操作](../../../../../../maintain-project-map/references/operations.md) 为准，实际解析在 [project_map.py](../../../../../../maintain-project-map/scripts/project_map.py)。已知使用方是记录查询和阅读生成；它们拿到位置后才按需读取。未知目标保留项目 ID 并说明未定位。
