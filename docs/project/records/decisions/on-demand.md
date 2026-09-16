---
id: DEC-on-demand
kind: decision
title: 权威记录共用，阅读与维护按需发生
status: current
summary: 避免为两种阅读方式 或每轮开发复制资料；让模型只读影响当前判断的记录。
sources:
- path: ../../maintain-project-map/SKILL.md
  role: skill-source-authority
- path: ../../maintain-project-map/references/evaluation.md
  role: skill-source-authority
- path: ../../maintain-project-map/references/composite-projects.md
  role: skill-source-authority
relations:
- relation: implements
  to:
    record_id: REQ-cost
- relation: related
  to:
    record_id: REQ-assets
---

# 权威记录共用，阅读与维护按需发生


一份正式需求或接口只维护一处，其他模块通过绑定和链接找到它。A/B 是同一份记录的两种阅读方式，生成页面不是另一份可独立修改的规格。

模型按当前问题读有关记录；丰富资产不等于每次都要加载。目录与链接帮助开发者定位，检索脚本帮助模型读有限原文。Archify 复用原生图能力，Mistune 复用 Markdown 解析，Git 复用版本历史。

新增指引应帮助模型判断范围，不强制全图分析、固定检查表或每轮报告。维护可能包含合并、剪枝或退役。效果要在后续开发任务中检验；建图耗时、记录数量和单次 UI 检查不能证明开发更省 token。
