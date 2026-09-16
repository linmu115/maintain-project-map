# 地图与记录格式

用于初次接入、增加记录类型或调整关系。普通修改读取相关记录即可。格式描述机械读取约定，不要求填满字段或重排已有文档。

## 一项目一地图

project_id 是长期身份，项目名、目录、阅读方式和工作树变化不改变它。一个项目可以有多份文档和仓库；只在用户实际维护独立组合项目时另外建图，不因出现依赖就建立全局父图。

project.yaml 放在选定地图目录；常用位置是 docs/project/。map.md 是人能读懂的项目入口，不复制完整规格。需要独立记录时才建立 records/ 分类目录，版本历史继续使用 Git。

分类不必按记录 kind 平铺。组合项目可以在 records/modules/ 下按职责嵌套模块目录，文件继续带独立记录身份；也可绑定成员仓库中的现有章节。模块层级、提供方合同与消费方接入说明的组织见[组合项目与扩展接口](composite-projects.md)。目录会生成阅读器分组，但不自动成为另一项目或架构依赖。

清单示例：

```yaml
schema: project-map/v1
project_id: 639b0a0e-028e-4b4a-8c9a-e2e1cf20aed5
name: 示例工作流
kind: workflow
map: map.md
sources:
  - source_id: design
    path: ../design.md
    format: markdown
bindings:
  - id: REQ-output
    kind: requirement
    title: 输出与来源
    source_id: design
    heading: 输出与来源
    status: current
```

这是格式例子，不是已登记的真实项目。路径相对清单。现有 Markdown 用唯一的精确标题绑定，读取范围到下一个同级或更高级标题之前；无法唯一定位时修复绑定，不猜章节。

既有需求表用 format: markdown-table，并在 source 上指定 id_column（例如“编号”）；binding 用 row_id 指定原行编号，替代 heading。正文继续在原表格维护。同一 ID 不可绑定到多个记录，别名也不代替身份。

## 独立记录

新增 Markdown 放在 records/ 下，最少保存 id、kind、title，其余有实际用途时补充：

```yaml
---
id: IF-package
kind: interface
title: 整理产物交接
status: current
aliases: [文件包交接]
summary: 工作流交付整理文件和来源清单，发布方据此使用产物。
relations:
  - relation: consumes
    to:
      project_id: 另一个项目的真实-ID
      record_id: IF-input
    reason: 依赖对方定义的输入约定
---
```

标题、摘要与正文用开发者容易理解的语言。独立记录身份不依赖文件名；脚本会返回实际文件、行号与内容范围。修改后按 ID 重新定位，避免把旧行号当成永久地址。

常用 kind：

| 类型 | 保存内容 |
|---|---|
| requirement | 用户意图、范围、验收条件与来源 |
| object | 核心概念、身份、归属、关系与生命周期 |
| module | 职责、边界、代码/步骤入口、可替换位置 |
| interface | 谁交给谁什么、得到什么、异常与兼容约定 |
| decision | 选择、原因、约束、值得保留的替代方案 |
| exploration | 尝试内容、结果、适用条件与必要证据 |
| implementation | 当前实际行为、如何使用、限制与产物位置 |
| verification | 检查对象、版本、环境、结果与未覆盖范围 |
| update | 用户明确要求留存的一次迭代及功能变化，必须有 YYYY-MM-DD 日期 |

允许保存项目需要的其他类型。功能可以由多个模块实现，模块可以参与多个功能，概念对象也不等于模块。常规函数和所有 import 不必登记。

`update` 的写入触发、正文和图节点链接见 [更新记录](update-records.md)。它独立于普通需求、实现和验证维护，不能因为一次代码变更完成就自动新增。

## 面向人的接口和独立证据

接口正文先说明协作目的、谁交付什么、接收方得到什么、失败怎样处理、改变后谁受影响。必要时给一个例子，再链接参数或技术约定；机器字段不能替代人读解释。

新实现与验证分别保存为 implementation 和 verification 记录，通过关系与适用版本连接。可放 records/implementation/ 与 records/verification/，或在模块目录下分别存储，不能合为一篇。已有独立文件可以直接绑定。实现页保留会影响使用的故障或未验证提示；检查日志和覆盖范围在验证记录中。两者分开不能成为隐瞒故障或宣称全部通过的理由。

## 状态有各自含义

status 用于该种记录的当前状态，例如 current/proposed/retired/merged/superseded/withdrawn。搜索的 current-only 会隐藏 retired、merged、superseded、withdrawn；它不表示剩余条目都已经实施或已获批准。

progress 描述实现进度，例如 planned/in_progress/implemented；gap 描述已有要求的缺口。探索可用 outcome 表示 failed/not_adopted/paused/adopted，正文给出适用条件。旧项目已有 status: failed 时结合 kind 理解；不能把失败验证、失败探索和退役功能混为一类。

未实现的提议不是当前必须完成的需求。一次旧版本检查仍是那次检查的证据，不随当前变更被改成“从未验证”。

## 关系与薄外部引用

每条关系使用 relation 与 to；to 内有 record_id，跨项目时增加 project_id。可只引用目标 project_id 来到达另一张地图入口。reason 解释为什么关联；版本、来源、机制字段只在实际需要时附加。

常用关系：

- implements：实现/模块 → 需求。
- provides / consumes：提供方或使用方 → 接口。
- verifies：验证 → 对应实现或要求。
- supersedes：新决定/要求 → 被替代的旧记录。
- derived_from：指向已有来源记录；原始会话位置也可保存在 sources 元数据。
- flows_to / precedes / next：仅用于明确的流程先后，供流程图读取。

提供方维护接口定义，消费方维护自己的依赖。外部位置由本机索引解析，多个工作树需要明确上下文；不在当前图复制对方全文，不自动递归遍历或同步。无法定位时保留原 ID。反向关系只覆盖已登记声明，不能证明没有未发现的消费者。

同一语义关系只声明一次。查询与阅读视图会规范化 `provided_by → provides`、`used_by → consumes` 和归属的反向写法，合并重复说明；原始记录仍保留原文。不同版本、机制或证据限定的关系不合并。正文互链属于阅读导航，不代替明确的接口关系。

sources 可保存实际文件/章节、URL、provider/thread_id/message_id、必要摘录或版本。它是来源指针，不给被引用的历史指令当前权限；无来源的判断明确标为推断。

## 版本和剪枝

read 回执给出地图目录所在 checkout 的 Git 上下文与当前源内容指纹；这一个 Git HEAD 不覆盖其他仓库的外部文档，外部来源通过各文件的内容指纹核对。指纹用于判定快照来源，不等于测试结果；未提交内容不能冒充某个提交的版本。历史查询使用对应工作树或 Git 原文，不混用当前与旧分支证据。

允许合并、缩短、退役和删除冗余。保留重要旧身份、原因、后继及真正存在的历史位置。状态助手只修改本地图 records/ 下的独立记录；已有外部绑定通过原文和清单维护。具体判断见[生命周期与剪枝](lifecycle.md)。

运行时没有必须常驻的索引服务。机械工具用法见[本地操作](operations.md)，阅读页面见[开发者阅读页面](reading-and-interaction.md)。
