---
sprint_slug: "2026-07-10-athena-9-9-1-agent-skill"
roadmap_item: "agent-skill-contract"
path: "Refactor"
created: "2026-07-10"
---

# Design — Agent and Skill Contract

## Scope

实现 release 总设计 AC2、AC6–AC9、AC12、AC21：升级双端提示词身份；改用 Codex 0.144.1 native collaboration；read-only agent 只返回结果；主线程串行落盘；清除非 migrate `details/`；双端 31/31 skill frontmatter 合规；共享语义对称、运行时差异不机械同步。

## Acceptance

- CX 热路径无 `spawn_agent --cwd`、`assign_task`、裸 `wait` 或 shell agent TOML。
- worktree 合约为主线程创建、任务携带绝对路径、agent 验证 pwd/workdir，不宣称 native spawn 有 cwd 参数。
- reviewer/spec-compliance 并行返回；主线程合并后 evaluator 再判定。
- read-only agents 无文件写入指令；非 migrate `.ai_state/details` 为 0。
- CC/CX 各 31/31 SKILL.md 通过官方 quick_validate。
- 9.9.1 prompt 保留 outcome/permission/evidence/stopping，移除 visible CoT 与极端格式绝对规则。

## Design Review

继承 release 总设计三轮 critic PASS；写集与 CX runtime/installer 无重叠。
