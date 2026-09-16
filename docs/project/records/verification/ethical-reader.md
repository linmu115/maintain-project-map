---
id: VER-ethical-reader
kind: verification
title: Ethical 样式与引导布局检查
status: partial
summary: 阅读相关 28 项回归通过，实际检查桌面和 375px 窄屏的引导展开、章节切换与内容溢出。
relations:
  - relation: verifies
    to: {record_id: REQ-ethical-reader}
  - relation: verifies
    to: {record_id: MOD-reader}
---

# Ethical 样式与引导布局检查

2026-09-15。使用 ui-ux-pro-max 的 accessible-and-ethical 条目作为风格依据；通用设计系统自动推荐的 Swiss 风格未作为本次依据。

## 问题与检查

- 改动前，真实嵌入页引导区被限制在 154px。标题/说明区域 clientHeight 65px 而 scrollHeight 86px；章节区 clientHeight 28px 而 scrollHeight 55px，两者 overflow:hidden。这直接造成截图中的裁切。
- 改动后，图内引导默认可折叠；展开后的网格按 max-content 排行。桌面“带图阅读”状态的文字区高度与内容高度均为 187px，章节区均为 56px。内容超出引导区时使用可见滚动条，而不是压缩内部网格。
- 375px 窄屏下，引导文字区高度与内容高度均为 318px、章节区均为 108px；引导区宽度与 scrollWidth 均为 312px，父文档宽度与视口同为 375px，没有横向溢出。
- 在实际浏览器通过键盘完成图形选中、引导展开和首章切换，截图核对了约 891px 默认窗口、1280×1000 和 375×812。临时视口在检查后恢复。
- 阅读导出、图内相机、图形选择层共 28 项回归通过。生成的主页面和两份图形 JavaScript 通过语法检查，原生图导出无错误。
- 主文字 #202e29/白色为 14.15:1；辅助文字 #46574f/#f3f5f2 约 7.00:1；白色/#24533f 为 8.81:1；标签 #284736/#e4eee7 为 8.65:1。

## 边界

这不是完整 WCAG 合规认证；未完成屏幕阅读器、多操作系统、所有原生弹窗、所有作者图源和长期模型收益验证。SVG 内部字号和坐标仍由原生图源控制，图的实际可读性与缩放有关。浏览器部分跨 iframe 指针操作存在工具的小数坐标检查限制，本次以键盘和真实 DOM/截图核对引导布局。

源与安装版的分发文件核对及上游固定文件哈希检查另外随本次交付执行；上游原版页面不套用下游主题。
