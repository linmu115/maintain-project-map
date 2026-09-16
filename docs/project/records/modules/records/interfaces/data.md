---
id: IF-record-data
kind: interface
title: 记录、绑定与语义关系
status: current
summary: 原文件维护正式内容，地图用身份和绑定连接已有章节、接口与证据。
sources:
- path: ../../maintain-project-map/references/asset-model.md
  role: skill-source-authority
- path: ../../maintain-project-map/scripts/project_map.py
  role: skill-source-authority
relations:
- relation: related
  to:
    record_id: OBJ-evidence
---

# 记录、绑定与语义关系


项目维护者交付 project.yaml、入口 map.md，以及真正需要独立维护的记录。已经有正式需求书时，可绑定它的唯一标题或表格编号；不要再抄一份完整规格。新的独立记录带稳定 ID、类型、标题及所需状态与来源。

字段的唯一完整约定在 [资产模型](../../../../../../maintain-project-map/references/asset-model.md)。本页帮助理解边界：文件夹服务人读分组，ID 服务长期定位，提供/消费关系表达实际协作，正文链接只帮助阅读。

同一语义关系只声明一次；读取时归一已知反向写法，保留不同版本和角色。一个模块使用某个接口，不说明它的所有功能都调用该接口。实现记录与验证记录分别保存，见 [[OBJ-evidence]]。

已知使用方是 [[MOD-records|记录引擎]]、[[MOD-document-navigation|目录与链接]]、[[MOD-reader|阅读生成]]。绑定标题失效或 ID 重复时修复来源/绑定，不能用旧导出掩盖当前错误。
