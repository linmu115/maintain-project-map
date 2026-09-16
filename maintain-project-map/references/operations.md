# 本地操作

仅在需要脚本时读取。`<skill>` 表示当前 SKILL.md 所在目录；以下 `python` 使用宿主已配置的 Python 3.10+。YAML 解析需要 requirements.txt 中的 PyYAML；JSON 语法的清单也可读取。不要为了查询一条已知记录而安装新工具链。

## 定位与接入

已有清单时直接使用其路径。新项目在选定的地图目录初始化，再由 LLM 绑定已有文档并填写真实的当前目标：

```text
python "<skill>/scripts/project_map.py" discover "当前工作目录" --stop "项目根目录"
python "<skill>/scripts/project_map.py" init "docs/project" --name "项目名称" --kind software
python "<skill>/scripts/project_map.py" register "docs/project"
python "<skill>/scripts/project_map.py" resolve "项目-ID" --current "当前工作目录"
```

init 只建立最小文件，已有内容不会覆盖。登记使用本机位置索引，默认位于 `~/.codex/project-maps/registry.json`；`PROJECT_MAP_REGISTRY` 或命令的 `--registry` 指向另一份注册表。测试使用独立注册表，不混入个人地图。

多个工作树共享项目 ID，各自登记位置。显式路径最准确；存在多个合理位置时需要选定具体清单。未登记的外部引用可以保留，不能假装已经解析。

## 查询当前记录

```text
python "<skill>/scripts/project_map.py" search "docs/project" "跨项目引用" --limit 5
python "<skill>/scripts/project_map.py" read "docs/project" "REQ-example" --max-chars 3000
python "<skill>/scripts/project_map.py" related "docs/project" "IF-example" --limit 15
python "<skill>/scripts/project_map.py" validate "docs/project"
```

search 是中文子串、词面和别名检索，默认可以找历史记录；明确只看当前时用 `--current-only`。read 返回正文、原文件位置与覆盖范围，长记录通过 `--offset` 继续；继续读取时传回先前结果的 `--fingerprint`，若源内容已变则重新定位，避免拼接不同版本。不能把局部读取当成全文。related 仅给出当前地图登记的关系，不递归读其他项目。验证格式和本地链接不等于验证产品实现。

脚本从当前源文件读取，不依赖持久语义数据库。外部依赖、未索引内容和动态调用可能需要另行核查。

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

```text
python "<skill>/scripts/serve_map.py" status "docs/project/views/index.html"
python "<skill>/scripts/serve_map.py" stop "docs/project/views/index.html"
```

现有导出也可用 `serve_map.py start "docs/project/views/index.html"` 直接打开服务。服务回执保存在相邻 `index.preview.json`，只属于本机预览状态，不是项目身份或长期来源。HTTP 启动失败会返回失败状态并保留已经生成的 HTML；不要把文件生成成功说成服务已经可用。

Archify 渲染需要 Node.js 18 或以上，无需 npm 安装；脚本查找显式 `--node`、`PROJECT_MAP_NODE`、系统路径及已存在的 Codex 运行时。`--no-diagrams` 可只生成文档阅读页面。图形不可用时保留正文，并报告原因；不要求为普通记录查询安装 Node.js。

图直接使用清单 `archify` 中声明的原生 JSON，调用捆绑上游 CLI 的 `deliver`，没有声明时仅显示缺少图源。图源编写、校验、比较及可选原生预览见[原生 Archify 图源](archify-authoring.md)。`views/architecture.json` 与 `workflow.json` 是本次交付的原文快照，不能作为默认维护源。`.native.html` 保留上游原版，普通 `.html` 是浅色嵌入版，`.receipt.json` 分别记录源、原版和嵌入版哈希。

阅读用法和边界见[开发者阅读页面](reading-and-interaction.md)。页面是带版本与指纹的导出快照；源码更新后按需重新生成。普通开发无需先渲染。
