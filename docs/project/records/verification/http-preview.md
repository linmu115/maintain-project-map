---
id: VER-http-preview
kind: verification
title: 默认 HTTP 阅读入口的检查范围
status: verified
summary: 7 项 HTTP 专项检查及全部 51 项功能检查通过；浏览器视觉不在本次检查范围内。
relations:
  - relation: verifies
    to: {record_id: REQ-http-entry}
  - relation: verifies
    to: {record_id: IMP-release}
---

# 默认 HTTP 阅读入口的检查范围

2026-09-15，Python 在隔离的临时项目中运行真实本地服务与命令入口。

## 已执行

`tests/test_http_preview.py` 的 7 项检查通过：

- 中文 HTML 与相对图形链接通过 HTTP 返回，响应禁用旧内容缓存。
- 同一输出位置重复启动复用地址与进程，文件更新后返回新字节。
- 非导出文件、路径穿越、无预览标识的访问、外来 Host/Origin 及普通页面写入请求被拒绝。
- 可以查询、停止和重新启动服务；停止不依赖回执中的 PID 去终止系统进程。
- 不覆盖非本服务的回执文件；可恢复已经失效的本服务回执。
- 两个独立进程同时启动同一入口时复用同一个服务。
- `render_map.py` 默认返回 HTTP 地址，`--export-only` 只生成离线文件。

组合执行 `python -m pytest maintain-project-map/tests tests -q`：51 项通过，耗时 36.35 秒。安装目录的官方 Skill 结构检查通过，44 个交付文件与源目录逐一匹配。

## 边界

检查使用合成页面和测试地图，不代表浏览器截图、A/B/C 全流程操作、窄屏布局或长期模型效果已经验收。服务的 8 小时空闲退出由代码配置，未等待 8 小时做时长实测。浏览器工具此前的协议限制没有被修改。
