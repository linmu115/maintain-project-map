# 系统地图

只在组合独立地图、维护系统接口目录或实现系统阅读入口时读取。普通项目内部的多插件组织仍用[组合项目](composite-projects.md)，不按安装包数量自动拆图。

## 选择范围

系统地图是一张有自己身份的维护资产，围绕用户选定的开发对象汇集独立地图。先确认哪些已收录、哪些只是外部依赖、哪些关系仍待核实。强耦合、目录相邻或一条依赖线都不自动扩大收录范围。项目可被多个系统引用，不具有唯一父级；循环、交叉和共享接口照实表示。

系统只维护系统边界、跨项目要求和系统级决定。接口正文属于提供方，消费方的接入说明写清调用哪项能力、影响哪些功能；同一接口仅一份权威定义。不同 Adapter 家族分别建接口记录，可用 `interface_family` 分类。提供关系用 `provides`、调用关系用 `consumes`；关系只声明一次，工具派生反向目录。包依赖不自动等于调用所有接口。

## 最小配置

沿用 `project-map/v1`，增加 `kind: system`，不迁移已有项目身份。`system.members` 仅列明确收录地图；可以使用本机项目注册表，也可提供相对路径明确选定一个工作树。

```yaml
schema: project-map/v1
project_id: your-stable-system-id
name: 我的协作系统
kind: system
map: map.md
system:
  members:
    - project_id: provider-project-id
      role: 提供引用身份与提交接口
      scope: 引用协作范围
      # 可省略 manifest，此时按本机 registry 解析；有多处工作树不猜选。
      manifest: ../../provider/docs/project/project.yaml
      diagram: architecture
      # 可选：node 为目标项目图中的稳定节点 ID
      node: reference-api
archify:
  architecture:
    source: diagrams/system.architecture.json
    node_projects:
      provider-card: provider-project-id
    node_records:
      provider-card: [DEC-scope]
```

`node_projects` 把原生 Archify 节点绑定到明确收录的项目 ID。图身份是“项目 ID + architecture/workflow”；相对图源文件可移动，声明的身份保持。`node_records` 仍关联系统自己的记录。项目卡片可多处引用同一项目，不复制项目合同。

系统只声明 `architecture`，不声明 `workflow`。普通项目仍独立保留两种图。图源使用原生组件、边界框和连接，不把目录层级强制画成执行顺序；边界和依赖的证据仍需作者核实。示例见 `examples/system-map`，它不代表用户实际项目分组。

## 阅读与打开项目

阅读器按 `kind` 展示系统概览、接口与关联、收录项目、更新记录。聚合页只带接口摘要、来源指纹、提供方和已登记消费者，不复制完整合同。

点击系统图项目卡片先打开原生语义护照；“进入项目”是可见的新标签页链接。目标由本机预览服务在打开时按成员 ID 解析，必要时生成目标阅读页并启动或复用服务。新标签页包含目标项目自己的侧栏与声明的图，原标签页不导航、不重建画布。不要改成直接打开孤立的 `.native.html`，也不加跨项目 input/output 中间卡。

收录清单不存临时 HTTP 端口。未登记、多个工作树、图源/节点失效会显示缺口，不猜同名项目；快照后发生的变化在打开时再次检查，失败页保留具体原因，原系统页继续可用。浏览器阻止标签页时保留可右键打开的链接和提示。离线 `file:` 阅读可查看快照，跨项目入口需要本地 HTTP 阅读服务。

## 面向模型的直接查询

```text
python <skill>/scripts/project_map.py --help
python <skill>/scripts/project_map.py members <system> --limit 5
python <skill>/scripts/project_map.py interfaces <system> --query 引用 --limit 5
python <skill>/scripts/project_map.py impact <system> IF-reference --project provider-project-id --limit 10
python <skill>/scripts/project_map.py modules <project> --limit 8
python <skill>/scripts/project_map.py search <project> 引用 --module MOD-api --limit 5
python <skill>/scripts/project_map.py read <project> IF-reference --max-chars 3000
```

`members/interfaces/impact/modules` 返回 `total/truncated/next_offset`，用 `--offset` 继续。接口中嵌套的提供方与消费方也有数量及截断标记；用 `impact` 按接口读取剩余关系。成员无法解析会明确报告，反向目录仅覆盖本系统明确成员与实际声明，不递归加载其下级系统。不把未登记当成没有依赖。接口来源文件和 ID 是进入权威正文的入口。

模块范围首先使用记录的 `module_id`，否则由最近的模块 `overview.md/index.md/README.md` 推导。目录仅帮助查找归属；稳定身份仍是模块记录 ID。必要约束写进相关记录的正文或元数据，有限候选只是定位结果；正文显示部分读取时不得宣称约束已读全。

`read` 返回整图指纹和 `record_fingerprint`。用 `--record-fingerprint` 续读时只核对这一记录及其绑定源文件；无关记录变化不会阻止继续。绑定来源文件整体改变时保守地重新定位，避免拼接不一致的上下文。需要严格整图一致时仍可用 `--fingerprint`。

本地扫描不等于模型收到全部资料；完整 HTML/docs.json 供人阅读，不作为普通开发上下文。工具每次从当前文件派生查询，不要求新建数据库、预先读系统总览或读取所有祖先。已知源码位置的小任务可直接查源码。

## 局部维护

- 私有实现调整：维护本模块受影响记录。
- 图内细节变化：更新该图及节点绑定。
- 职责或收录变化：核对项目入口和相关系统说明。
- 接口语义、权限、生命周期变化：核对唯一合同、已登记消费者和相应验证；缺失关系回到源码搜索。
- 删除/合并：保留旧身份与后继，修复有关链接和节点。

接口聚合索引是派生结果，可重新生成；每个成员有自己的内容指纹，不用一个仓库的 HEAD 代表多个项目。导出的系统目录是快照，成员变化后按需重新生成系统阅读页，不需要重写所有系统记录。开发者更新记录仍只在用户明确要求时新增。实际实现和验证证据分别存储。

## 职责边界

Archify 负责单图模型、布局、渲染与校验；适配层和阅读器负责系统聚合、护照入口与页面导航；检索脚本负责有界查询。不要为这项扩展修改上游内核或另造版本控制。递归子图、MRS、成本 benchmark 和浏览器插件不由此流程自动启动。
