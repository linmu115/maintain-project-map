# maintain-project-map

辅助长期开发的软件、工作流与 Skill 维护项目认识：需求、设计、对象、模块、接口、实现、验证和来源。一项目一地图，原始资料使用 Markdown/YAML 和 Git 保存。

## 安装到 Codex

将本仓库的 `maintain-project-map` 文件夹复制到用户的 `.codex/skills/` 目录。入口为 [SKILL.md](maintain-project-map/SKILL.md)。在会话中说：

> 用 $maintain-project-map 为这个项目建立并维护地图。

Python 3.10+ 用于记录操作，安装 `maintain-project-map/requirements.txt` 中的依赖。图形导出另需 Node.js 18+，普通记录查询不要求渲染页面。

## 包含的能力

- 稳定项目 ID 与本机位置登记，跨项目用简短 ID 引用。
- [系统地图](maintain-project-map/references/system-maps.md)：明确收录独立项目，派生接口目录和交叉关系；系统图的项目护照通过“进入项目”新开完整项目阅读页，原标签页保持位置。含[可运行示例](maintain-project-map/examples/system-map/README.md)。
- 绑定已有需求文档的章节或表格行，避免复制一套规格。
- 按需采用[组合项目与扩展接口](maintain-project-map/references/composite-projects.md)的组织指引：职责层级、提供方唯一合同、具体能力的接入依据，以及 Archify 模块边界和泳道。
- 模块目录自动生成 B 可展开侧栏；Mistune 解析 Markdown，标准文档链接和 Wiki 链接连接记录、章节及已声明原资料。同义反向关系合并显示。
- 记录合并、退役和失败探索分别表达；实现与验证独立存储。
- 按名称、别名、正文检索；支持检索明确指定的 Codex 可见会话记录。
- 模块范围查询、有限接口目录和反向关系查询，支持只核对当前记录及来源的续读指纹；不要求模型读取全图。
- 按需生成两种人读页面：项目概览、项目条目。白色为主的阅读界面、独立滚动、文档内按点击激活的画布。
- 复用固定版本 Archify 的图模型、校验和阅读器，保留原版及嵌入副本。画布视窗固定，内部内容缩放和平移。
- 图节点对应的条目直接进入语义护照；顶栏返回恢复页面、滚动与图中视野。正文可链接并居中图卡片。
- [更新记录](maintain-project-map/references/update-records.md)保存用户明确要求留存的迭代，按日期浏览；普通维护不会自动追加。

本地 HTTP 服务仅用于阅读导出快照。页面操作不调用模型；提问继续使用原会话。没有长期对照证据证明 Skill 已降低 token 成本或提高开发成功率。

## Skill 自身的项目地图

本仓库同时维护 [自身地图](docs/project/map.md)、[地图清单](docs/project/project.yaml)和[设计方案](设计方案.md)。地图包含需求、模块、接口、实现与独立验证记录，以及可编辑的 Archify 图源；保留原项目和记录 ID。`research/` 中的早期检查是历史证据，不代表当前版本的测试结果或长期收益。

克隆仓库并安装上述依赖后，在仓库根目录生成并启动交互阅读页面：

```sh
python maintain-project-map/scripts/render_map.py docs/project/project.yaml
```

命令返回本机 HTTP 阅读地址。HTML、运行端口和预览回执可重新生成，不提交到仓库；无需开发者原有目录或个人会话文件。GitHub 上可直接阅读 Markdown，Wiki 条目链接和图节点交互由生成的阅读器提供。

## 开发与检查

```sh
python -m pip install -r maintain-project-map/requirements.txt
python -m pytest tests maintain-project-map/tests
```

测试需要 pytest 和可用的 Node.js。项目接入说明见[本地操作](maintain-project-map/references/operations.md)。

## 第三方代码

Archify 固定于 `d673e8300df60a5c8166abe78787fdc78f6b8000`，原始文件摘要及 MIT/字体许可保留于 [归属说明](maintain-project-map/assets/vendor/archify/ATTRIBUTION.md)。下游适配不改写这些原始文件。

此仓库包含可分发 Skill、测试及 Skill 自身的项目地图；其他个人项目地图、会话原文、本机预览状态及临时诊断不属于发布内容。
