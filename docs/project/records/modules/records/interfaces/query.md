---
id: IF-map-query
kind: interface
title: 查询与分段读取
status: current
summary: 模型按当前问题取得有限记录、原位置和版本范围，不必读取整张页面。
sources:
- path: ../../maintain-project-map/references/operations.md
  role: skill-source-authority
- path: ../../maintain-project-map/scripts/project_map.py
  role: skill-source-authority
relations:
- relation: consumes
  to:
    record_id: IF-project-location
- relation: consumes
  to:
    record_id: IF-record-data
---

# 查询与分段读取


输入当前地图和关键词、记录 ID 或关系起点，可获得候选记录、限定正文或明确登记的关联。比如只问“为什么旧同步模块退役”，先查名称/别名，再读决定和后继，不用展开全部 UI。

长记录按 offset 续读，并带回内容指纹；来源变化时重新定位，避免拼接不同版本。关系查询返回本地图已声明的边，不自动遍历外部项目。词面和别名检索不等于语义检索，也不证明未命中的事实不存在。

加载共同源数据供阅读导出也属于记录引擎职责。命令示例只在 [本地操作](../../../../../../maintain-project-map/references/operations.md) 维护，返回信息由 [project_map.py](../../../../../../maintain-project-map/scripts/project_map.py) 定义。普通查询不会加载 HTML、源码阅读快照或 Archify 运行时。

## 局部披露扩展

modules 返回稳定模块 ID；search --module 按显式 module_id 或最近模块概览限定范围。read --record-fingerprint 只核对当前记录及绑定源，允许无关模块修改后的续读；原有整图 --fingerprint 仍可用于严格一致性。候选和部分正文都附覆盖说明，不能把尚未打开的约束视为完整已读。

members、interfaces、impact 在明确系统范围内汇集成员摘要与登记关系，分页返回，不自动展开正文或递归成员；系统约定见 [[IF-system-composition]]。
