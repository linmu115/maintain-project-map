---
{
  "id": "IF-map-query",
  "kind": "interface",
  "title": "查询与分段读取",
  "status": "current",
  "summary": "模型按当前问题取得有限记录、原位置和版本范围，不必读取整张页面。",
  "sources": [
    {
      "workspace_id": "source",
      "path": "maintain-project-map/references/operations.md",
      "role": "usage",
      "reviewed_sha256": "d7c4d10f51271240631bfa6155d8841e9d6524a80cfdf04df54ef409b955f3a6",
      "reviewed_dependencies": []
    },
    {
      "workspace_id": "source",
      "path": "maintain-project-map/scripts/project_map.py",
      "role": "implementation",
      "symbol": "search_project",
      "reviewed_sha256": "67aee0a424ef3fe0019e0db34fbc97d9168e2edc6e35ee107faef86a63b49f6a",
      "reviewed_symbol_sha256": "85b8f638f4010d666bfac9a018b6f559874a132f2d8cc43bc3a3f988d99fbff0",
      "reviewed_dependencies": [
        {
          "path": "maintain-project-map/scripts/document_archive.py",
          "sha256": "da4f6deaadde3da10c228a46f6ce02d3f5e2e2d3a970664420b05685f622f9e4"
        },
        {
          "path": "maintain-project-map/scripts/record_search.py",
          "sha256": "3b8ed4498616ad797569311d344f0a33436c1f0a54cd37e446d448c885cd258b"
        },
        {
          "path": "maintain-project-map/scripts/semantic_retrieval.py",
          "sha256": "14195cee22caab390ca24ad0ec5d7acdeb700d0497d2fa137eb80f6fba94c331"
        },
        {
          "path": "maintain-project-map/scripts/source_inventory.py",
          "sha256": "9a955c3abda4b41beb79fc713b25c7e3093c2b1fa4844fc9980e7e2d18c22e90"
        },
        {
          "path": "maintain-project-map/scripts/source_locations.py",
          "sha256": "f748ce97270ff5619278a4caf28d07778918ed4fcb601d28ed91f10388e870d0"
        },
        {
          "path": "maintain-project-map/scripts/system_map.py",
          "sha256": "c591323f312d35a7428a1e92983f24d2aac23dba3f980cf6bf7838a4856be979"
        }
      ]
    },
    {
      "workspace_id": "source",
      "path": "maintain-project-map/scripts/record_search.py",
      "role": "implementation",
      "symbol": "rank_records",
      "reviewed_sha256": "3b8ed4498616ad797569311d344f0a33436c1f0a54cd37e446d448c885cd258b",
      "reviewed_symbol_sha256": "2bb3dc4b02c9ef9543c85c27c2cf897bcb57ddaee7c46b47b9fd8538fc0394de",
      "reviewed_dependencies": []
    },
    {
      "workspace_id": "source",
      "path": "maintain-project-map/scripts/semantic_retrieval.py",
      "role": "implementation",
      "symbol": "semantic_search",
      "reviewed_sha256": "14195cee22caab390ca24ad0ec5d7acdeb700d0497d2fa137eb80f6fba94c331",
      "reviewed_symbol_sha256": "e5b9e270275460a92d3c2722660a50f4061e19d0d1b4af9d32e0675ef073108d",
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
    }
  ],
  "relations": [
    {
      "relation": "consumes",
      "to": {
        "record_id": "IF-project-location"
      }
    },
    {
      "relation": "consumes",
      "to": {
        "record_id": "IF-record-data"
      }
    }
  ],
  "source_review": {
    "reviewed_at": "2026-09-19T08:50:46.534604+00:00",
    "reason": "复核原字节归档规则允许 CRLF 保留；真实 Git 往返验证通过，公共导出和本机读取行为不变。",
    "body_sha256": "7ef61fd1eca990c317274cc108a39ffb475672c62116281b57ca6640a771e62a"
  }
}
---

# 查询与分段读取


输入当前地图和关键词、记录 ID 或关系起点，可获得候选记录、限定正文或明确登记的关联。比如只问“为什么旧同步模块退役”，先查名称/别名，再读决定和后继，不用展开全部 UI。

长记录按 offset 续读，并带回内容指纹；来源变化时重新定位，避免拼接不同版本。关系查询返回本地图已声明的边，不自动遍历外部项目。候选同时标明词面或语义途径；语义相近不表示事实已核实，未命中也不证明事实不存在。

加载共同源数据供阅读导出也属于记录引擎职责。命令示例只在 [本地操作](../../../../../../maintain-project-map/references/operations.md) 维护，返回信息由 [project_map.py](../../../../../../maintain-project-map/scripts/project_map.py) 定义。普通查询不会加载 HTML、源码阅读快照或 Archify 运行时。

## 局部披露扩展

modules 返回稳定模块 ID；search --module 按显式 module_id 或最近模块概览限定范围。read --record-fingerprint 只核对当前记录及绑定源，允许无关模块修改后的续读；原有整图 --fingerprint 仍可用于严格一致性。候选和部分正文都附覆盖说明，不能把尚未打开的约束视为完整已读。

members、interfaces、impact 在明确系统范围内汇集成员摘要与登记关系，分页返回，不自动展开正文或递归成员；系统约定见 [[IF-system-composition]]。

## 当前检索和来源读取

搜索默认查当前状态，多个关键词可以跨字段命中，可按记录类型、模块筛选。精确名称优先，背景历程降低排序权重；返回原文命中片段。命令行默认自动使用已配置的本地中文模型，将词面与语义候选用 RRF 合并，同一记录只占一项。无本地能力时明确回退，显式 --retrieval hybrid 则失败。旧状态用 --include-history，原短语用 --match phrase。

search/read 默认是简短视图，完整元数据用 --detail full。读取来源时按照 project.yaml 中显式工作区解析文件，保留角色、可用性及未核对范围；声明了实际核对基线的文件发生变化时提示 needs_review。source 可在显式工作区提取入口、导入、定义与静态调用线索，并返回未登记关系及待复核说明。核实仍适用后保存 review-record 基线；确认失效才 archive-record，默认读取旧 ID 给出后继或说明缺口，显式历史读取才展开归档正文。改进需求见 [[REQ-llm-retrieval]]，当前实现见 [[IMP-llm-context]]。
