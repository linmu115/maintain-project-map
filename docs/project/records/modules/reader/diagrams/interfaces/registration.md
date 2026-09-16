---
id: IF-native-diagram
kind: interface
title: 图源登记、节点绑定与交付
status: current
summary: 地图登记原生图文件和记录映射；Archify 负责底层格式、校验和图交互。
sources:
- path: ../../maintain-project-map/references/archify-authoring.md
  role: skill-source-authority
- path: ../../maintain-project-map/assets/vendor/archify/schemas/architecture.schema.json
  role: skill-source-authority
- path: ../../maintain-project-map/assets/vendor/archify/schemas/workflow.schema.json
  role: skill-source-authority
- path: ../../maintain-project-map/scripts/archify_adapter.py
  role: skill-source-authority
relations:
- relation: consumes
  to:
    record_id: IF-record-data
---

# 图源登记、节点绑定与交付


作者交付架构或工作流 JSON，并在 project.yaml 声明源路径及 node_records。比如一个“提交事务”节点可关联模块、需求和验证的入口，节点本身仍使用原生 ID。

完整地图接入方式见 [Archify 图源维护](../../../../../../../maintain-project-map/references/archify-authoring.md)；底层图格式只以 [架构 schema](../../../../../../../maintain-project-map/assets/vendor/archify/schemas/architecture.schema.json) 和 [工作流 schema](../../../../../../../maintain-project-map/assets/vendor/archify/schemas/workflow.schema.json) 为准。

提供方是本 Skill 的图适配模块，底层能力来自 Archify。输入经原生交付后得到可读图、节点对应与回执；无效源不能被旧图冒充，缺少绑定时明确显示未关联。原版和嵌入版摘要分别保存。

现有 A/B 清单每种类型接入一份主图。更深模块可用原生边界、聚焦视图和文档互链表达；额外图没有自动加入页面的导航功能。普通文本修订不要求重画全部图。
