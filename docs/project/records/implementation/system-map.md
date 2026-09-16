---
id: IMP-system-map
kind: implementation
title: 系统地图与局部检索的实际实现
status: current
progress: implemented
summary: 已支持系统类型、明确收录与接口聚合、原生护照项目入口、新标签页目标解析、模块范围查询和记录级续读。
gap: 实际 DSH 系统的收录范围尚未迁移；内嵌画布鼠标端到端实测受浏览器自动化坐标限制。性能收益未做对照实验。
relations:
  - relation: implements
    to: {record_id: REQ-system-map}
  - relation: implements
    to: {record_id: REQ-scoped-disclosure}
  - relation: related
    to: {record_id: MOD-system}
  - relation: related
    to: {record_id: VER-system-map}
---

# 系统地图与局部检索的实际实现

## 已能使用

- `kind: system` 明确收录独立地图，系统有自己的身份、说明和决定；支持多个系统引用同一项目。
- 系统概览、接口与关联、收录项目、用户按需留存的更新记录。系统只显示整体组织，普通项目继续保留功能路径。
- 同一合同在提供方唯一维护，目录派生提供方与消费者；交叉、循环、外部端点按声明保留，不递归加载依赖。
- 项目卡片先显示原生语义护照，“进入项目”按稳定身份在新标签页打开完整项目阅读页。源图不作页面导航。
- 目标丢失、多个工作树、图或节点失效、预览不可用会明确报错。临时 HTTP 地址不进入长期收录配置。
- `modules` 与 `search --module` 定位局部；`members/interfaces/impact` 返回有限目录、已登记关系及覆盖说明；`read --record-fingerprint` 支持在无关记录改动后续读本记录。
- Windows 的 Git 查询、渲染链和测试辅助进程补齐隐藏控制台启动方式，上游 Archify 文件保持原样。

## 使用方式

按 Skill 的 references/system-maps.md 配置明确成员和项目节点绑定，像普通地图一样调用 render_map.py。可运行示例位于 Skill 的 examples/system-map：Core 维护两类接口，Board 和 Graph 分别接入并有交叉关系。示例不代表真实 DSH 分组。

局部开发可直接读目标记录或源码。系统查询本地加载必要资料后只返回有界结果；生成的 HTML 和 docs.json 用于开发者阅读，不要求加入模型上下文。

## 当前边界

系统目录是派生快照，成员记录变化后按需重新导出；模型查询直接读当前源文件，没有新增持久索引数据库。绑定源文件整体改变时，记录级续读保守地要求重新定位。反向查询覆盖明确收录及已声明边，不推断动态调用。

本次交付功能和虚构示例；没有重分真实 DSH 插件归属或修改插件源码，没有自动新增开发者更新条目。递归模块子图、MRS、成本 benchmark 和浏览器插件继续留待后续。具体已验证与未验证范围见 [[VER-system-map]]。
