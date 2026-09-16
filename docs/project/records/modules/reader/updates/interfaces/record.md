---
id: IF-update-record
kind: interface
title: 一次迭代怎样成为更新记录
status: current
summary: 明确请求留存后新增有日期的 update 文档；图链接使用图类型和稳定节点 ID。
sources:
- path: ../../maintain-project-map/references/update-records.md
  role: skill-source-authority
- path: ../../maintain-project-map/scripts/project_map.py
  role: skill-source-authority
- path: ../../maintain-project-map/scripts/reader_content.py
  role: skill-source-authority
---

# 一次迭代怎样成为更新记录

输入是开发者明确提出的留存请求和这次迭代已完成的功能变化。输出是一份带唯一 ID、kind: update、title、date、summary 及正文的 Markdown；date 必须是 YYYY-MM-DD。来源指出这次请求，功能细节和验证证据按需链接原记录。

正式格式及例子由 [Skill 的按需说明](../../../../../../../maintain-project-map/references/update-records.md) 提供，本页是面向使用者的入口；不另外维护一份矛盾的 schema。

正文可以写 `[交接位置](map-node:workflow/实际节点ID)` 或 architecture 对应链接。作者先核查图源中的实际 ID；页面遇到已删除的节点会提示，不能把别的节点冒充旧位置。原记录普通链接仍按 [[IF-document-links|文档链接约定]] 处理。

已接入：[[MOD-updates|更新记录阅读]]读取这些文档；[[MOD-document-navigation|文档导航]]把图链接转为当前页定位；[[MOD-archify|图适配]]调用原生相机居中，语义护照中的按钮可打开正式项目条目。
