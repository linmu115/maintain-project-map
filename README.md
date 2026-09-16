# maintain-project-map

辅助长期开发的软件、工作流与 Skill 维护项目认识：需求、设计、对象、模块、接口、实现、验证和来源。一项目一地图，原始资料使用 Markdown/YAML 和 Git 保存。

## 安装到 Codex

将本仓库的 `maintain-project-map` 文件夹复制到用户的 `.codex/skills/` 目录。入口为 [SKILL.md](maintain-project-map/SKILL.md)。在会话中说：

> 用 $maintain-project-map 为这个项目建立并维护地图。

Python 3.10+ 用于记录操作，安装 `maintain-project-map/requirements.txt` 中的依赖。图形导出另需 Node.js 18+，普通记录查询不要求渲染页面。

## 包含的能力

- 稳定项目 ID 与本机位置登记，跨项目用简短 ID 引用。
- 绑定已有需求文档的章节或表格行，避免复制一套规格。
- 按需采用[组合项目与扩展接口](maintain-project-map/references/composite-projects.md)的组织指引：职责层级、提供方唯一合同、具体能力的接入依据，以及 Archify 模块边界和泳道。
- 模块目录自动生成 B/C 可展开侧栏；Mistune 解析 Markdown，标准文档链接和 Wiki 链接连接记录、章节及已声明原资料。同义反向关系合并显示。
- 记录合并、退役和失败探索分别表达；实现与验证独立存储。
- 按名称、别名、正文检索；支持检索明确指定的 Codex 可见会话记录。
- 按需生成三种人读页面：项目概览、项目条目、连续文档。白色为主的阅读界面、独立滚动、文档内按点击激活的画布。
- 复用固定版本 Archify 的图模型、校验和阅读器，保留原版及嵌入副本。画布视窗固定，内部内容缩放和平移。

本地 HTTP 服务仅用于阅读导出快照。页面操作不调用模型；提问继续使用原会话。没有长期对照证据证明 Skill 已降低 token 成本或提高开发成功率。

## 开发与检查

```sh
python -m pip install -r maintain-project-map/requirements.txt
python -m pytest tests maintain-project-map/tests
```

测试需要 pytest 和可用的 Node.js。项目接入说明见[本地操作](maintain-project-map/references/operations.md)。

## 第三方代码

Archify 固定于 `d673e8300df60a5c8166abe78787fdc78f6b8000`，原始文件摘要及 MIT/字体许可保留于 [归属说明](maintain-project-map/assets/vendor/archify/ATTRIBUTION.md)。下游适配不改写这些原始文件。

此仓库包含可分发 Skill 与测试；个人项目地图、会话原文、本机预览状态及临时诊断不属于发布内容。
