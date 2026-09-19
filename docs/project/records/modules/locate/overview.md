---
{
  "id": "MOD-locate",
  "kind": "module",
  "title": "找到当前项目地图",
  "status": "current",
  "summary": "按项目名称、别名、ID 或明确位置找到地图；维护本机目录，区分当前工作树、默认位置和失效入口。",
  "relations": [
    {
      "relation": "implements",
      "to": {
        "record_id": "REQ-map"
      }
    },
    {
      "relation": "flows_to",
      "to": {
        "record_id": "MOD-records"
      },
      "reason": "用户请求生成阅读页面时，把明确的地图位置交给记录读取器。"
    },
    {
      "relation": "provides",
      "to": {
        "record_id": "IF-project-location"
      }
    }
  ],
  "sources": [
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
      "path": "maintain-project-map/references/operations.md",
      "role": "skill-source-authority",
      "workspace_id": "source",
      "reviewed_sha256": "d7c4d10f51271240631bfa6155d8841e9d6524a80cfdf04df54ef409b955f3a6",
      "reviewed_dependencies": []
    }
  ],
  "source_review": {
    "reviewed_at": "2026-09-19T08:50:28.323998+00:00",
    "reason": "复核原字节归档规则允许 CRLF 保留；真实 Git 往返验证通过，公共导出和本机读取行为不变。",
    "body_sha256": "55cab5992327e38b74f26882e97596b34eed561031fa7776937d42e77d7bed05"
  }
}
---

# 找到当前项目地图

项目 ID 是长期身份，本地路径负责到达文件。当前工作树有明确地图时使用它；一个 ID 对应多个可用位置且不能判断上下文时，需要指定位置，不能随便选一份。

用户说“看 Archify 的项目地图”时，先通过名称或别名查本机登记，拿到清单后再围绕问题读取内容。无须用户重新给路径；查询只返回位置和简短元信息，不预载地图正文或开发历程。

注册表保存名称、别名、稳定 ID、位置和明确指定的默认工作副本。重复登记不重复写入；新建、接入、实质更新或搬迁时由 Skill 主动核对。没有后台全盘扫描。默认位置丢失会报告失效，不自动换成旧副本。

目录只接入本 Skill 的项目地图。MRS 软件的开发地图属于项目地图；B/C 题等 MRS 研究地图不在本能力范围。样例、测试、候选与视频导出副本不自动成为当前入口。

代码入口：maintain-project-map/scripts/map_catalog.py 与 project_map.py。实现和核查见 [[IMP-map-catalog]]、[[VER-map-catalog]]。


定位约定见 [[IF-project-location]]；长期身份与工作树的区别见 [[OBJ-map-identity]]。
