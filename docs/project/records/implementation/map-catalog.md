---
id: IMP-map-catalog
kind: implementation
title: 本机项目地图目录与名称查找
status: current
summary: 在原位置注册表上增加名称、别名、分页检查和默认位置，主动登记现有项目地图。
relations:
- relation: implements
  to:
    record_id: IF-project-location
sources:
- path: ../../maintain-project-map/scripts/map_catalog.py
  role: implementation
---

# 本机项目地图目录与名称查找

2026-09-17 新增轻量目录命令。注册时读取清单身份与名称，保留别名和多个位置；使用已有独占写锁与原子写入。名称查询只读取当前候选页的清单，不调用全图读取器，不读取日志正文。

明确的工作树优先于默认位置。默认位置不可用时保留候选并要求核对，不用文件修改时间猜测权威副本。原 ID 解析器支持同一默认字段，跨项目链接沿用现有协议。

本机登记了 10 个项目、11 个工作位置；项目地图 Skill 源稿与发布仓库共享一个身份，当前源稿明确设为默认。每台机器的实际路径保存在用户目录的 .codex/project-maps/registry.json，未打包进 Skill。盘点说明位于同目录的 inventory.md。

用户修正了初始范围：本次只维护项目地图，不纳入 MRS 研究地图。研究地图适配试写在安装前移除，未修改 B/C 题或其他研究文件。MRS 软件开发地图仍按普通项目登记。过程见 [[HIST-map-catalog]]，验证见 [[VER-map-catalog]]。
