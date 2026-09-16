---
id: IMP-release
kind: implementation
title: 当前可用能力与使用边界
status: current
progress: implemented
summary: 已安装 Skill 可维护项目与系统地图，支持接口聚合、新标签页项目入口、模块局部查询及 A/B 阅读。
gap: 尚无后续多轮开发的有无地图对照；额外图导航和更多会话格式仍未实现。
relations:
- relation: implements
  to:
    record_id: REQ-map
- relation: implements
  to:
    record_id: REQ-assets
- relation: implements
  to:
    record_id: REQ-source
- relation: implements
  to:
    record_id: REQ-linear-reader
aliases:
- 首版实际实现
---

# 当前可用能力与使用边界

## 已能做什么

- [[MOD-guidance|按需维护]]：明确需求、设计理由、实现与证据；合并冗余和退役旧记录，区分失败探索。
- [[MOD-locate|项目定位]]：稳定项目 ID 与位置登记，区分多个工作树，通过薄引用查另一张地图。
- [[MOD-records|记录查询]]：绑定已有标题/表格行，按关键词和 ID 查回原文，分段读取并核对指纹。
- [[MOD-reader|开发者阅读]]：同一批资料生成 A/B，递归目录、Markdown/Wiki 链接、声明的原资料阅读，以及独立实现/验证入口。
- [[MOD-archify|图形]]：复用固定版本的原生 Archify 校验、拓扑查询和交互；外框固定，选中画布后缩放/拖动，点击外部返回正文滚动。
- [[MOD-system|系统组合]]：明确收录独立地图，汇集唯一合同与接入关系；项目护照新开目标项目阅读页，局部查询不依赖上层总图。
- [[MOD-session|会话来源]]：查询明确指定的 Codex 可见消息，保留身份与范围。

## 怎样使用

在正常会话提出需求、旧设计问题或地图整理要求，模型按当前范围选用 Skill。入口为 [SKILL.md](../../../../maintain-project-map/SKILL.md)，具体调用查 [本地操作](../../../../maintain-project-map/references/operations.md)。生成页面时优先使用当前本机 HTTP 地址；记录变化后按需导出并刷新。

## 适用边界

查询采用词面和别名，未提供语义数据库。跨项目引用不会自动同步或遍历；会话适配只支持明确的输入格式。A/B 各接入一份主架构与主流程图，其他图的页面导航需要单独实现。

页面、摘要和图源校验都不能证明产品代码正确。此前 80 项运行检查与阅读器实测见 [[VER-reader-navigation]]；本次自身地图整理见 [[VER-self-map]]。未据此声明 token 节省或后续开发质量提升。

## 更新记录与往返阅读

已支持 [[IMP-passport-updates-history|语义护照条目跳转、更新记录和顶栏返回]]。更新记录仅在开发者明确要求留存某次迭代时新增，不随普通维护自动追加。
