---
id: EXP-overwrite-sync
kind: exploration
title: 用整目录覆盖实现同步的探索
summary: 样例曾观察到离线删除无法传播，因此在指定条件下未达到同步目标。
aliases: [覆盖同步, 整个文件夹覆盖]
status: failed
relations:
  - relation: derived_from
    to:
      record_id: VER-overwrite-sync
---

# 用整目录覆盖实现同步的探索

试图解决的问题是两个目录保持一致。尝试方法只把仍然存在的源文件复制到目标，不维护删除信息。

样例设定中的失败条件：材料在源端离线删除后再次复制，目标中旧文件仍保留，因此目录内容不一致。这个失败只针对需要传播删除的同步目标；简单复制归档不要求同样的删除语义。

如果未来引入显式删除记录和冲突规则，可以重新考虑同步；本项目当前只做归档，不将该探索升级为待开发功能。观察细节单独在 [VER-overwrite-sync](../verification/VER-overwrite-sync.md)。
