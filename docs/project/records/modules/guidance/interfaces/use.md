---
id: IF-skill-use
kind: interface
title: 开发者怎样让模型维护地图
status: current
summary: 开发者提出自然需求或指出记录；模型找到相关权威资料，解释或修订并给出可查位置。
sources:
- path: ../../maintain-project-map/SKILL.md
  role: skill-source-authority
- path: ../../maintain-project-map/references/composite-projects.md
  role: skill-source-authority
relations:
- relation: consumes
  to:
    record_id: IF-map-query
---

# 开发者怎样让模型维护地图


例如：“把之前的只读导出改为可同步，但不要动历史记录。”模型需要找到对应需求和对象边界，先区分已确定的修改与仍在讨论的想法，再修改有关记录和实际实现。回答应指出改了哪里、依据是什么、还有什么没核实。

提供方是本 Skill 的维护指引，使用方是当前会话中的模型与开发者。它通过 [Skill 入口](../../../../../../maintain-project-map/SKILL.md) 和必要参考文件约定行为，不另设聊天界面或常驻任务。

地图不会自动证明实现正确，也不会在模型未运行时自己维护。来源不完整时继续可独立完成的工作，只有缺失信息影响关键判断时才澄清。查询由 [[IF-map-query]] 支持，结构选择参考 [组合项目指引](../../../../../../maintain-project-map/references/composite-projects.md)。
