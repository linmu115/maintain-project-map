# 本地操作

仅在需要脚本时读取。`<skill>` 表示当前 SKILL.md 所在目录；以下 `python` 使用宿主已配置的 Python 3.10+。YAML 解析需要 requirements.txt 中的 PyYAML；JSON 语法的清单也可读取。不要为了查询一条已知记录而安装新工具链。

## 定位与接入

用户提供项目名而没有路径时，先查本机登记；定位不读取记录正文：

```text
python "<skill>/scripts/map_catalog.py" locate "Archify" --limit 5
python "<skill>/scripts/map_catalog.py" register "docs/project/project.yaml" --alias "常用简称"
python "<skill>/scripts/map_catalog.py" list --limit 8 --offset 0
```

`map_catalog.py` 复用下述本机注册表，兼容已有 `project_map.py register/resolve`。查询先匹配 ID，再精确匹配名称/别名，最后匹配名称子串；同名的多个项目返回候选，不按首项选择。默认最多 8 项、上限 50，`next_offset` 表示还有候选；只检查当前页的清单和阅读入口，不读地图正文、日志或外部地图。`list` 同时检查路径可用性，可用于搬迁后的核对。状态 resolved 只表示找到清单，`missing_entrypoints` 仍需单独处理，不证明地图内容已验证。

多个位置先匹配 `--current` 指定的工作目录（默认当前目录）或 Git 工作树。明确知道常用工作副本时，用 `register ... --preferred` 登记默认位置；其他上下文仍可以选择当前工作树。没有明确默认且多个位置可用则返回 ambiguous。默认位置失效时返回 unresolved，保留可用候选供核对，不悄悄打开另一份旧副本。坏清单和身份不符只标记该位置，不中断其他项目查询；按 `manifest_path` 显式使用的权威位置优先于名称查询。

新增、接入、移动或实质更新地图后，运行 register 更新名称与位置；`--alias` 可重复使用，合并原别名，重复登记不重写文件。项目迁移沿用原 `project_id`；同名但 ID 不同的地图不合并。注册表采用带锁的原子写入，锁冲突会明确失败，不覆盖其他写入者。自动维护是使用 Skill 时的职责，没有后台全盘监听。仅登记真实项目地图；样例、测试、导出快照和候选版本可在盘点说明中列出排除原因。MRS 的 `.mrs-project.json` 不属于该目录格式。

已有清单时直接使用其路径。新项目在选定的地图目录初始化，再由 LLM 绑定已有文档并填写真实的当前目标：

```text
python "<skill>/scripts/project_map.py" discover "当前工作目录" --stop "项目根目录"
python "<skill>/scripts/project_map.py" init "docs/project" --name "项目名称" --kind software
python "<skill>/scripts/project_map.py" register "docs/project"
python "<skill>/scripts/project_map.py" resolve "项目-ID" --current "当前工作目录"
```

init 只建立最小文件，已有内容不会覆盖。登记使用本机位置索引，默认位于 `~/.codex/project-maps/registry.json`；`PROJECT_MAP_REGISTRY` 或命令的 `--registry` 指向另一份注册表。测试使用独立注册表，不混入个人地图。

多个工作树共享项目 ID，各自登记位置。显式路径最准确；存在多个合理位置时需要选定具体清单。未登记的外部引用可以保留，不能假装已经解析。

## 可选的本地语义能力

已有配置时直接查询。尚未启用且任务需要同义表达召回时，一次性准备可选依赖和模型：

```text
python -m pip install -r "<skill>/requirements-semantic.txt"
python "<skill>/scripts/setup_retrieval.py"
```

setup 从固定版本的官方模型仓库下载约 95 MB 文件并核对 SHA-256，做本地推理检查后写配置；不启动服务。默认配置是 `~/.codex/config/project-map-retrieval.json`，`PROJECT_MAP_RETRIEVAL_CONFIG` 可指定其他位置；设置 CODEX_HOME 时沿用该根目录。模型与缓存分别在本机 models/project-map、project-maps/semantic 下，不随 Skill 或项目 Git 提交。已有不同配置会保留；需要替换时先检查内容，再显式用 `--replace`。查询不会安装依赖、下载模型或向外发送地图文本。仅词法读取无需这一步。

## 查询当前记录

```text
python "<skill>/scripts/project_map.py" search "docs/project" "跨项目引用" --limit 5
python "<skill>/scripts/project_map.py" read "docs/project" "REQ-example" --max-chars 3000
python "<skill>/scripts/project_map.py" related "docs/project" "IF-example" --limit 15
python "<skill>/scripts/project_map.py" validate "docs/project"
```

