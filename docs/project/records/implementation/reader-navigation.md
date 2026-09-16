---
id: IMP-reader-navigation
kind: implementation
title: 模块目录与 Wiki 文档导航
status: current
progress: implemented
summary: 通用阅读器已支持递归目录、Markdown/Wiki 链接、源码快照与反向关系归一，组合项目指引按具体能力核查接入。
gap: 原资料阅读限于直接引用且已声明的文本；同名 Wiki 目标需作者用 ID 或路径消歧。后续开发效果尚无对照结果。
relations:
  - relation: implements
    to: {record_id: REQ-reader-navigation}
  - relation: implements
    to: {record_id: REQ-composite-structure}
---

# 模块目录与 Wiki 文档导航

## 当前行为

- records 的文件夹成为 B 可展开目录；模块 overview/index/README 的标题作为组名，其他记录列在所属层级。绑定的既有文档保持原来源。搜索展开匹配条目的祖先，正文跳转显示相应位置。
- Mistune 负责 Markdown 语法，薄适配层处理 `[[ID#章节|标签]]`、同名消歧、记录与原资料定位。标准相对链接、参考式链接和带空格路径继续可用。
- 接口源码与文档可以在当前阅读器打开并返回。只打包直接引用且已声明的文本资料，展示来源位置和独立指纹；没有扫描整个仓库或将资料复制成另一份权威合同。LLM 的普通查询不读取这些页面快照。
- provides/consumes/contains 的已知反向声明合并显示，保留各条说明；不同角色、版本、机制及外部项目身份保持区分。本文互链只作阅读导航。
- Skill 的组合项目参考说明补充通用耦合分析和证据边界；入口仍然按需加载该说明。没有增加每轮全图分析或固定报告。

实现位于 scripts/reader_content.py、reader_markdown.py、render_map.py、project_map.py 与 assets/reader.html。Archify 原版核心及图形缩放层未修改。

## 适用范围

现有地图重新导出即可使用；无须新增一份 UI 目录配置或将所有文档转成 Wiki。DSH–Obsidian 的修订地图是示例，生成器和测试不依赖 DSH 名称。旧 candidate 对比产物独立保留。

本说明只报告已实现能力。验证结果见 [[VER-reader-navigation]]，不据此推断后续项目开发一定更省 token 或质量更高。
