---
id: IMP-archive-v1
kind: implementation
title: 当前归档入口
summary: 可复制 UTF-8 txt/md 材料并生成来源清单；同名冲突仍未处理。
status: active
progress: implemented
gap: 不同目录的同名输入可能覆盖；失败可能留下部分输出。
relations:
  - relation: implements
    to:
      record_id: REQ-local-archive
  - relation: implements
    to:
      record_id: IF-archive-package
---

# 当前归档入口

使用方式：`python workflow/archive.py --out 输出目录 输入文件...`。入口支持 `.txt` 与 `.md`，副本沿用输入文件名，来源清单为 `manifest.json`。

## 当前限制

- 不同目录下的同名文件会落在相同输出位置，当前没有冲突处理。这是有依据的缺口，见 [EVT-05](../../sources/design-events.md#evt-05--同名输入仍未解决)。
- 出错前已经生成的文件可能留下；不能把这次执行当成完整成功。
- 本样例尚未运行真实验收。代码存在不等于已经验证所有行为。

代码：[archive.py](../../workflow/archive.py)。详细检查范围单独保存在 [VER-archive-v1](../verification/VER-archive-v1.md)。
