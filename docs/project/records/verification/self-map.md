---
{
  "id": "VER-self-map",
  "kind": "verification",
  "title": "自身地图的整理与核对",
  "status": "current",
  "summary": "52 个原记录身份保持不变，来源、正文链接和两份原生图核对通过；浏览器检查模块目录、护照跳转、图定位与返回。",
  "sources": [
    {
      "path": "maintain-project-map/SKILL.md",
      "role": "skill-source-authority",
      "workspace_id": "source",
      "reviewed_sha256": "89778cf774a9a4af4c7e3b0585a6aa3997c2e873f4ba856dad970d8ebe8636c5",
      "reviewed_dependencies": []
    },
    {
      "path": "maintain-project-map/scripts/project_map.py",
      "role": "skill-source-authority",
      "workspace_id": "source",
      "reviewed_sha256": "67aee0a424ef3fe0019e0db34fbc97d9168e2edc6e35ee107faef86a63b49f6a",
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
      "path": "maintain-project-map/scripts/render_map.py",
      "role": "skill-source-authority",
      "workspace_id": "source",
      "reviewed_sha256": "9c67374bd56a05b84f3e041f0708b494cf70e22fecf3c29993f67a5038a0ec55",
      "reviewed_dependencies": [
        {
          "path": "maintain-project-map/scripts/archify_adapter.py",
          "sha256": "1cb5a7341603996feccfc850ddf29daa4c3bfed62f398af47e53a1f6a66a6964"
        },
        {
          "path": "maintain-project-map/scripts/development_history.py",
          "sha256": "556b088e8d4562f9440a5130f8b1731e70d4ccc5e75c1926be72b8ad7026f8ca"
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
          "path": "maintain-project-map/scripts/public_export.py",
          "sha256": "a688ba62ab937a48a5dd16b6964e79ba298260fcd9be87af977128ee460fb5ef"
        },
        {
          "path": "maintain-project-map/scripts/reader_content.py",
          "sha256": "8ad021637190777cb58a5b02b1ed8945031c2d7575576bb977cd32242dafc80e"
        },
        {
          "path": "maintain-project-map/scripts/reader_markdown.py",
          "sha256": "9c040c241e23ad0e084b5803f12901abfee65273dce0b881ae74a9352290cd39"
        },
        {
          "path": "maintain-project-map/scripts/serve_map.py",
          "sha256": "91382ef2456f566e09f80c4a92d5d1bed3e79416f43afb78cc82dc8a2a8ed96b"
        },
        {
          "path": "maintain-project-map/scripts/source_inventory.py",
          "sha256": "9a955c3abda4b41beb79fc713b25c7e3093c2b1fa4844fc9980e7e2d18c22e90"
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
      "relation": "verifies",
      "to": {
        "record_id": "IMP-release"
      }
    },
    {
      "relation": "verifies",
      "to": {
        "record_id": "MOD-reader"
      }
    }
  ],
  "source_review": {
    "reviewed_at": "2026-09-19T08:50:52.614137+00:00",
    "reason": "复核原字节归档规则允许 CRLF 保留；真实 Git 往返验证通过，公共导出和本机读取行为不变。",
    "body_sha256": "cc5461ccc3b18929b50e468c6170d9adc18d01205affbbbb59ba87d034bb3f3e"
  }
}
---

# 自身地图的整理与核对

## 当前地图核对

日期：2026-09-16。以本地图独立仓库的 `125cf4120da8dda8a2d5183dd914628c58a9a0fb` 为整理基线，项目 ID 保持为 `2c64630e-7c8f-465f-97b9-ef6e5916c8aa`。52 个原记录 ID 全部保留，仍为 46 份独立记录和 6 个既有设计章节绑定；没有新增或删除记录，更新记录数量为 0。

本次按源码核对了维护指引、身份定位、记录与绑定查询、指定会话检索、阅读生成、文档导航、原生图适配、更新阅读及 HTTP 预览。源码基线为 `45c38d8`，成员边界指引的未提交修订及三份副本一致性另见 [[VER-composite-guidance|指引文档核对]]。当前要求、实现说明和验证记录分别保留，既有技术约定继续链接到原负责文件。

- 地图结构检查通过，无错误或警告；73 条规范化关系均有有效本地记录身份。31 个不同的已声明本地来源存在，正文中的 Markdown/Wiki 目标与章节已按读取器的解析规则核对。
- 架构图保留 14 个节点，流程图保留 8 个节点及原图全文；两份图的原节点 ID 与所有现有绑定保留。架构图只修订输入和边界说明，补充 3 个节点到条目的关联，布局与关系不变。
- 两份图各 9 项原生交付检查通过，原始图源与交付快照一致，原版和适配版分别保留回执。架构图有 1 项全图适配时的小字号提示，缩放后阅读；流程图没有布局警告。
- A/B 页面通过本机 HTTP 打开。浏览器实测模块目录能到达“原生图接入与交互适配”；首页图位置链接打开并居中“维护指引”卡片，护照显示全部 5 条对应记录；进入组织指引后用顶栏返回，节点选择、护照和相机变换与离开前一致。更新入口显示空列表。

浏览器检查使用 1280 × 720 视窗。嵌入图的鼠标点击受浏览器工具坐标限制，护照与条目跳转改用图原有的键盘入口完成；本次没有把它记作新的鼠标交互验收。未改变阅读运行代码，未重新运行下述历史运行测试或长期开发对照。

两个带行号的历史 JSONL 来源仍只显示定位文字，原文件存在；它们不是页面内阅读链接，按指定会话检索回查。其他已声明且直接链接的资料按阅读器规则导出快照。此边界与图字号提示不影响当前地图结构检查的结论。

## 此前的首次重组

日期：2026-09-16。当时沿用原自身地图 project_id 与全部 31 个已有记录 ID，整理后有 47 项记录。原四个模块入口迁入各自 overview，补齐维护指引、定位、记录接口、文档导航、Archify 适配、HTTP 服务和会话查询的职责与接口。正式需求继续绑定原设计方案。以下保留那次修订的检查范围。

### 地图与当时能力

模块指向分发仓库的实际文件，接口完整定义由提供方参考文档、源码或上游 schema 维护。实现与验证独立保存。此地图目录已有独立 Git 历史，原状态可以回查。

用户在本次维护中要求停止维护连续文档。当前设计、阅读模板、样式、生成参数、模块说明和自身架构/流程图已统一为 A 项目概览与 B 项目条目。旧模式地址包含有效条目时转到对应条目，没有条目时使用默认概览。此项属于用户决定的功能退役，旧验证记录只作为历史依据。

### 当时检查

- 地图加载与结构检查通过；保留全部旧 ID。声明的本地来源存在，当前记录链接和章节目标均可解析。
- 65 条关系规范化后仍为 65 条。架构图 14 个节点、流程图 8 个节点均有明确记录映射，旧原生节点 ID 保留。
- 两张图的原生交付成功。自身架构图没有交叉与标签重叠；全图适配时存在小字号提示，需缩放阅读。流程图严格布局检查通过。
- 删除连续文档后的阅读、URL 导航、Markdown/原资料、图形嵌入和画布相关检查：37 项通过。分发源码与 Codex 安装版的 Skill 格式检查通过，修改的运行文件逐一核对一致。
- 浏览器检查两种阅读入口、模块目录、正文定位和架构图显示。原生图交付、浏览器检查与长期开发收益分别记录。

旧设计中的两个 JSONL 文件加行号保持来源定位文字；原始会话没有打包进阅读器，回查使用指定会话检索。其余声明的文档来源通过页面读取本次快照。原资料页不递归收录全部邻接文件。

此前的 80 项检查属于阅读器上一轮修订。这里不将历史结果计作本次新增验收，也没有用地图数量、建图成本或文档长度证明后续开发效果。

本页保留 2026-09-16 当时的验证范围与数量，不能作为后来版本的验收声明。2026-09-19 的 LLM 检索、源码发现与说明归档检查见 [[VER-llm-retrieval]]。

当前安装与在线静态发布的验证范围见 [[VER-public-map]]。
