---
id: VER-passport-updates-history
kind: verification
title: 语义护照、更新记录与返回的检查范围
status: current
summary: 83 项回归检查通过；浏览器核对条目跳转、卡片居中、相机与正文滚动恢复。真实项目的更新列表不自动填入测试记录。
relations:
  - relation: verifies
    to:
      record_id: IMP-passport-updates-history
  - relation: verifies
    to:
      record_id: REQ-passport-updates-history
---

# 语义护照、更新记录与返回的检查范围

2026-09-16，在本机开发版本运行 `pytest tests maintain-project-map/tests -q`，83 项通过。覆盖原有记录与绑定、原生交付、HTTP 预览、画布激活和相机行为；新增检查包括日期有效性、普通导出不生成更新记录、图节点链接身份、护照多记录绑定、无抽屉、URL 与历史恢复、相机快照还原。

浏览器使用独立示例地图核对：更新列表按日期排列；打开更新并点击图链接后，卡片中心与 SVG 视窗中心偏差小于 0.001 像素；键盘激活卡片后的语义护照包含节点名称与全部条目按钮；进入条目再返回，相机矩阵保持一致，选中状态恢复；正文滚动在离开前后都为 858.666687 像素。

测试示例的更新记录仅存在于临时测试目录。正式地图不会因为本次实现更新记录功能而自动新增 update 条目。

这些检查支持阅读与数据格式行为，不能证明 LLM 会在所有未来对话中正确判断更新范围，也没有检验后续项目开发的 token 成本或质量收益。历史图按需从 Git 查回；图位置链接使用当前导出的图。
