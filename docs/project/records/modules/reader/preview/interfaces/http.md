---
id: IF-http-preview
kind: interface
title: 阅读入口与预览状态
status: current
summary: 生成器交付 HTML 入口，预览服务返回可用地址或具体失败状态。
sources:
- path: ../../maintain-project-map/scripts/serve_map.py
  role: skill-source-authority
- path: ../../maintain-project-map/references/operations.md
  role: skill-source-authority
---

# 阅读入口与预览状态


提供方是本机服务，使用方是阅读生成器和开发者。调用 start 提供已生成入口后，获得当前 URL 与服务状态；status 查询可用性，stop 停止这份阅读服务。完整命令例子以 [本地操作](../../../../../../../maintain-project-map/references/operations.md) 为准。

同一服务运行期间复用地址，刷新读取磁盘上的最新导出；它不会自动从原项目重新生成。页面更新与源记录维护是两个动作。无法启动服务时保留已生成文件，并明确说明没有可用 HTTP 地址。

长期链接应指向项目/记录 ID 与可解析的资料位置。本机 URL 只适合当前阅读，不是发布网站，也不是跨设备共享接口。

## 系统项目进入

系统地图的 __project 入口只接受当前清单明确收录的项目 ID，以及图、记录或节点身份。点击后检查目标当前状态，按需生成完整项目阅读页并在新标签页打开；不同系统可共用同一目标服务，生成过程按目标串行，原系统页保持。失效身份不猜选，失败页显示原因。
