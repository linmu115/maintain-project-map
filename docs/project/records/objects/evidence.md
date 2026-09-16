---
id: OBJ-evidence
kind: object
title: 要求、实现与验证的区别
status: current
summary: 要求表达应做什么，实现说明当前行为，验证只支持实际检查的范围和版本。
sources:
- path: ../../maintain-project-map/references/asset-model.md
  role: skill-source-authority
- path: ../../maintain-project-map/references/lifecycle.md
  role: skill-source-authority
relations:
- relation: related
  to:
    record_id: REQ-maintenance
---

# 要求、实现与验证的区别


“用户要求支持同步”“源码已经支持同步”“在两个真实应用中验证过同步”是三个不同事实。它们分别放在需求、实现和验证记录，通过身份、来源和版本关联。

来源指纹可判断读取内容是否变化，不能代替测试；地图目录的 Git 提交也不自动覆盖外部仓库。旧报告保留原版本，当前没重跑不能把它改成新的通过记录。

合并/退役记录与失败探索不同：曾经有效的功能因新需求退出，不表示它的探索失败。当前视图可以剪短，旧 ID、后继和重要理由继续能查到。格式和状态约定见 [资产模型](../../../../maintain-project-map/references/asset-model.md)、[生命周期](../../../../maintain-project-map/references/lifecycle.md)。
