---
id: VER-public-map
kind: verification
title: 安装与在线地图发布检查
status: current
summary: 记录当前安装包一致性、公共导出及 GitHub Pages 发布的实际检查范围。
relations:
  - relation: verifies
    to:
      record_id: IMP-public-map
---

2026-09-19 公共导出加入后的完整回归 147 项通过（135.58 秒）。之后发现 Git 自动换行会改变归档原文字节，增加归档目录属性与真实 Git 往返检查；源码/归档及公共导出的 16 项针对性检查通过（34.36 秒）。

公共导出检查覆盖：缺少本机 capture 时仍保留公开历程、完全不调用原始证据读取、无事件目录与取证映射、来源超出显式根目录时拒绝、输出目录存在旧文件时拒绝。自身地图两张图均通过 9/9 原生交付检查，归档原文单独生成；本机路径没有出现在公共产物中。

自身源码文本统一 LF，第三方原始资产与归档保留原字节。这样 GitHub 构建的来源指纹与维护工作区一致，归档原文的校验也不受 Windows/Linux 换行转换影响。

待提交 Git tree 解包到独立临时目录后，使用原发布命令重新构建成功：80 条记录结构有效，两张图均生成，旧实现归档页存在，来源基线没有出现换行造成的待复核；没有事件目录。143 个 Skill 分发文件与本机安装版逐一校验一致，两份自身地图继续沿用既有位置和项目 ID。

远程发布结果在 [GitHub Actions](https://github.com/linmu115/maintain-project-map/actions/workflows/project-map-pages.yml) 与对应部署中核查；本机生成成功本身不作为网站已上线的证据。

首次线上实测：提交 `58c27c7` 的 [构建与部署](https://github.com/linmu115/maintain-project-map/actions/runs/35433170806) 成功。浏览器实际打开 Pages 首页，验证在线发布文档跳转与返回、架构图渲染、旧 ID 的短定位和独立归档原文，以及任务历程的本机证据提示；页面没有要求读者启动本地服务。
