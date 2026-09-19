---
{
  "id": "IMP-llm-context",
  "kind": "implementation",
  "title": "LLM 检索、源码发现与说明归档",
  "status": "current",
  "progress": "implemented",
  "summary": "混合检索结合显式工作区静态发现；来源变化提示复核，确认失效的说明物理归档，旧 ID 保留替代入口。",
  "gap": "静态解析不覆盖全部动态调用、反射、框架入口或所有语言；无普遍召回率保证。",
  "relations": [
    {
      "relation": "implements",
      "to": {
        "record_id": "REQ-llm-retrieval"
      }
    },
    {
      "relation": "supersedes",
      "to": {
        "record_id": "IMP-llm-retrieval"
      }
    }
  ],
  "sources": [
    {
      "workspace_id": "source",
      "path": "maintain-project-map/scripts/record_search.py",
      "role": "implementation",
      "reviewed_sha256": "3b8ed4498616ad797569311d344f0a33436c1f0a54cd37e446d448c885cd258b",
      "reviewed_dependencies": []
    },
    {
      "workspace_id": "source",
      "path": "maintain-project-map/scripts/semantic_retrieval.py",
      "role": "implementation",
      "reviewed_sha256": "14195cee22caab390ca24ad0ec5d7acdeb700d0497d2fa137eb80f6fba94c331",
      "reviewed_dependencies": [
        {
          "path": "maintain-project-map/scripts/record_search.py",
          "sha256": "3b8ed4498616ad797569311d344f0a33436c1f0a54cd37e446d448c885cd258b"
        },
        {
          "path": "maintain-project-map/scripts/system_map.py",
          "sha256": "c591323f312d35a7428a1e92983f24d2aac23dba3f980cf6bf7838a4856be979"
        }
      ]
    },
    {
      "workspace_id": "source",
      "path": "maintain-project-map/scripts/source_locations.py",
      "role": "implementation",
      "reviewed_sha256": "f748ce97270ff5619278a4caf28d07778918ed4fcb601d28ed91f10388e870d0",
      "reviewed_dependencies": [
        {
          "path": "maintain-project-map/scripts/code_parsers.py",
          "sha256": "619eb09eba72a70b3428a8754bb4e118a1d4d0a5bd5d4519dc50c657d2d7651a"
        }
      ]
    },
    {
      "workspace_id": "source",
      "path": "maintain-project-map/scripts/source_inventory.py",
      "role": "implementation",
      "reviewed_sha256": "9a955c3abda4b41beb79fc713b25c7e3093c2b1fa4844fc9980e7e2d18c22e90",
      "reviewed_dependencies": [
        {
          "path": "maintain-project-map/scripts/code_parsers.py",
          "sha256": "619eb09eba72a70b3428a8754bb4e118a1d4d0a5bd5d4519dc50c657d2d7651a"
        },
        {
          "path": "maintain-project-map/scripts/document_archive.py",
          "sha256": "da4f6deaadde3da10c228a46f6ce02d3f5e2e2d3a970664420b05685f622f9e4"
        },
        {
          "path": "maintain-project-map/scripts/project_map.py",
          "sha256": "67aee0a424ef3fe0019e0db34fbc97d9168e2edc6e35ee107faef86a63b49f6a"
        },
        {
          "path": "maintain-project-map/scripts/source_locations.py",
          "sha256": "f748ce97270ff5619278a4caf28d07778918ed4fcb601d28ed91f10388e870d0"
        },
        {
          "path": "maintain-project-map/scripts/system_map.py",
          "sha256": "c591323f312d35a7428a1e92983f24d2aac23dba3f980cf6bf7838a4856be979"
        },
        {
          "path": "maintain-project-map/scripts/workspace_scanner.py",
          "sha256": "0fe5a0759b81b1a63e1de71b53ebbed16605d5210662b6b5688468cbe5694075"
        }
      ]
    },
    {
      "workspace_id": "source",
      "path": "maintain-project-map/scripts/workspace_scanner.py",
      "role": "implementation",
      "reviewed_sha256": "0fe5a0759b81b1a63e1de71b53ebbed16605d5210662b6b5688468cbe5694075",
      "reviewed_dependencies": [
        {
          "path": "maintain-project-map/scripts/code_parsers.py",
          "sha256": "619eb09eba72a70b3428a8754bb4e118a1d4d0a5bd5d4519dc50c657d2d7651a"
        }
      ]
    },
    {
      "workspace_id": "source",
      "path": "maintain-project-map/scripts/code_parsers.py",
      "role": "implementation",
      "reviewed_sha256": "619eb09eba72a70b3428a8754bb4e118a1d4d0a5bd5d4519dc50c657d2d7651a",
      "reviewed_dependencies": []
    },
    {
      "workspace_id": "source",
      "path": "maintain-project-map/scripts/document_archive.py",
      "role": "implementation",
      "reviewed_sha256": "da4f6deaadde3da10c228a46f6ce02d3f5e2e2d3a970664420b05685f622f9e4",
      "reviewed_dependencies": [
        {
          "path": "maintain-project-map/scripts/project_map.py",
          "sha256": "67aee0a424ef3fe0019e0db34fbc97d9168e2edc6e35ee107faef86a63b49f6a"
        },
        {
          "path": "maintain-project-map/scripts/system_map.py",
          "sha256": "c591323f312d35a7428a1e92983f24d2aac23dba3f980cf6bf7838a4856be979"
        }
      ]
    }
  ],
  "source_review": {
    "reviewed_at": "2026-09-19T08:50:22.388166+00:00",
    "reason": "复核原字节归档规则允许 CRLF 保留；真实 Git 往返验证通过，公共导出和本机读取行为不变。",
    "body_sha256": "b693fbf8d63e4f1d9e1026825acef796e4c2e7d512fbfbaff98ef62f3c5780ab"
  }
}
---

