# 源码发现与说明归档

归档目录内的 `.gitattributes` 禁止 Git 转换原文字节，保证跨系统克隆后仍可校验原文指纹；把它和归档文件一起提交。源码的字节指纹会反映换行变化，项目若需跨系统复用核对基线，应统一源码的 Git 换行约定。

用于防止只读登记记录而遗漏源码中的入口和依赖。用户用自然语言指定项目，LLM 定位地图、维护工作区绑定和核对说明；无需用户编辑配置或操作另一套界面。

## 显式绑定

```text
python "<skill>/scripts/project_map.py" bind-workspace "<地图>" source "<Git 工作树根目录>" --python-root src
```

多个仓库或工作树分别使用不同 workspace_id。路径尽量保存为相对地图的位置；地图可与源码仓库并列，绑定仍是权威定位。不会把地图自身 Git 根目录猜成源码仓库，也不会自动移动或删除旧地图。`--python-root` 可重复，未指定时尝试 `.` 与 `src`；普通平铺脚本项目用 `--python-root .`。`--exclude "pattern"` 可重复，匹配仓库相对路径；重新指定该选项会替换原排除列表，原有其他工作区字段保留。

Python 使用标准库 AST。JavaScript、TypeScript、JSX/TSX 和 HTML 脚本使用 Tree-sitter；可选依赖在 requirements-source.txt。可以安装进当前 Python，或独立安装到本机 `<CODEX_HOME>/lib/project-map-source`：

```text
python -m pip install --target "<CODEX_HOME>/lib/project-map-source" -r "<skill>/requirements-source.txt"
```

CODEX_HOME 未设置时使用 `~/.codex`。查询不会自行下载安装；解析器缺失会在覆盖报告中说明，并在恢复依赖后重试。Python 3.10 读取 pyproject.toml 的入口需要 tomli；缺失同样明示。

## LLM 的阅读入口

```text
python "<skill>/scripts/project_map.py" source "<地图>"
python "<skill>/scripts/project_map.py" source "<地图>" --kind entrypoint --workspace source
python "<skill>/scripts/project_map.py" source "<地图>" --kind dependency --query "path/to/file"
python "<skill>/scripts/project_map.py" source "<地图>" --kind call --query "function_name"
python "<skill>/scripts/project_map.py" source "<地图>" --kind gap --limit 12
python "<skill>/scripts/project_map.py" source "<地图>" --kind review
python "<skill>/scripts/project_map.py" source "<地图>" --kind coverage
```

每次显式调用 source 刷新绑定工作树：Git 列出的已跟踪文件及未忽略的新文件，按内容指纹复用未改文件的解析结果。缓存按地图绝对位置、项目 ID 和工作区 ID 隔离，存于本机 project-maps/source，可重建；`PROJECT_MAP_SOURCE_CACHE` 可改变缓存目录。最多 3000 个候选文件，单文件 2 MiB；超量时明确要求收窄。排除 Git 内部目录、子仓库、外部符号链接、依赖包、构建产物、当前地图资料与阅读导出。`coverage` 返回排除原因、不支持的文件和解析失败位置。

入口包括 Python 主模块、main guard、pyproject 脚本、package.json 的 main/module/bin/exports/scripts。导入、函数/类定义、静态调用线索带工作区、文件、行号；可解析的相对导入附目标路径和符号。`symbol` 用于定位定义。调用结果只是语法上的引用候选；动态派发、变量遮蔽、反射、运行时注册、包路径别名、框架路由和其他语言不能保证解析。外部包与未解析项明确标记，不编造连线。

`gap` 是待核对登记候选：有定义/入口但没有 sources 关联的文件，以及代码导入两端已有记录、地图却没有登记的关系。它不自动生成架构说明，也不判断地图有错。明确相关性后由 LLM 更新记录和 relations。`--query` 以空格分隔的全部词过滤，`--limit/--offset` 分页，`next_offset` 继续；它不替代现有语义文档搜索。

人读页面只增加 `records/source-analysis/overview.md` 小栏目，概述入口、局部依赖、待复核说明及覆盖范围；大量静态数据保留在按需查询入口。报告属于生成资料，不在其中手写维护结论。指定一个工作区时其他工作区保留上次扫描结果；完整刷新不传 `--workspace`。HTML 是导出快照，刷新报告后需要重新导出才反映变化。

## 变化、核对、归档是不同步骤

1. 记录的 `sources` 把说明与真实文件绑定。扫描会保存首次观察到的关联文件和已解析的直接依赖指纹；未审阅的首次观察不证明说明有效。再次扫描或者 search/read 发现关联文件变化时给出 `source_health.state: needs_review`，包括工作区、路径及依赖变化。重复扫描不会抹掉待复核状态。
2. LLM 对照当前源码检查说明是否仍适用。仍适用则更新必要说明后执行 `review-record`，留下核对理由、时间、正文摘要、源码/符号及直接依赖基线。命令只记录核对结果，不代替语义核查。文件级检查保守地将同文件其他位置变化也标为待复核；symbol_review 可说明指定定义本身是否变化。未声明 sources 或扫描能力外的依赖不在此保证范围内。
3. 已确认说明不再适用时使用 `archive-record`，填写失效理由和核对证据，可指向已有替代记录。源码变化本身不是失效证据。

```text
python "<skill>/scripts/project_map.py" review-record "<地图>" IF-example --reason "核对实现仍符合接口中列出的输入、返回与失败约定"
python "<skill>/scripts/project_map.py" archive-record "<地图>" IMP-old --reason "旧实现说明已被新版本替代" --evidence "已对照当前实现及 IMP-new" --successor IMP-new
python "<skill>/scripts/project_map.py" read "<地图>" IMP-old
python "<skill>/scripts/project_map.py" read "<地图>" IMP-old --include-history
```

归档将地图自有文档的原始字节移存至 `archive/records/`，原路径保留短定位条目。原 ID、别名、功能/需求 status、关系及未知元数据保留；`documentation.state` 单独标记说明归档，含原因、证据、时间、原位置、地图版本、快照校验值和后继。没有新版时明确显示当前说明缺口。外部章节/表格绑定会归档该记录的正文与来源摘录，外部原文件不修改；原文件以后缺失也可读该归档。

默认 search 的两路候选均排除归档说明；read 旧 ID 只给定位、替代记录或缺口。显式 `--include-history` 才搜索/读取归档原文，续读保留该标志。校验不符的历史快照拒绝冒充原始内容，但当前定位仍可读。人工页面的默认目录及搜索也不展示旧正文；“包含历史”显示短条目，点击“查看归档原文”打开独立历史页。主页面与 docs.json 不内嵌归档正文；共享外部原资料含归档章节时暂停整份原文快照，改从具体记录入口阅读。

地图与 archive/ 一起纳入已有 Git 管理。归档不会提交 Git，不删除源码、不取消有效需求；retire/merge 仍是独立的生命周期操作。
