---
name: pace
description: >
  工作流路由器 (Codex 版). 收到开发任务时触发. 按任务复杂度路由到 6 条路径.
effort: high
---

# PACE — 6 路径路由器 (v9.6.1 Codex)

首先读 `.ai_state/_index.md` (铁律 8 索引先行). 有 stage → 从当前阶段继续.
.ai_state/ 不存在 → 提示 `/athena-init`.

## 路由 (同 CC)

```
          ┌─ 1行/配置 ──────→ Hotfix
 修复 ────┤
          └─ 需要调试 ─────→ Bugfix

          ┌─ 需求清晰/小 ──→ Quick
 新建 ────┤ 需要设计 ─────→ Feature
          ├─ 改现有结构 ───→ Refactor
          └─ 跨模块/服务 ──→ System
```

## Codex 端能力矩阵 (vs CC, v9.6.1 已对齐 Codex v0.128.0+ GA)

| 能力 | CC | Codex | Athena 接入方式 |
|------|-----|-------|-----------------|
| `/goal` autonomous loop | ✓ v2.1.139+ | ✓ **v0.128.0+ GA** | 见下"Codex /goal" 段 |
| `/batch` 自动并行 worktree | ✓ v2.1.121+ | ✗ | spawn_agent 多线程 ([agents].max_threads) |
| `/background` 多会话 | ✓ v2.1.139+ | ✗ | 用户自己开多个 codex session |
| PreCompact / PostCompact | ✓ | ✗ | 长任务点主动写 `_index.md` 保存 |
| Session memory | ✓ ~/.claude/projects/ | ✗ | 无 (cross_session_memory: "none") |
| Cross-session memory | ✓ claude-mem | ✗ | 用户人工同步 `~/.codex/AGENTS.md` |

参考:
- Codex /goal: <https://developers.openai.com/codex/changelog> (rust-v0.128.0, 2026-04-30)
- Codex /goal 内部 prompt: <https://github.com/openai/codex/blob/main/codex-rs/core/templates/goals/continuation.md>

## Codex /goal 接入 (v0.128.0+ GA)

Codex /goal 行为与 CC 等价: 持久化 thread-level 状态, 跨 session resume, 支持 create / pause / resume / clear.

启动方式:
- `/goal <objective>` — 创建或替换当前 goal
- `/goal pause` — 暂停
- `/goal resume` — 恢复
- `/goal clear` — 清除

每个 PACE stage 对应一个 condition 模板, 见 `templates/goal-conditions.md` 的 "Codex 端" 段.

平台特性检测: `athena-init` / `athena-setup` 调用 `codex --version` 解析版本号, 写入 `_index.md.platform_features.goal_supported` (≥ "0.128.0" → true).

**降级**: cx_version < v0.128.0 时, 由 `delivery-gate.py` (Stop hook) 兜底判定 VERDICT.

## Codex 优势 (vs CC)

| 信号 | Codex 更适合 |
|------|------------|
| 终端命令为主 | Terminal-Bench 2.0 SOTA 82.7% (GPT-5.5 Apr 2026) |
| 大量同模式改写 | token 成本 0.25-0.33× CC, 适合"重复劳动" |
| 多模型互审 | Codex 主跑 + 调 web_search 验证 |

## 跨平台路由建议

Codex 端在以下情况主动建议用户切到 CC:
- 任务需要 `/batch` 自动 worktree 隔离 (Codex 端只有 spawn_agent, 无 worktree)
- 任务需要 PreCompact/PostCompact 跨长会话快照 (Codex 无 compact 生命周期 hook)
- 任务需要 Opus 设计能力 (跨模型最佳实践: Codex 实现, CC adversarial review)

不强制 — 是建议. **`/goal` 不再是切到 CC 的理由** (Codex v0.128+ 已对齐).

## 6 路径 (Codex 版, 简化)

### Hotfix · Bugfix
同 CC 版, 没有 stage. `apply_patch` 改 → `shell` 跑测试 → `git commit`.

### Quick (impl → review → ship)
TDD 实现 → /review (Codex 内置) → git commit.
路径升级监测 (同 CC).

### Feature (plan → impl → review → ship)
- **plan**: web_search 调研 + brainstorming → design.md → 用户确认 → tasks.
  可选: `/goal "design.md 含 File Structure Plan + tasks ≥ 1 + 用户确认"` (v0.128+)
- **impl**: 按 task 实现, TDD, 完成勾选 + progress 追加. 路径升级监测.
  可选: `/goal "tasks-current.md 全 [x] + <test_cmd> exits 0"` (v0.128+)
- **review**: /review + spawn_agent reviewer (Codex subagent, 见 [agents].max_threads). VERDICT.
- **ship**: git commit + 归档.

### Refactor (plan → impl → review → ship)
- **plan**: 用户确认重构方案 + design.md (before/after) + tasks-current.md.
- **impl**: 用 spawn_agent 多线程并发 (Codex 端不像 CC 的 /batch 自动 worktree, 需要手动多 agent 协作).
  - 设置 `[agents].max_threads = N` 控制并发度.
- **review**: 同 Feature.
- **ship**: 同上.

### System (plan → design → impl → review → ship)
完整流程. 长 stage 主动写 `.ai_state/_index.md` 保存 (Codex 无 compact 生命周期).

## 共享协议 (审查/发布同 CC 端)

### 审查协议 (Feature+ review 阶段共用)

```
1. /review → 第一份审查 (Codex 内置)
2. spawn_agent reviewer → 跨 reviewer 对抗审查
   → 必须看到真实 subagent job ID (铁律 6)
3. [System] 追加 web_search 查 OWASP / 最佳实践
4. @evaluator → VERDICT
   PASS → /compound → 停一轮让用户确认 → stage=ship
   CONCERNS → 修复 → 重新评分
   REWORK → stage=impl (Feature/Refactor) 或 stage=design (System)
   FAIL → stage=plan
```

### 发布协议 (ship 阶段共用)

```
1. [Quick] git commit
2. [Feature+] git tag + push
3. details/lessons.md (compound 已追加) + progress.md 最终更新
4. _index.md: stage="", sprint+=1
```

## 失败处理协议 (同 CC, 铁律 6 完成度证据)

工具失败 → 三轮重试 (改参数 / 换工具 / 拆任务). 三轮后报告完整 stderr + exit code.
spawn_agent 输出预算 ≤ 2000 tokens.

**禁止**: "请你手动执行" 作为首次响应.

## 状态管理 (铁律 5/8)

`.ai_state/_index.md` 单一入口. 协议字段同 CC 端. 跨平台一致 (铁律 6).

合法 path: Hotfix / Bugfix / Quick / Feature / Refactor / System
合法 stage: plan / design (System only) / impl / review / ship

Codex 无 compact 生命周期 → 不写 `compact-snapshot.md`, hooks 也无 PreCompact/PostCompact.