## 词面与语义候选

搜索按当前状态、类型和模块筛选后进行检索；精确 ID/标题/别名优先，候选按字段及记录类型排序。完整记录只在 read 时展开；候选附原文片段，分页通过 next_offset 继续。

词法自动匹配先匹配空格分隔的全部词，没有候选时使用明示的字面回退。中文使用相邻双字重合，不是分词模型或同义词召回；弱匹配仍需模型核实。接口 ID、方法名和路径不会被字符回退拆成中文词。

命令行默认自动使用已配置的本地 BGE small 中文模型。段落带项目、模块、标题上下文，模型使用 CLS 池化、归一化和查询前缀。语义先保留每条记录的最佳原文片段，再与较宽的词面候选池按等权 RRF 合并；每路最多 50 条记录，精确 ID、标题和别名优先。同一记录只有一个结果，得分不表示事实置信度。没有配置或不可用时 auto 明示回退，显式 hybrid 会失败；严格词面规则不混入语义候选。Python API 默认 lexical 以兼容已有调用。

## 缓存与实时来源

配置、固定版本模型和 SQLite 向量缓存在本机，查询阶段没有网络请求。缓存只保存内容摘要键、向量和完整性校验，不保存另一份正文。按地图绝对位置、项目 ID、模型和分词器校验值及查询前缀隔离；地图修改后只补算变化片段，删除记录退出，归档记录按当前范围排除。每次片段都取实时源文档。缓存不决定文档有效性。

## 简短结果与读取

默认输出移去候选的重复摘要、空字段及不用于下一步的内部数据；read 保留状态、缺口、适用范围、结果、来源与读取范围。分段返回记录指纹供续读；--detail full 保留完整元数据及原回执，Python API 保留完整格式。历史状态默认隐藏，--include-history 仍可查回。

## 绑定工作区的静态发现

使用 source 查询显式绑定的 Git 工作树，包含已跟踪与未忽略的新文件，排除依赖包、构建产物和地图导出。Python AST、JavaScript/TypeScript Tree-sitter 与 HTML 脚本解析提供定义、导入、静态调用线索；包清单提供声明入口。不执行被检查项目，动态或未支持部分通过 coverage 明示。

source 按 summary、entrypoint、dependency、call、symbol、gap、review、coverage 分页查询。工作区、路径、行号、目标与对应记录在同一结果中；登记缺口是待核对候选，不能直接当成架构错误。人读页面仅增加“源码入口与依赖”文档小栏目，完整数据按需读取。未修改文件复用解析缓存，绑定位置和地图位置隔离。

## 源码变化待复核

sources 中的 workspace_id、path、可选 symbol 将说明关联到源码。首次扫描保存观察基线；后续发现文件或已解析直接依赖变化时，search/read 和人读正文前提示 needs_review 与变化位置。反复扫描不覆盖旧基线，缺少基线不表示说明有效。

LLM 对照源码实际核对后，review-record 记录理由、时间及文件/符号/直接依赖指纹。文件级检查保守地提示同文件其他位置的变化，symbol_review 辅助定位；不声称具有完整符号影响分析。读取最多展示 8 项来源，完整声明按需查看；不会把源码正文一起塞进 LLM 结果。

## 确认失效后的物理归档

archive-record 要求失效理由与实际核对证据。自有文档原始字节保存于 archive/records/，原路径变为短条目；原 ID、别名、功能或需求 status 不变。documentation 单独记录归档状态、原位置、版本、校验值及后继；无新版时明确给出当前说明缺口。

外部文档绑定只归档本条正文和来源摘录，不改外部文件；原文件以后缺失也能读归档。默认词法/语义候选排除归档说明，read 旧 ID 返回替代入口，显式 --include-history 才读旧正文。人工页面遵守相同边界，旧正文放在独立归档页；共享原始资料包含已归档章节时，不再从整份原文视图泄露旧正文。

本条替代 [[IMP-llm-retrieval]] 中“自动扫描、符号解析、物理归档尚未实现”的旧描述，检索能力继续保留。核查证据见 [[VER-llm-retrieval]]，操作约定由 Skill 的 references/source-and-archive.md 维护。
