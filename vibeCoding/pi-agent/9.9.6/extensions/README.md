# extensions/ · Phase-2 已落地 (2026-08-03)

架构: **适配器模式** — CC 端 hooks 逻辑一行不改 (cc-core/, 与 claude/9.9.6 同源, schema parity 天然成立), TS 适配器只做 pi 事件 ↔ CC hook 协议转换。

| 文件 | pi 事件 | 复用的 cc-core |
|---|---|---|
| `athena-gates.ts` | `tool_call` (bash/edit/write) · `agent_end` | pre-bash-guard.cjs · delivery-gate.cjs |
| `athena-lifecycle.ts` | `session_start` · `before_agent_start` · `session_before_compact` · `session_compact` | session-start.cjs · stage-breadcrumb.cjs · compact-snapshot.cjs · compact-restore.cjs |

## cc-core 相对 CC 原版的差异 (仅 2 处, 均为路径)

1. `session-start.cjs`: rules 索引优先 `~/.pi/agent/rules/_index.md`, fallback `~/.claude/rules/`
2. `stage-breadcrumb.cjs`: stages.md 优先 `~/.pi/agent/skills/pace/references/`, fallback `~/.claude/skills/pace/references/` (pace skill 未迁移前 fail-open 零注入)

## 语义降级 (设计决策, 非 bug)

- **Stop 门禁**: pi 无硬 block 停止 → `agent_end` 检出阻断时发 followUp 纠偏消息; 同一 reason 不重复发 (防轰炸, 对应 CC 熔断器意图), 改 ui.notify 交人工
- **hook 崩溃/超时 → 放行**: 对齐 CC 平台 hook 超时语义, 只有显式 block 才拦

## 测试

```bash
pi -e ./extensions/athena-gates.ts "跑一下 rm -rf /"       # 期望 block
pi -e ./extensions/athena-lifecycle.ts                      # 含 .ai_state 项目内起会话看注入
```

未迁移 hooks 与原因见 ../MIGRATION.md。新增扩展前先问 dogfood 数据 (铁律[反过度工程])。