search 默认排除 retired、merged、superseded、withdrawn、archived 状态；查旧名或历史时加 `--include-history`，`--current-only` 保留为显式写法。空格分隔的关键词可以跨标题、别名、摘要、正文和类型匹配；用 `--kind interface --kind implementation` 限定类型，`--module` 限定模块。精确 ID、标题和别名优先，其他候选按字段与类型排序，背景历程不因词频高占据前排。每项返回实际命中片段，不是模型生成摘要。

`--retrieval auto` 是命令行默认：已配置本地模型时混合词法与语义两路结果，用 RRF 按排名合并，同一记录只占一个候选。精确 ID 直接走词法定位，精确标题和别名保留优先级。`--retrieval lexical` 只查词面；`--retrieval hybrid` 显式要求混合，能力不可用时失败。auto 不可用时返回 `retrieval.status: degraded` 和原因，仍提供词法结果；不会悄悄下载模型或调用远程 API。Python `search_project` 为兼容既有调用默认 lexical，传入 `retrieval="auto"` 或 `"hybrid"` 启用。

词法部分的 `--match auto` 先匹配所有关键词，无结果时尝试中文相邻双字重合或部分关键词，`match_mode` 和 `match` 明示回退。混合模式会扩大中文词面候选池供融合；双字重合仍是字面匹配。`--match all/phrase/any` 选择严格的纯词法规则，与显式 hybrid 不同时使用。两路共享类型、模块和状态范围；结果的 `retrieved_by` 区分 lexical、semantic，片段来自实时原文或元数据。弱词面命中与语义同时存在时，可采用最佳语义片段并标出 `snippet.via`。

混合检索每路最多 50 条去重记录，融合后分页；`total` 是候选并集数量，不是全部相关事实数量。用 `--limit/--offset` 继续，地图改变后重新查。语义最近邻可能返回无关候选，必须读原文确认；问题太宽时补充模块或关键对象。没有命中也不宣称事实不存在。

search/read 默认输出简短视图，完整元数据用 `--detail full`；Python 接口仍返回完整数据。read 保留正文、原位置、状态、缺口、来源定位与覆盖范围。长记录按 `continuation` 中的 `offset` 和 `record_fingerprint` 续读；`--fingerprint` 仍支持整图严格检查。局部读取不代表全文已读。related 仅返回登记关系，不递归读其他项目。格式检查不验证产品实现。

```text
python "<skill>/scripts/project_map.py" search "docs/project" "接口 查询" --kind interface --limit 5
python "<skill>/scripts/project_map.py" search "docs/project" "旧接口" --include-history
python "<skill>/scripts/project_map.py" read "docs/project" "IF-example" --detail full
```

read 同时展示该记录最多 8 个来源位置；数量超出会提示，完整来源声明仍在 `--detail full` 的记录元数据中。来源路径默认相对 project.yaml；有 `workspace_id` 时相对显式工作区，不猜地图仓库与源码仓库的关系。不返回源码正文或请求远程来源。`availability` 检查文件是否存在，支持的 `symbol` 静态解析后给出 found/missing/ambiguous/unavailable 及行号。来源声明包含 `reviewed_sha256` 时核对至多 4 MiB 的文件，并检查已登记的符号、直接依赖基线；变化为 needs_review，未变为 unchanged_since_review，没有基线为 no_baseline。search/read 同时返回小型 source_health 提示，文件变化不证明说明失效。工作区和基线格式见[资产模型](asset-model.md)。

## 源码发现与说明归档

`bind-workspace` 显式绑定 Git 工作树，`source` 按需刷新并查询入口、导入、静态调用线索、定义、待补登记和待复核记录；人读页面对应“源码入口与依赖”小栏目。`review-record` 保存实际核对后的基线，`archive-record` 保存已确认失效的正文并保留原 ID 的替代入口。默认搜索和读取不会展开归档正文，`read --include-history` 显式展开，续读应保持该标志。具体命令与解析范围见[源码发现与说明归档](source-and-archive.md)。

脚本从当前源文件取正文，混合检索仅复用可重建的本机向量缓存。外部依赖、未索引内容和动态调用可能需要另行核查。

局部检索可先用 `modules <project>` 找模块 ID，再用 `search <project> 关键词 --module MOD-id`。`read` 的 `--record-fingerprint` 只检查当前记录及绑定源，允许无关模块改动后的续读；`--fingerprint` 仍检查整图。部分读取会明确提示尚未打开的约束不能视为已核实。

系统地图新增 `members`、`interfaces`、`impact` 查询；使用 `--help` 查看各命令的范围和示例，使用 `--limit/--offset` 限制结果。`interfaces` 只汇集合同摘要与接入关系，`impact` 返回已登记反向关系。系统范围、配置与维护方法见[系统地图](system-maps.md)。

## 写入与剪枝

需求、设计、接口、实现等正文直接修改其权威 Markdown 或原表格。元数据、关系和来源按[资产模型](asset-model.md)保存。绑定记录修改原始文档，不能只在生成页面修改。

