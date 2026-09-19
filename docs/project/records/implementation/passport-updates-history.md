---
{
  "id": "IMP-passport-updates-history",
  "kind": "implementation",
  "title": "语义护照条目入口、更新记录与返回",
  "status": "current",
  "summary": "原映射抽屉已移入护照，侧栏增加按需更新入口；图链接居中卡片，返回恢复阅读状态。",
  "sources": [
    {
      "path": "maintain-project-map/assets/reader.html",
      "role": "skill-source-authority",
      "workspace_id": "source",
      "reviewed_sha256": "d8a8efae8efe5b4555fa8d896885a0bfde2b444f9f19f5456141e998bb1ed590",
      "reviewed_dependencies": []
    },
    {
      "path": "maintain-project-map/assets/diagram-records.js",
      "role": "skill-source-authority",
      "workspace_id": "source",
      "reviewed_sha256": "99c1dde3809c661661a545234d639ea80edc170ec576ad040d05d441d4438c73",
      "reviewed_dependencies": []
    },
    {
      "path": "maintain-project-map/assets/reader-history.js",
      "role": "skill-source-authority",
      "workspace_id": "source",
      "reviewed_sha256": "5ee09ad39b96b7d43fd0fc94c68aa379027e7346a81620d77242d4996822e25d",
      "reviewed_dependencies": []
    }
  ],
  "relations": [
    {
      "relation": "implements",
      "to": {
        "record_id": "REQ-passport-updates-history"
      }
    },
    {
      "relation": "implements",
      "to": {
        "record_id": "MOD-updates"
      }
    },
    {
      "relation": "implements",
      "to": {
        "record_id": "MOD-document-navigation"
      }
    }
  ],
  "source_review": {
    "reviewed_at": "2026-09-19T08:47:23.192869+00:00",
    "reason": "核对新增公共静态导出和归档 Git 原字节保护；147 项完整回归与后续 16 项专项通过。其他来源仅统一 LF，Git 内容差异确认未改逻辑，保留原说明并更新跨系统可复用基线。",
    "body_sha256": "8cf25c4f0fce19111b72d18e1929aeb63c1c21f841ac127b68236c13a558e809"
  }
}
---

# 语义护照条目入口、更新记录与返回

## 怎样使用

选中图形后点击卡片，语义护照里会显示该节点对应的全部项目条目，沿用节点名称加条目按钮的形式。图下的映射抽屉已移除。打开条目后，顶栏“返回”回到原来的图、所选节点及缩放平移位置。

侧栏“更新记录”读取 [[IF-update-record|用户明确要求保存的迭代文档]]；无记录时保持空状态，不从提交或验证日志自动编排内容。读更新时点击图位置链接，在当前页打开对应图并将卡片居中；再次点击卡片查看护照。当前节点失效时说明原因。

返回同时恢复页面、条目、页签、搜索、目录展开、文档滚动与画布是否选中；初始页面没有地图内历史时禁用按钮。浏览器前进后退共用同一份状态。

## 实现边界

正文图链接保存本张地图的图类型和节点 ID。它定位当前图；不会自动重建某次历史图。原生 Archify 原版文件保持独立，项目条目和页面历史桥接仅进入适配阅读副本。

验证范围独立见 [[VER-passport-updates-history]]。
