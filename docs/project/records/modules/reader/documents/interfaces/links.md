---
id: IF-document-links
kind: interface
title: 文档链接与章节定位
status: current
summary: 普通相对链接与 Wiki ID 共用记录身份；标题重名不猜目标，原资料读取有明确范围。
sources:
- path: ../../maintain-project-map/references/reading-and-interaction.md
  role: skill-source-authority
- path: ../../maintain-project-map/scripts/reader_content.py
  role: skill-source-authority
- path: ../../maintain-project-map/scripts/reader_markdown.py
  role: skill-source-authority
relations:
- relation: consumes
  to:
    record_id: IF-record-data
---

# 文档链接与章节定位


作者可以写标准 Markdown 相对链接，也可以用 `[[记录ID#章节|显示名称]]`。例如主页的 [[IF-map-query|查询说明]] 直接指向本地图的一份接口介绍，而不会复制正文。

稳定 ID 不随文件移动改变；相对路径在移动时仍需修正。Wiki 可匹配唯一标题、别名或文件名；重名时保留未解析提示，作者用 ID 或完整路径消歧。具体规则以 [阅读与交互](../../../../../../../maintain-project-map/references/reading-and-interaction.md) 为唯一完整说明。

原资料要在来源元数据中声明，正文再链接它。当前阅读快照支持常见文本文件并设单文件 2 MiB 上限；未知、失效或超出范围的目标保留定位信息。它没有任意文件浏览服务。

此接口的使用方是记录作者与 A/B 阅读页面。链接只表示“到这里读”，不证明提供/消费、调用顺序或数据归属。
