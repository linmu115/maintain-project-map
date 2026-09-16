---
id: VER-linear-reader
kind: verification
title: Linear 阅读工作区检查
status: current
summary: 29 项导出、导航与画布检查通过，并在 891、1280 和 375 像素宽的浏览器中检查阅读布局。
relations:
  - relation: verifies
    to: {record_id: REQ-linear-reader}
  - relation: verifies
    to: {record_id: MOD-reader}
---

# Linear 阅读工作区检查

2026-09-15，针对 reader.html、reader.css 和 diagram-theme.css 的黑白工作区改版。

## 自动检查

- test_reader_export.py、test_reader_navigation.py、test_canvas_camera.py 和 test_canvas_activation.py 合计 29 项通过。
- 导出后的入口、架构图和流程图内 JavaScript 通过语法检查；两个原生图交付无错误。
- 新增导航检查执行实际模板函数，覆盖旧地址兼容、含特殊字符的条目 ID、面板与页签恢复、前进后退时不额外写入历史、非法值回退。

## 浏览器检查

- 891 × 720：固定顶栏与左侧阅读方式、搜索；目录和正文均为独立的可滚动区域。条目查询可定位 Linear 需求，并保留命中的历史记录状态。
- 1280 × 900：条目正文与右侧现状并排，重复首标题已消除。连续文档可通过目录跳转到章节，刷新后同一章节距正文顶端约 28 像素，恢复定位。
- 375 × 812：目录默认收起，开关可展开，选择“说明与规格”后收起；文档宽度为 375 像素，正文内容没有横向溢出。临时视口尺寸已重置。
- 原生架构图和流程图采用黑白、中性灰；图未选中时 iframe 不接收指针，选中与“返回文档”切换可用。
- 浏览器返回恢复之前的面板；本次页面没有捕获到控制台错误。

## 范围

本次未重新执行全部原生图工具手势；滚轮缩放与拖动由既有相机和激活检查覆盖，不把这些自动检查描述为本次浏览器实际滚轮测试。未开展长期多轮有无 Skill 对照，也未证明模型效果提升或 token 成本下降。
