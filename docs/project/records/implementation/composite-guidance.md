---
id: IMP-composite-guidance
kind: implementation
title: 组合项目的按需组织指引
status: current
progress: implemented
summary: 先确认成员和外部边界，再按职责分析层级、唯一合同与实际消费能力；图按归属和执行证据组织。
gap: 指引不会自动判定全部成员或消费者；尚无后续项目开发的有无地图对照，额外图导航仍需单独实现。
sources:
  - path: ../../maintain-project-map/SKILL.md
    role: skill-source-authority
  - path: ../../maintain-project-map/references/composite-projects.md
    role: skill-source-authority
relations:
  - relation: implements
    to: {record_id: REQ-composite-structure}
---

# 组合项目的按需组织指引

## 当前怎样帮助组织项目

入口只在接入组合项目、调整层级、解释扩展或维护相关图时加载专门说明。先用用户确认的范围和成员声明确定地图边界，再核查源码职责。协议是通信约定；目录相邻、共用安装包或某个调用点都不能单独证明成员归属。

有独立地图的外部提供方保留自己的内部模块与完整合同。本地图说明自己接入哪项能力、影响哪些功能，使用项目 ID 和必要条目 ID 关联；架构图把该依赖放在成员边界之外。确认属于本项目的模块，再按职责、接口、对象和维护边界决定是否继续细分。

平台适配与业务对象扩展分别解释，正式合同由提供方维护一份，双方接入说明互链。按具体消费能力核查接口与证据，区分直接调用、间接依赖、计划和未核实范围。图中的框表达归属，有执行依据的流程才使用泳道和交接顺序。

## 使用范围与依据

这些是给模型按上下文应用的判断指引，适用于软件、工作流和 Skill。示例不自动成为本 Skill 的成员；目录示例可缩减，不要求空目录、每轮全图分析、用户旅程或固定报告。

完整组织指引只在 [组合项目与扩展接口](../../../../maintain-project-map/references/composite-projects.md) 维护。目录、正文导航与关系归一的实际阅读能力见 [[IMP-reader-navigation]]；文档核对范围见 [[VER-composite-guidance]]，不据此声称模型已经识别全部接入方或提高后续开发效果。
