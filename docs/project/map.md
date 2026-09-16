# 项目维护地图 Skill

## 它帮助你做什么

长期开发时，把项目能做什么、关键对象、设计原因、接口、当前实现和来源保留下来。忘了可以自己读地图，也可以在原会话里让 LLM 找到有关位置；有新需求或旧功能退出时，继续修订同一份资产。

一项目一地图，适用于软件、插件组合、工作流和 Skill。核心原则见 [[DEC-on-demand|为什么共用权威记录并按需维护]]，实际能力与限制见 [[IMP-release|当前能力与使用边界]]。这张地图维护的是 Skill 本身：按需维护指引、项目定位、记录查询、会话取证和开发者阅读。

## 按你现在关心的事情进入

| 想弄清什么 | 阅读入口 |
| --- | --- |
| 模型什么时候该维护、怎样判断范围 | [按需维护与解释](records/modules/guidance/overview.md)、[会话使用方式](records/modules/guidance/interfaces/use.md) |
| 怎样找回项目、旧需求或某个接口 | [位置与身份](records/modules/locate/overview.md)、[查询与分段读取](records/modules/records/interfaces/query.md) |
| 文档与模块怎样组织，哪些应拆开 | [记录与绑定](records/modules/records/interfaces/data.md)、[模块层级与扩展接口](records/requirements/composite-projects.md) |
| 页面、目录树、正文链接和图如何协作 | [阅读模块](records/modules/reader/overview.md)、[目录与文档跳转](records/modules/reader/documents/overview.md)、[Archify 适配](records/modules/reader/diagrams/overview.md) |
| 阅读地址是什么，为什么需要刷新 | [本机预览](records/modules/reader/preview/overview.md)、[入口与状态](records/modules/reader/preview/interfaces/http.md) |
| 如何找长会话里的原话 | [指定会话检索](records/modules/session/overview.md) |
| 本次系统地图扩展要做什么，怎样验收 | [功能更新需求：在项目地图上扩展系统地图](records/requirements/system-map.md)、[命令查询与分层披露细则](records/requirements/scoped-disclosure.md) |

## 地图范围与协作边界

[[OBJ-map-identity|项目、记录和工作树]]区分身份与位置；[[OBJ-evidence|要求、实现和验证]]区分应做什么、目前能做什么和实际检查过什么。正式接口说明由提供方维护一份，消费者页解释自己用到的能力并互链。

Skill 的源码、安装副本和这份地图属于同一维护对象。DSH Suite、Session Maintenance、ThoughtDAG 是使用方或分析案例，各自保留自己的地图；它们的模块与合同在各自项目中维护。

组合项目先按已确认的范围和成员声明确定边界，再核查职责。共用协议、安装位置或代码依赖只说明联系，不自动产生父子模块。已有独立地图的外部提供方用项目身份和本项目的接入说明关联，见 [[REQ-composite-structure|模块与接口的组织原则]]。

Archify 提供原生图模型与交互，Mistune 处理 Markdown，Git 保存版本历史。本 Skill 维护它们的接入和使用边界。模型直接查询权威记录，A/B 页面给开发者阅读；提问继续使用原会话。

## 结构和流程怎样看

“整体组织”框出资料、地图核心、阅读生成与原生组件；“功能路径”展开按需读取并交付阅读页面的实际顺序。该流程只在需要页面时运行，不是每轮开发的固定步骤。项目条目按文件夹展开，正文互链连接模块、接口和来源。

也可以直接定位[维护指引](map-node:architecture/skill-guidance)或[阅读页面交付](map-node:workflow/compose-reading-page)，从卡片的语义护照打开相关说明，再用顶栏返回此前阅读位置。

## 做到哪与缺什么

本次扩展需求见 [[REQ-system-map|系统地图超集扩展的功能需求]]：围绕开发对象汇集项目接口与一般图关系，只显示整体组织图；点击项目节点先看护照，再通过“进入项目”新开项目地图标签页，保留原系统页状态。功能已实现，配置与实际能力见 [[IMP-system-map|系统地图实现]]、[[IF-system-composition|系统收录与接口汇集]]；具体检查和限制见 [[VER-system-map]]。

当前功能见 [[IMP-release|能力与使用边界]]。模块树、Wiki 章节跳转和反向关系归一见 [[IMP-reader-navigation|目录与文档导航]]；组合项目的通用分析规则见 [[IMP-composite-guidance|组合项目的组织指引]]。当前每类接入一份主图，会话脚本处理指定的 Codex 记录文件；更多图的页面导航、其他会话格式和后续开发效果对照见实现说明中的限制。

验证详情独立放在 [[VER-reader-navigation|阅读器检查]]、[[VER-self-map|自身地图核对]]。过去的样式决定与旧检查保留原状态和日期，历史可查，不把旧页面或建图数量当成开发效果证据。

## 留存迭代与往返阅读

需要记住一次功能迭代时，在会话中明确要求加入 [[MOD-updates|更新记录]]。图卡片的语义护照可直接打开对应条目，顶栏返回恢复此前阅读位置；变化涉及图时，更新正文能直接定位卡片，见 [[IMP-passport-updates-history|护照、图定位与返回说明]]。
