---
id: VER-native-archify
kind: verification
title: 原生 Archify 迁移与适配嵌入的检查范围
status: partial
summary: 已核对上游字节、原生交付与图源快照；界面行为经过代码执行检查，浏览器视觉尚未验收。
relations:
  - relation: verifies
    to: {record_id: REQ-native-archify}
  - relation: verifies
    to: {record_id: IMP-release}
---

# 原生 Archify 迁移与适配嵌入的检查范围

日期：2026-09-15。上游固定提交：d673e8300df60a5c8166abe78787fdc78f6b8000。

## 上游来源与原生命令

- 68 个上游文件共 2,334,674 字节，从固定提交 Git blob 原样复制；每个文件的哈希和字节数写入 PIN.json 并逐一核对。MIT 与第三方、字体许可保留。
- 原生 doctor：15 项通过。五种图类型的捆绑样例分别通过 deliver，每份 9/9 检查、showcase pass，错误及警告为 0，源与产物哈希符合回执。
- 原生 architecture compare：28/28 检查通过，base/head composition 均 pass。结论只覆盖指定图源的显式变化。
- 原生 workflow v1→v2 migrate：诊断为空，原源字节不变；迁移后 validate 为 9/9、showcase pass。
- 自身项目新架构图与流程图分别通过原生 validate/deliver，9/9、错误及警告为 0；图节点与项目记录绑定有效。

原始回执：.work/archify-native-smoke/results.json、audit.json、extended.json；自身图：.work/self-native-check/results.json、summary.json。它们是本次运行证据，未打包为 Skill 指令。

## 地图与适配检查

最终组合执行 `python -m pytest maintain-project-map/tests tests -q`：58 项全部通过，耗时 45.64 秒（引擎 32、阅读导出与原生嵌入 14、会话检索 5、HTTP 7）。源目录与安装目录均通过官方 Skill 结构检查；86 个交付文件逐一匹配，安装后的 68 个上游源文件再次核对哈希。

覆盖图源单次读取、原始 JSON 字段和 ID 保留、BOM/换行还原、多对多映射、图变更进入总指纹、图源及全部产物路径保护。错误图仅产生图诊断，记录仍可读取；上游校验失败保留先前文件但不将其链接为当前结果。

真实原生交付输出经过原版与浅色副本分别哈希核对。A/B/C 适配函数使用实际页面 JavaScript 做行为检查，覆盖原生聚焦 ID、多节点切换、无映射、失败图、C 仅流程图项目的概览与章节入口、首次展开和防重复插入。此项没有使用浏览器，不能证明实际排版与全部原生控件交互。

HTTP 检查包括原版图的允许链接，原有正文、浅色图及服务行为继续回归。Skill 入口正文没有增加原生说明书；图源指导在按需参考中。

## 独立使用与边界

独立子智能体在 .work/native-forward-use 建立四条记录的工作流项目，维护正常路径和修订返回，把一条记录关联两个原生节点，再仅修改原图并重新生成页面。此次检查发现并促成修复 C 原来仅展开架构图的遗漏。修复后 A/B/C 均重新导出，原生校验为 9/9，两个节点映射保留，图源和原版/浅色副本的回执哈希一致；C 实际展开逻辑由无浏览器函数测试另外覆盖。证据：.work/native-forward-use/evidence/forward-use-result.md。

这是一次限定场景的前向检查，没有不使用 Skill 的对照组，不能证明 token 节省或模型总体能力提升。浏览器视觉、窄屏、大图交互及原生单图实时预览未在本次验收。普通本地图浏览不调用模型；明确的远程品牌素材可能由上游联网获取。
