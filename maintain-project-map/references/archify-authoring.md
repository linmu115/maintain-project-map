# Archify 图源维护

仅在新增、修改、比较架构或流程图时阅读。普通需求更新、检索和记录剪枝不要求加载本文或重画全图。

## 资料与嵌入边界

Archify JSON 是图的原始资料，沿用上游 schema；本 Skill 只登记文件和节点关联，并把原生阅读器嵌入 A/B。项目 ID、需求与设计正文、实现和验证、来源及记录生命周期是补充资料，不冒充 Archify 的原生字段。上游 lifecycle 是状态机图，migrate 是工作流格式迁移，二者不等于项目记录退役。

在 project.yaml 中声明需要的图，路径相对该清单：

```yaml
archify:
  architecture:
    source: diagrams/architecture.json
    node_records:
      record-engine: [MOD-records, IF-storage]
      human-reader: [MOD-reader]
    # 只有架构图需要核对仓库证据时才指定：
    # repo_root: ../..
  workflow:
    source: diagrams/workflow.json
    node_records:
      load-records: [MOD-records]
      render-reader: [MOD-reader]
```

node_records 的键是图内原节点 ID，值是本地图记录 ID 数组。映射不改图，不复制关系，不强迫每个节点都有文档。一条记录可出现在多个节点下。外部项目仍通过项目记录的轻量 ID 引用连接。

未声明图时不自动扫描或从文档顺序生成图。已有 views/architecture.json 等派生文件也不自动成为图源；采用已有图时，将经过检查的原始 JSON 登记为资料，避免导出覆盖来源。

## 编写图源

当图涉及组合项目、嵌套模块或对外扩展接口时，先应用[组合项目与扩展接口](composite-projects.md)的职责与接入判断。架构图用 boundaries 表达真实归属，流程图按参与者选用 lanes / groups；相关内部功能和接口必须可定位。只把插件各画成一个节点、把所有步骤放入“正常/异常”两行，不能算已说明这种项目的内部组织。

选择实际需要的格式，按需读取[架构 schema](../assets/vendor/archify/schemas/architecture.schema.json)或[工作流 schema](../assets/vendor/archify/schemas/workflow.schema.json)及其[公共定义](../assets/vendor/archify/schemas/common.schema.json)。遇到复杂布局再查[上游编写约定](../assets/vendor/archify/references/authoring-contract.md)和邻近的 examples，不必一次读完全部资料。

保留已有原生 ID 与合法的布局、边界、泳道、分组、条件、分支、回路、路径和引导视图。不要为了适配记录 ID 重命名图节点，也不要为了通过检查删除有意义的关系文字。新工作流通常使用 schema v2；旧图有固定坐标时，不只改版本号。关系来自已确认的设计或明确来源；位置接近、普通依赖和阅读顺序不证明流程先后或运行时影响。

新增或改变语义时由 LLM 根据项目材料选择节点和关系，脚本不替代这一步判断。跨文件修改涉及含义时，同步相关说明和节点映射；纯文字修订不要求重建无关图。退役记录仍被引用时应检查映射与图源，不能静默删节点或把失败探索当作曾存在的功能。

## 原生命令

下面的 `<skill>` 为安装目录，输入是明确的原始 JSON；`<output>` 为产物目录。正常地图生成仍使用 render_map.py，它会调用原生交付并导出浅色副本。需要单独排错、比较或编写图时再使用这些命令：

```text
node "<skill>/assets/vendor/archify/bin/archify.mjs" validate architecture "<source>/architecture.json" --json
node "<skill>/assets/vendor/archify/bin/archify.mjs" deliver architecture "<source>/architecture.json" "<output>/architecture.native.html" --json
node "<skill>/assets/vendor/archify/bin/archify.mjs" compare architecture "<source>/base.json" "<source>/head.json" "<output>/architecture.compare.html" --receipt "<output>/architecture.compare.json" --json
node "<skill>/assets/vendor/archify/bin/archify.mjs" preview workflow "<source>/workflow.json" "<output>/workflow.preview.html" --no-open
```

validate/deliver 可把 architecture 换成 workflow。架构证据检查需要时显式传 `--repo-root "<repository>"`。比较的是两份指定图源；版本与工作树选择交给 Git。preview 仅用于需要持续预览的图源编写过程，监听一个指定文件，结束时停止；它与默认 A/B HTTP 阅读服务分别工作，不是普通开发的常驻要求。原生 preview 会保留最近成功版本，当前候选失败时不能将旧画面说成本次成功。更多参数按需查 CLI `--help` 或[上游交付说明](../assets/vendor/archify/references/delivery-contract.md)。

## 结果与证据

导出快照使用同一次加载的图源字节和指纹。原生交付成功后保留 `<kind>.native.html`，浅色适配写入 `<kind>.html`；`<kind>.receipt.json` 分别记录图源、原生文件和适配文件的哈希。原生回执只证明对应原版文件，不能挪用为浅色副本的视觉验收。

无效图源或交付失败只使该图不可用；保留诊断与原始资料，记录阅读仍可继续。无效节点映射不能制造关联，需查明节点或记录是否更名、移除或退役。图通过确定性检查、浏览器实际检查、开发功能验证是不同结论，按实际范围记录，不互相替代。

图内使用明确的远程品牌 URL 时，上游素材获取可能联网；本地图源校验与页面阅读不调用模型。不要为普通记录维护附加全图重渲染、浏览器检查或固定汇报流程。