对于 `records/` 内归本地图管理的独立记录，可以用机械状态操作：

```text
python "<skill>/scripts/project_map.py" retire "docs/project" "MOD-old" --reason "用户已取消该功能" --successor "MOD-new"
python "<skill>/scripts/project_map.py" merge "docs/project" "DEC-old" --reason "相同约定合并到后继" --successor "DEC-current"
```

这些命令不删除代码，也不凭空产生原记录的 Git 历史。退役依据必须来自实际任务；失败探索仍用探索结果表达。旧身份、别名、原因与后继保留。绑定的外部正文不由该状态命令代改；有必要时直接更新来源与绑定元数据。

## 查回指定会话

```text
python "<skill>/scripts/search_session.py" --source "指定任务.jsonl" --query "接口 输出" --limit 5
python "<skill>/scripts/search_session.py" --source "指定任务.jsonl" --message-id "消息-ID" --offset 0 --max-chars 2500
python "<skill>/scripts/search_session.py" --source "指定任务.jsonl" --line 120 --max-chars 2500
```

默认只查用户消息。`--role assistant` 仅覆盖明确标为可见 final/commentary 的消息；未知格式不会作为助手正文返回。关键词用空格分隔时要求全部命中。offset 按 Unicode 码点计数，不是字节；读取结果中 `next_offset` 给出后续位置。

此适配器只支持明确的 Codex 可见消息记录格式，其他来源使用宿主工具或相应适配。查询结果仍需结合必要邻近消息与后续修订判断。[检索与来源](retrieval.md)解释引用语义。

## 生成阅读页面

scripts/render_map.py 读取同一份地图与记录，输出 A/B 页面和 Archify 图形：

```text
python "<skill>/scripts/render_map.py" "docs/project/project.yaml" --mode a
```

默认写入清单同目录下的 `views/index.html` 及图形文件，并启动或复用本机 HTTP 阅读服务。向用户交付回执中的 `url`，例如 `http://localhost:端口/本次预览标识/`。不要把 HTML 文件路径作为默认阅读地址。

`--output "另一个目录/index.html"` 可指定位置，`--mode b` 以项目条目打开，默认 `--mode a` 以项目概览打开，页面内仍可切换。只需离线文件时加 `--export-only`，不会启动服务。生成参数不改变源记录的需求和状态。

服务只监听本机，按需启动，不调用 LLM；同一输出位置的服务仍在运行时复用原地址。再次生成后刷新浏览器读取新内容，服务不会自行重新生成地图。连续 8 小时无请求后退出；重启电脑或服务退出后，重新执行生成命令取得当前地址。

系统地图的“进入项目”链接会在新标签页按成员 ID 解析目标，必要时生成目标阅读页并复用其服务。系统页本身仍是导出快照；成员接口变化后按需重新导出即可。Windows 下 Git 查询、渲染器及其子进程均以隐藏命令窗口方式启动。

```text
python "<skill>/scripts/serve_map.py" status "docs/project/views/index.html"
python "<skill>/scripts/serve_map.py" stop "docs/project/views/index.html"
```

现有导出也可用 `serve_map.py start "docs/project/views/index.html"` 直接打开服务。服务回执保存在相邻 `index.preview.json`，只属于本机预览状态，不是项目身份或长期来源。HTTP 启动失败会返回失败状态并保留已经生成的 HTML；不要把文件生成成功说成服务已经可用。

Archify 渲染需要 Node.js 18 或以上，无需 npm 安装；脚本查找显式 `--node`、`PROJECT_MAP_NODE`、系统路径及已存在的 Codex 运行时。`--no-diagrams` 可只生成文档阅读页面。图形不可用时保留正文，并报告原因；不要求为普通记录查询安装 Node.js。

图直接使用清单 `archify` 中声明的原生 JSON，调用捆绑上游 CLI 的 `deliver`，没有声明时仅显示缺少图源。图源编写、校验、比较及可选原生预览见[原生 Archify 图源](archify-authoring.md)。`views/architecture.json` 与 `workflow.json` 是本次交付的原文快照，不能作为默认维护源。`.native.html` 保留上游原版，普通 `.html` 是浅色嵌入版，`.receipt.json` 分别记录源、原版和嵌入版哈希。

阅读用法和边界见[开发者阅读页面](reading-and-interaction.md)。页面是带版本与指纹的导出快照；源码更新后按需重新生成。普通开发无需先渲染。
# 开发历程的可选命令

需要查找排错、改进、验证或人工纠偏经验，或按任务查询公开消息、工具配对和反馈时，见 [开发历程](development-history.md) 中 `development_history.py cases/search/events/read` 的有限读取接口。经验可按类别、尝试结果和模块筛选，再自主展开正文与所属任务的证据。普通 `project_map.py` 查询不会因此读取事件载荷；导入指定来源仅在需要保留该任务时执行。
