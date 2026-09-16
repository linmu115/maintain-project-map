---
id: MOD-reader
kind: module
title: 阅读页面：文档、图与本机入口
status: current
summary: 以同一份记录生成 A/B 页面，目录与正文互链，图形复用 Archify；页面交互不调用模型。
sources:
- path: ../../maintain-project-map/scripts/render_map.py
  role: skill-source-authority
- path: ../../maintain-project-map/assets/reader.html
  role: skill-source-authority
- path: ../../maintain-project-map/assets/reader.css
  role: skill-source-authority
- path: ../../maintain-project-map/references/reading-and-interaction.md
  role: skill-source-authority
relations:
- relation: consumes
  to:
    record_id: IF-map-query
- relation: contains
  to:
    record_id: MOD-document-navigation
- relation: contains
  to:
    record_id: MOD-archify
- relation: contains
  to:
    record_id: MOD-http
- relation: implements
  to:
    record_id: REQ-reader-navigation
- relation: implements
  to:
    record_id: REQ-canvas-reader
- relation: implements
  to:
    record_id: REQ-linear-reader
- relation: implements
  to:
    record_id: REQ-http-entry
---

# 阅读页面：文档、图与本机入口


## 开发者怎样阅读

项目概览分别展示说明与规格、整体组织和功能路径；项目条目围绕一个对象阅读说明、现状和关系。顶栏固定，侧栏与正文独立滚动，默认白色/黑色风格。搜索和目录展开在本地完成。

点击文档内的图窗口后才切换为画布缩放、拖动；点击外部返回文档滚动。边框和视窗固定，只移动内部图形。提问继续通过当前会话，阅读器不另设输入框。

## 内部模块与交接

- [[MOD-document-navigation|目录与正文链接]]：从 records 层级生成目录，用 Mistune 解析 Markdown，并按 ID、章节和已声明来源跳转。
- [[MOD-archify|原生图适配]]：调用已有 Archify 校验/交付，再保留原版和黑白嵌入副本；图节点与记录单独绑定。
- [[MOD-updates|更新记录阅读]]：展示开发者明确选择留存的功能迭代；没有更新时显示空状态。
- [[MOD-http|本机预览]]：只提供已生成页面和图形，复用仍在运行的阅读地址。

生成入口是 [render_map.py](../../../../../maintain-project-map/scripts/render_map.py)，行为约定在 [阅读与交互](../../../../../maintain-project-map/references/reading-and-interaction.md)。记录由 [[IF-map-query|记录引擎]] 加载，图源出错时保留正文和诊断。修改源码后要重新导出并刷新，旧页面只是原来的快照。

语义护照直接连接项目条目，正文图链接居中卡片，顶栏返回恢复图与文档位置，见 [[IMP-passport-updates-history]]。更新条目的写入需要开发者明确请求；生成页面本身不会创建迭代记录。
