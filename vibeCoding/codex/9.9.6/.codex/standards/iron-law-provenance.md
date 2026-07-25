---
version: "9.9.6"
purpose: "铁律溯源表 — 每条铁律追溯到一次具体失败 (ratchet principle)"
note: "冷路径, 不自动注入。要判断某条铁律能不能动时 Read 本文件。"
---

# 铁律溯源

> 来源: harness engineering 的 ratchet principle —— **每条规则都要能追溯到一次具体的失败**。
> 追不到出处的规则是凭空立的, 应当被质疑; 追得到的, 改动前必须先读懂当初踩的坑。

| 铁律 | 起因 | 档案 |
|---|---|---|
| [门禁即律法] | 声称完成但无证据的"静默假过"反复出现, prompt 层劝导无效 | `compound/2026-07-08-decision-token-usage-null-and-subagent-stop.md` |
| [零写入·按区路由] | 并行 generator 在主 checkout 互相覆盖; worktree ledger 与实际 checkout 数对不上 | `compound/2026-07-11-learning-worktree-generator-ledger-gap.md` |
| [分诊先行] | 路由凭感觉选路径, 改动面超路径上限后无人回头重审 | `compound/2026-07-08-learning-hook-order-and-worktree-counts.md` |
| [文档即真相·索引先行] | 全量 glob 扫描把上下文烧光; 状态散在多处互相矛盾 | `compound/2026-07-13-decision-index-field-audit.md` |
| [证据与出处] | Codex 侧 wire evidence 缺失时被当作通过, 需改 fail-closed | `compound/2026-07-10-learning-codex-wire-evidence-fail-closed.md` |
| [复利颗粒化] | 经验写成长文档后无人回读, 一事一档才被复用 | `compound/README.md` |
| [反过度工程] | v9.7 一次调研产出 24 个文件, 无痛点数据支撑, 被自己否决 | 9.9.3 CHANGELOG "Anti-Overengineering" |
| [Standards ≠ Codex .rules] | 曾把用户工程规范与 Starlark 命令权限文件混为一谈，导致规范被写进不会注入 prompt 的权限层 | 9.9.6 `AGENTS.md` 平台边界审计 |
| [Hook 是进化器] | 规训写在 prompt 里会被模型自行权衡掉, 机械规则必须落 hook | `compound/2026-07-08-learning-hook-order-and-worktree-counts.md` |
| [四原语] | CC/CX 伪造对称工具名, 产生永不触发的死分支 | 9.9.6 review: CX matcher 曾含 `MultiEdit` (Codex 无此工具名) |

## v9.9.6 新增待立条目 (下版评估是否升为铁律)

| 候选 | 起因 (9.9.6 实测) |
|---|---|
| **常驻预算是一等约束** | SessionStart 实测 7,801 B、skill 热路径 93 KB, 全部超预算且从没测过; 按字符截断中文导致实际超 3 倍 |
| **全局 env 不得凌驾角色配置** | `CLAUDE_CODE_SUBAGENT_MODEL` 官方定义即覆盖 frontmatter, 设了它整个角色矩阵静默失效 |
| **同事件多写者必须原子写** | PostToolUse/Stop 上 2–3 个 hook 非原子写同一 `_index.md`, 丢的是门禁标记且不报错 |
| **文档层不可作为一手事实** | changelog / 文档页 / JSON schema 三者互相矛盾, 只有 schema 与源码 tag 能定音 |
| **护栏强度须匹配权限面** | CX 在 `approval_policy=never` + `danger-full-access` 下, guard 覆盖面只有 CC 的 1/4, `rm -rf /*` 曾直接放行 |
