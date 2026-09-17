---
id: VER-map-catalog
kind: verification
title: 本机地图定位的验证范围
status: current
summary: 验证别名、重名、默认位置、失效路径、分页和与原注册表的兼容性；盘点结果不等同于全机无遗漏证明。
relations:
- relation: verifies
  to:
    record_id: IMP-map-catalog
sources:
- path: ../../maintain-project-map/tests/test_map_catalog.py
  role: verification
---

# 本机地图定位的验证范围

2026-09-17，新增 6 项自动检查覆盖旧格式登记兼容、别名与大小写、ID 优先、同名歧义、登记幂等、当前位置与默认位置、默认失效不回退、损坏清单隔离、身份不符、分页边界以及拒绝 MRS 研究地图。地图核心共 38 项检查通过。

本机 10 个项目、11 个登记工作位置均能读取清单，所有项目名称可定位；Skill 自身两个副本使用明确的默认位置。登记仅核对清单和入口存在性，没有宣称这些项目的所有内容与实现均已验证。

盘点使用清单文件名扫描当前用户目录、D 盘和 C 盘部分非系统目录，排除依赖、版本控制内部目录和应用系统目录。访问受限的系统目录、两处无法访问的旧教材路径未覆盖。历史副本、样例及测试夹具留在盘点说明而不作为当前项目；MRS 研究地图不在范围内。后续新建、搬迁及更新时由 Skill 主动登记，没有后台监听或每次全盘扫描。
