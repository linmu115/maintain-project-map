# 本地材料归档工作流

这份项目是独立的合成验证样例。日期、事件和材料均为测试数据，不是用户历史会话或已经发生的真实项目事件；样例不注册到个人项目索引。

## 当前能力

接收本地 UTF-8 文本材料，复制到指定输出目录，并生成来源清单。保持输入不变；目前每个输入按原文件名保存，尚未处理不同目录下的同名文件。

- [归档要求](records/requirements/REQ-local-archive.md)：本地保存、保留来源、原始材料保持不变。
- [归档交付接口](records/interfaces/IF-archive-package.md)：使用者交给工作流什么，以及在哪里找结果。
- [实际实现](records/implementation/IMP-archive-v1.md)：当前入口、能力和限制。
- [检查范围](records/verification/VER-archive-v1.md)：与实现说明分开，按需核对。

## 设计与边界

- [归档步骤](records/modules/MOD-archive.md) 只整理本机提供的材料；后续阅读 Skill 用薄引用连接。
- [本地交付决定](records/decisions/DEC-local-delivery.md) 解释为何取消旧的自动共享，并保留其查找入口。
- [语义检索建议](records/requirements/REQ-semantic-search.md) 仍为提议，未进入本轮实现范围。

## 历史与探索

- 旧称“分享卡片”“自动发出去”：见 [自动共享退役记录](records/modules/MOD-auto-share.md)。
- “整目录覆盖同步”的失败条件：见 [同步探索](records/explorations/EXP-overwrite-sync.md)。
- 合成来源材料：[需求演进记录](sources/design-events.md)。
