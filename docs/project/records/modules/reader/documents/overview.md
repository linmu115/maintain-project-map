---
id: MOD-document-navigation
kind: module
title: 目录、Markdown 与文档跳转
status: current
summary: 文件夹成为人读目录，Markdown 和 Wiki 链接连接记录、章节及明确声明的原资料。
sources:
- path: ../../maintain-project-map/scripts/reader_content.py
  role: skill-source-authority
- path: ../../maintain-project-map/scripts/reader_markdown.py
  role: skill-source-authority
- path: ../../maintain-project-map/references/reading-and-interaction.md
  role: skill-source-authority
relations:
- relation: consumes
  to:
    record_id: IF-record-data
- relation: provides
  to:
    record_id: IF-document-links
---

# 目录、Markdown 与文档跳转


[reader_content.py](../../../../../../maintain-project-map/scripts/reader_content.py) 根据真实目录生成 B 层级，并建立路径与记录身份的对应；[reader_markdown.py](../../../../../../maintain-project-map/scripts/reader_markdown.py) 复用 Mistune 解析语法。模块概览提供文件夹的可读名称，搜索保留并展开祖先目录。

提供方正文可跳到消费方接入说明，再返回唯一合同。原始合同或源码只在直接引用且已声明时打包为阅读快照；页面显示来源和独立指纹，不把它变成新的权威记录，也不递归抓取整仓库文档。

链接写法、重名处理和移动文件后的规则见 [[IF-document-links]]。这部分服务阅读导出；LLM 的常规查询仍使用原记录。图形内搜索与路径查询交给 [[MOD-archify|Archify]]，没有重复编写图算法。

页面历史保存上一阅读状态，包含搜索、目录与文档滚动位置；图中的相机和所选卡片通过嵌入桥接恢复。图位置链接可以从更新或普通正文进入相应图并居中卡片，具体使用见 [[IMP-passport-updates-history]]。
