# 项目级经验沉淀 (Lessons Learned)

<!--
每个 Sprint 通过 Gate 后由 compound skill 追加。append-only, 不删不改历史。
本文件存项目级业务代码经验 (Athena 不做跨项目知识管理)。
跨项目记忆请装 claude-mem 或 superpowers。

格式 (v9.6.1: 每条 lesson 附校准标签, 铁律 10):

## [YYYY-MM-DD Sprint N] 一句话标题
- **Pattern**: 解法描述 (文件:行号) [executed | inspected | assumed]
- **Pitfall**: 坑点描述 [executed | inspected | assumed]
- **Constraint**: 新约束 [executed | inspected | assumed]

示例:

## [2026-05-21 Sprint 1] JWT refresh 不能和 access 共享 secret
- **Pattern**: 分开 secret + rotation key 在 env (src/auth/config.ts:15) [executed]
- **Pitfall**: Authorization header 大小写处理不一致, 用 lodash.toLower 前置 [executed]
- **Constraint**: Redis 需要 ≥256MB 才放得下 session cache [inspected: 查 prod metrics]
-->
