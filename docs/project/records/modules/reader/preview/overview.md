---
id: MOD-http
kind: module
title: 本机阅读服务
status: current
summary: 启动或复用只读预览，为已生成地图返回本机 HTTP 地址。
sources:
- path: ../../maintain-project-map/scripts/serve_map.py
  role: skill-source-authority
- path: ../../maintain-project-map/references/operations.md
  role: skill-source-authority
relations:
- relation: provides
  to:
    record_id: IF-http-preview
- relation: implements
  to:
    record_id: REQ-http-entry
---

# 本机阅读服务


[serve_map.py](../../../../../../maintain-project-map/scripts/serve_map.py) 接收已经存在的 HTML 入口，返回本机地址。相同输出位置的服务仍在运行时复用；内容变更后导出并刷新即可。退出或重启后重新启动，地址可能变化。

服务只读指定导出文件和相邻图形，不浏览原始项目目录，不后台维护地图，不调用模型。默认空闲 8 小时退出，可通过状态/停止命令管理。操作说明见 [[IF-http-preview]]。

服务回执属于本机运行状态，不能拿 URL 当项目长期身份。持久位置由 [[MOD-locate|项目登记]] 管理。服务不可用时 HTML 仍是可选离线交付，状态须分别说明。
