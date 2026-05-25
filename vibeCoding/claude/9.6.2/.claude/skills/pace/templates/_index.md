---
# Athena PACE 工作状态 (.ai_state/_index.md)
# v9.6.2 schema. 项目执行 athena-init 时由模板初始化, 之后由主 agent + hooks 维护.
version: "9.6.2"

# === PACE 路由状态 ===
path: ""              # Hotfix | Bugfix | Quick | Feature | Refactor | System
stage: ""             # plan | design | impl | review | polish | ship
current_sprint: 1
skip_polish: false    # 项目级 opt-out (默认 false, Refactor/System 强制 polish)

# === 平台与版本 ===
platforms_enabled: ["cc"]   # cc | cx | both. 项目用哪些 Athena 端
cc_version: "claude-code 2.x"      # 由 athena-init 探测
cx_version: ""                     # 留空表示项目未用 cx; 若用, 由 athena-init 探测 e.g. "codex-cli 0.133.0"
ag_callable: false                 # antigravity (agy) 是否可调度? athena-init 检测 `which agy`

# === 平台原生能力 (athena-init 探测后填) ===
# 用于 PACE 决策 "用哪个工具最优"
platform_features:
  cc_subagent_task: true                     # CC Task tool 调度 subagent (always true)
  cx_spawn_agent: false                      # Codex spawn_agent (要 0.128+)
  cx_spawn_agents_on_csv: false              # Codex 批处理 (要 0.128+ + features.multi_agent)
  cx_goal_default_on: false                  # Codex /goal 默认开启 (0.133+)
  ag_parallel_subagents: false               # Antigravity 并行 subagents (always true 如果 ag_callable)
  ag_headless_p: false                       # agy -p "..." 可用 (always true 如果 ag_callable)

# === 工具可用性 (athena-init 探测) ===
tools_available:
  context7_cli: false        # npx ctx7 可用? (true if `npx ctx7 --version` 退码 0)
  context7_mcp_cx: false     # ~/.codex/config.toml [mcp_servers.context7] 配置且启用?
  augment_mcp_cc: false      # ~/.claude/mcp.json augment-context-engine 配置?
  augment_mcp_cx: false      # ~/.codex/config.toml [mcp_servers.augment-context-engine]?
  web_search_cc: true        # CC WebSearch tool (always true)
  web_search_cx: false       # Codex web_search = "live"?
  rg_available: true         # ripgrep
  jq_available: true

# === 进度计数 (由 index-updater hook 自动维护, 不要手填) ===
counts:
  features_count: 0
  reviews_count: 0
  cleanup_count: 0

# === Pointer (指向当前最新的相关文件) ===
pointers:
  latest_design: "details/design.md"
  latest_review: ""           # e.g. details/reviews/sprint-1.md
  latest_cleanup: ""          # e.g. details/cleanup-pass-1.md (仅 Refactor/System)
  latest_lessons: "lessons.md"

# === Fingerprint (由 index-updater hook 维护, 用于 mtime 比对触发 recount) ===
fingerprint: ""
---

# Athena Project State Index

> 本文件由 Athena 自动维护. 不要手工修改 frontmatter 字段以外的部分除非你知道你在做什么.

## 当前状态

[由主 agent 在 stage 切换时简短追加, 例如]
- `2026-05-23 14:00`: athena-init 完成, 进入 plan stage (path=Feature)
- `2026-05-23 14:32`: design.md 写完, 进入 impl stage

## 工具调度建议 (PACE 工作时主 agent 读这里)

根据 `tools_available` 字段, 当前可用工具:

### plan stage 调研
1. **优先**: 若 `context7_cli`: `npx ctx7 resolve <lib>` + `ctx7 get-docs <id> --topic <T>`
2. **次选**: 若 `augment_mcp_cc`: 通过 MCP `search_context` 语义检索项目代码
3. **兜底**: WebSearch + WebFetch (官方文档)

### impl stage 写代码
1. CC 端: 主 agent 或 Task `subagent_type: generator`
2. CX 端 (if `cx_spawn_agent`): `spawn_agent generator.toml`
3. **大批量并行任务** (≥ 5 个独立 Task):
   - 若 `cx_spawn_agents_on_csv`: 用 Codex CSV 批处理 (`spawn_agents_on_csv`)
   - 若 `ag_parallel_subagents`: 调度 `agy -p "..."` (Antigravity 异步 subagents, 见 `skills/antigravity/SKILL.md`)
   - 否则: 主 agent 顺序处理

### review stage
1. CC: Task `reviewer` + `evaluator` (并行)
2. CX (if available): `spawn_agent reviewer + pr_explorer + evaluator`
3. 文档调研: `docs_researcher.toml` (cx) 或主 agent web_fetch

### polish stage (Refactor / System 强制)
1. CC: 主 agent 加载 `~/.claude/skills/polish/SKILL.md`
2. CX: `spawn_agent polish_worker.toml` (network=true 查最佳实践)
3. 完成后 → `cleanup-pass-{sprint}.md` + stage 转 ship

## 历史 (按时间倒序, 最多保留近 10 条)

[由 pace-continuator hook 自动追加]
