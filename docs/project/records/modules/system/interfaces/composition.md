---
id: IF-system-composition
kind: interface
title: 系统收录、接口汇集与项目进入约定
status: current
summary: system.members 明确收录，node_projects 按稳定项目 ID 绑定原生图节点；聚合目录只返回摘要和声明关系，完整合同保留在提供方。
---

# 系统收录、接口汇集与项目进入约定

## 给开发者的解释

把多张独立地图加入一个系统，相当于建立一个共享的阅读目录：它汇集项目在此系统中的职责、可用接口及接入关系。接口名称可点开权威合同，消费方入口可点开其接入说明。不会把各项目正文重新抄到系统里。

## 配置与身份

清单沿用 project-map/v1，kind 为 system。system.members 的每项包含 project_id、职责 role、收录说明 scope、目标 diagram，可选目标 node 和明确工作树 manifest。缺少 manifest 时按注册表解析；多个合理位置返回歧义。

archify.architecture.node_projects 将原生节点 ID 绑定到已收录项目 ID。系统只声明 architecture。项目自己的 architecture/workflow 保留各自身份；系统不提供功能路径占位。普通项目格式不需要迁移。

## 提供与消费

提供方的模块用 provides 指向接口，消费方接入说明用 consumes 指向提供方项目及接口 ID。查询按这一份声明派生反向关系。interface_family 可区分不同 Adapter 家族；目录不把它们合并成同一接口。

members、interfaces、impact 只汇集明确成员，不递归展开子系统。结果包含覆盖缺口、分页和定位信息；未登记关系不证明没有依赖。CLI 正文续读约定见 [[IF-map-query]]。

## 打开项目

护照的进入项目链接指向当前本机服务的解析入口，参数只有稳定项目和图/记录/节点身份。服务检查当前明确成员清单，按需准备目标项目阅读页、启动或复用预览，再转到目标完整地图。目标页有自己的概览、条目、更新记录与图入口。

缺失项目、歧义工作树、目标图或节点失效不会猜选。快照中的缺口在护照和成员列表显示；点击时新发现的故障在新标签页显示，原系统页保持。浏览器阻止新标签页时提供可见链接与反馈。没有跨项目输入输出中间卡，也不建立单标签页跨地图返回栈。

完整可分发配置说明由 Skill 的 references/system-maps.md 维护；本记录解释本项目模块的职责，代码在 scripts/system_map.py、scripts/serve_map.py、assets/diagram-records.js。
