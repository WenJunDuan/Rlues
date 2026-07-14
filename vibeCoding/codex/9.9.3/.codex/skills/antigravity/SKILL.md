---
name: antigravity
description: |
  通过 `agy -p "..."` 命令调度 Google Antigravity CLI (subagent / 并行任务).
  Athena 在 CX 端可用此 skill 把"重的、可并行的、不需要 CC 自己跑"的任务外包给 Antigravity.
  Antigravity 由用户的 Google 账号驱动, 默认使用 Gemini 3.5 Flash, 适合大批量、可独立切片的任务.
  注: 用户不直接用 Antigravity, 调度由 Athena 负责.
---

# /antigravity — Athena 端 agy 调度 skill (v9.6.2)

## 概念

Antigravity CLI (命令 `agy`) 是 Google 在 2026-05-19 替代 Gemini CLI 的 Go 编写的终端 agent.
- 官方文档: https://antigravity.google/docs/cli-using
- 官方 transition: https://developers.googleblog.com/an-important-update-transitioning-gemini-cli-to-antigravity-cli
- Headless 调用: `agy -p "<prompt>"` (单次, 适合 Athena 外包)
- TUI 模式: `agy` (用户直接交互, 但 Athena 场景下不用)

## Athena 如何使用 agy (3 个场景)

### 场景 1: 并行 fan-out (impl stage 大批量任务)

任务清单 ≥ 5 个独立可并行的小任务 → 用 agy 并行跑.

```bash
# 主 agent (CX) 把每个 Task 描述写成 prompt, 并行调度 agy
for task in tasks/*.md; do
  (agy -p "$(cat "$task"). 严格按 task 描述实现, 完成后输出 diff." \
    >"/tmp/agy-$(basename "$task").log" 2>&1) &
done
while jobs -pr | grep -q .; do sleep 1; done
```

**何时用**:
- 5+ 个独立小任务 (例如批量重命名、批量加 type hint、批量改 import)
- Task 之间不互相依赖
- 单个 Task 上下文 ≤ 2000 tokens 可表达完整

**不适合**:
- 互相依赖的 Task (用主 agent 顺序处理)
- 涉及 .ai_state 写入 (主 agent 集中管 state)
- 涉及 git commit (主 agent 集中 commit, audit trail 统一)

### 场景 2: 调研 / 文档查询外包 (plan / review stage)

CX 端要查官方文档 / 大型 codebase, 但 CC 自己跑会占用主上下文.

```bash
# 把调研外包给 agy, 收到 markdown 结果回主 agent
agy -p "调研 React 19 useEffect 的最新最佳实践 (2026). 给出 3 个权威链接 + 关键引用. 输出 markdown."
```

**何时用**:
- 复杂的多文档调研 (CC 自己跑会消耗大量上下文)
- 用户开了 Antigravity 而 context7 / docs_researcher 未配置

**不适合**:
- 简单的"查这个 lib 的 API" (直接用 ctx7 即可, 不需要 agy)
- 需要严格审计 / 引用的研究 (优先 ctx7 + WebFetch 因为可见度高)

### 场景 3: 长任务后台运行 (Refactor / System 路径)

Refactor 一整个模块 (e.g. "把 callback 模式全部改成 async/await") 可能 1 小时, 主 agent 跑会卡死.

```bash
# 后台启动
agy -p "Refactor src/legacy/ 所有 callback 模式为 async/await. 保持测试通过. 写完后 echo DONE." \
  > /tmp/agy-refactor.log 2>&1 &
AGY_PID=$!

# 主 agent 继续做别的事, 定时 check
while kill -0 $AGY_PID 2>/dev/null; do
  sleep 60
  tail -5 /tmp/agy-refactor.log
done
```

**何时用**:
- 长 Refactor (≥ 30min)
- 主 agent 还有别的子任务可并行做
- 改动可清晰边界化 (不会破坏全局)

**不适合**:
- 跨 module 改动 (需要全局视角, 不适合后台)
- 涉及 .ai_state state machine 推进 (主 agent 集中管)

## 检测 agy 是否可用

athena-init 跑这一行, 写入 `_index.md.ag_callable`:

```bash
if command -v agy >/dev/null 2>&1; then
  agy --version >/dev/null 2>&1 && AG_CALLABLE=true || AG_CALLABLE=false
else
  AG_CALLABLE=false
fi
```

如果 `ag_callable=false`:
- 主 agent 不要尝试调 agy (会失败)
- 大批量任务降级到主 agent 顺序处理, 或用 Codex 原生 `spawn_agent` fan-out

## 与其他工具的优先级

当主 agent 需要"并行执行 N 个独立 Task"时:

| 优先级 | 工具 | 条件 |
|---|---|---|
| 1 | CC 当前 subagent 机制 | N ≤ 4 (以当前 session 限制为准) |
| 2 | Codex `spawn_agent` fan-out | CX 可用且切片写集互斥 |
| 3 | Antigravity `agy -p "..." &` 并行 | N ≥ 5 且 `ag_callable = true` |
| 4 | 主 agent 顺序处理 | 其他机制不可用 |

## 调度时的硬约束

1. **每个 agy 调用必须 prompt 包含足够上下文**, 因为 agy 是独立 session, 不见 .ai_state
2. **agy 完成后, 主 agent 必须显式 review 它的输出** (不是 blind merge), 因为 agy 用 Gemini 3.5 Flash, 写代码风格可能不一致
3. **agy 不允许写 .ai_state** (那是主 agent 的 state, 集中管才有 audit trail)
4. **agy 不允许 git commit** (commit msg 必须符合 git-conventions, 主 agent 集中做)
5. **agy 输出 diff/patch 而非直接改文件**, 主 agent review 后用 apply_patch 或 Edit 工具落地

## 与 _index.md 联动

`_index.md.platform_features.ag_parallel_subagents` 和 `ag_headless_p` 用于决策路由.

每次主 agent 进入 impl 或 review stage, 先读 `_index.md.tools_available`:
- 若 `ag_callable = true` 且任务符合场景 1-3 → 调度 agy
- 否则 → 走其他路径

## 例外与降级

- 若 `agy` 命令存在但调用失败 (网络 / 认证): 主 agent 在 `sprints/{current_sprint_slug}/runtime-events.md` 记录 `ag-call-failed`, 自动降级
- 若 `agy` 输出明显是垃圾 (例如长度 > 50KB 或包含 prompt 泄漏): 主 agent 拒绝 merge, 重新发更精确的 prompt
- agy 连续失败 ≥ 3 次 → 当 session 禁用 agy, 后续都走降级路径

## 参考

- 安装: https://antigravity.google/docs/cli-using
- Slash commands: https://geminicli.com (旧 Gemini CLI 文档, 命令大部分继承)
- 模型列表 (2026-05): Gemini 3.5 Flash (默认), Gemini 3.1 Pro, Claude Sonnet, Claude Opus, GPT-OSS 120B
- 个人版 free tier (preview): 比 OpenAI Codex 个人额度大, 适合并行 fan-out
