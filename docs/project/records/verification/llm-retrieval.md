---
{
  "id": "VER-llm-retrieval",
  "kind": "verification",
  "title": "LLM 检索、源码发现与说明归档检查",
  "status": "current",
  "summary": "源码发现、待复核和物理归档已通过完整 144 项回归；人读摘要去重另复验 12 项，浏览器已检查旧 ID 与归档原文跳转。",
  "relations": [
    {
      "relation": "verifies",
      "to": {
        "record_id": "IMP-llm-retrieval"
      }
    },
    {
      "relation": "verifies",
      "to": {
        "record_id": "IMP-llm-context"
      }
    }
  ],
  "sources": [
    {
      "workspace_id": "source",
      "path": "maintain-project-map/tests/test_project_map.py",
      "role": "verification"
    },
    {
      "workspace_id": "source",
      "path": "maintain-project-map/tests/test_semantic_retrieval.py",
      "role": "verification"
    },
    {
      "workspace_id": "source",
      "path": "maintain-project-map/tests/test_source_archive.py",
      "role": "verification"
    },
    {
      "workspace_id": "source",
      "path": "tests/test_http_preview.py",
      "role": "verification"
    },
    {
      "workspace_id": "source",
      "path": "tests/test_reader_navigation.py",
      "role": "verification"
    }
  ]
}
---

## 回归与原有边界

2026-09-19 在源码工作区 codex/llm-map-retrieval 的未提交改动上运行 `python -X utf8 -m pytest tests maintain-project-map/tests -q`：129 passed，耗时 97.92 秒。该次将语义配置指向临时的不存在路径，单元检查使用确定性向量替身，普通回归不依赖下载或本机模型。Skill 格式与自身地图结构检查通过。

此前词法与来源改进的完整回归为 117 项通过。既有覆盖包括跨字段多关键词、类型过滤、当前状态与历史可达性、精确别名、原文片段位置、分页、明示中文回退、无关词法查询无命中；来源覆盖显式工作区、缺失绑定、越界路径、核对基线变化及不自动退役；简短读取保留缺口、失败结果、适用范围、读取边界和续读信息。

## 新增混合检索行为

新增 12 项检查覆盖：无字面重合的语义候选、两路相同状态/类型/模块范围、实时修改/删除/归档、增量向量复用、过滤时不清掉其他范围、地图位置与模型空间隔离、坏向量重算、无效模型结果失败、整个缓存损坏时明示降级、严格词面与精确 ID 快路、RRF 计算和记录去重、固定候选窗口分页、长段落位置及代码围栏、嵌入清理链接目标而保持原文证据。一个测试可包含多个相关断言，不把断言数当作独立实验。

## 真实模型检查

另外运行本机 BAAI/bge-small-zh-v1.5（Qdrant ONNX 固定版本 46fbe35fd4374a00fee7de77dfddaeb6dd6a2c59，512 维）。使用 12 条明确的测试记录：启动、认证、归档、备份、主题、分页、日志、构建、监听、缓存、权限和退出；查询期间禁用 Python socket 创建，向量缓存放在临时目录。不是对真实产品能力的验证。

| 问法 | 词法候选 | 混合中的目标名次 |
| --- | --- | --- |
| 开机后第一步做什么 | 无 | 启动入口第 2 |
| 这个程序是从哪里跑起来的 | 无 | 启动入口第 1 |
| 以前那份过期材料去哪里翻 | 无 | 历史版本归档第 1 |
| 登录服务用的密码存在哪个地方 | 认证配置 | 认证配置第 1 |

同一查询重做后，12 个片段全部复用、新增嵌入为 0，查询向量也复用。首次四记录试查曾要求“开机后第一步做什么”排第一，实际排第二导致断言失败；此处保留实际名次，不声称宽泛问句一定找准第一项。

另对既有自身地图试查“怎么查询项目记录”，查询接口排第一；“文件改了以后原来的说明还可信吗”仍可能把相近但并非目标的文档排在前面。需要结合类型、模块或具体对象收窄并读原文。以上不是使用者标注的召回率评估，也未做同预算 BM25、不同嵌入模型或重排器对照；没有普遍准确率或 token 收益结论。该次检索层升级尚未包含自动依赖发现与物理归档，后续实施和核查见下节；地图批量迁移及完整运行时影响分析不在本轮范围。


安装版端到端检查：沿用首选地图位置，以默认 auto、interface/implementation 范围搜索“怎么查询项目记录”，实际返回 hybrid/ready，首项 IF-map-query。继续 read 解析到真实源码仓库的 search_project、rank_records、semantic_search，三个已核对文件均为 unchanged_since_review；重复查询复用 124 个片段、新增嵌入为 0。安装版 Skill 校验及两份自身地图的 75 条记录验证通过，目录登记与首选位置未改变。

## 继续实施：源码发现与说明归档

2026-09-19 在同一源码工作区的未提交改动上完整运行 `python -X utf8 -m pytest tests maintain-project-map/tests -q`：144 passed，138.45 秒。第一次整轮曾有一个旧阅读器检查依赖“搜索自动包含历史”的行为，改为显式历史开关并载入实际的过滤辅助函数；正常的失败模块仍保留在当前范围。后续仅调整人读摘要的重复依赖显示，对源码/归档相关 12 项检查复验通过。

新增检查包括：真实独立 Git 工作树绑定、Git 忽略与新文件、解析增量复用、Python 相对导入和别名、TS/HTML 导入、包入口、非字面动态导入披露、缺失解析器恢复、多个工作树和地图缓存隔离；源文件/直接依赖变化、重复扫描保持待复核、核对后更新基线，以及未登记关系按文件对合并。

归档检查验证原始文件字节保留、状态与 ID 独立、后继与缺口、外部绑定不改原文且原文缺失后仍可读快照、坏快照拒绝冒充原文、默认词法和语义候选排除归档正文、历史读取续读标志、主 HTML/docs.json 不混入旧正文、旧链接仍定位。HTTP 检查确认独立归档页只有明确请求且在导出清单中才提供，未列出的归档页不可访问。

真实自身地图现有 27 个支持的源码文件、7 个入口、284 项导入。首次扫描保留观察基线，修订并实际核对本轮受影响的 12 份说明后保存 reviewed 基线；重复扫描复用全部 27 个文件。当前有 16 项合并后的待核对登记候选，不作为架构错误或全部依赖完整性的结论。原始 53 条候选因同文件多次导入存在重复，按文件对合并到 16 项，完整依赖证据保持可查询。

自身旧实现 IMP-llm-retrieval 已用 archive-record 原字节归档到两份地图各自的 archive/records/，status 仍为 current，documentation.state 为 archived；替代说明为 IMP-llm-context。浏览器实测旧 ID 进入短定位、明确点击“查看归档原文”打开带历史提示的独立页面。新源码小栏目沿用原有侧栏。静态调用只作语法线索，动态派发、反射和未支持语言没有全覆盖结论。

安装版端到端复核：两份地图均为 77 条记录且结构有效；旧实现默认读取只给后继、显式历史读取保留原正文，当前查询不命中独有的旧说明句子。安装版混合检索 ready，问“文件改了以后哪些说明需要核对”时 IMP-llm-context 排第一；source 入口能定位实际 project_map.py 的主模块入口。112 个运行/资源/参考文件与源码一致，首选地图位置保持原有明确选择。
