# VibeCoding Hermes Kernel v9.5

发布日期: 2026-05-09
基线: v9.4.5
平台版本要求: Claude Code ≥ v2.1.121

## 哲学定位

v9.5 是 **架构级减重 + 平台升级** 版本。

v9.4.x 系列累积了一些"看起来像在防御 LLM 偏见，实际是 anti-pattern"的设计：18 条 deny 列表把正常 Read 都拦了；9 条 pre-bash-guard 重复管控；全局 lessons 系统试图做跨项目知识管理；反 LLM 偏见段反复说"禁止 X"试图驯服模型。这些都是用墙挡水——挡得越多，水越要绕路。

v9.5 拆掉这些墙，用更少的硬约束 + 更明确的正向证据要求 + just-in-time 上下文注入，让 agent 在更少干扰下自然按工程纪律工作。同时接入 Anthropic 4-5 月发布的多个平台新能力（updatedToolOutput / SessionEnd / TaskCreated / effort.level）。

## 核心变更

### 减重（删除）

- `~/.claude/lessons/` 全局系统 + `lesson-drafter.cjs` + `lesson-archiver.cjs` + `lesson-curator/` skill
  - 知识管理不是 Hermes 职责。需要跨项目记忆 → 装 [claude-mem](https://github.com/AnyResearch/claude-mem) 或 superpowers
- `permissions.deny` 列表 18 → 0
  - agent 频繁撞墙，正常 Read 都被拦。改用流程约束 + design.md 边界 + evaluator 兜底
- `pre-bash-guard.cjs` 9 → 3 条灾难级（rm 根 / curl-pipe / mkfs-dd）
  - 其他靠流程约束兜底
- CLAUDE.md `反 LLM 偏见` 段（6 条禁止）
  - 反复"禁止 X" 是 anti-pattern，会反向暗示。改铁律 6（完成度证据）正向要求
- 铁律 9 → 7：合并 8/9 为铁律 6（完成度证据）+ 铁律 7（出处优先）；删除铁律 6 自审先行（与 Review 重复）
- `PreToolUse` Bash hooks 4 → 1（合并冗余 matcher）

### 增量（新增）

- **CLAUDE.md altitude 注释** — 明确这是 constitution（identity + iron rules + design principles），不规定步骤
- **just-in-time R₀** — 不预加载 tasks/lessons 内容，只注入计数；按需 read
- **subagent token 预算 ≤ 2000** — generator/evaluator/reviewer 全部加上（Anthropic 多 agent research 经验）
- **3 个新 hook**（CC v2.1.116-121 新事件）:
  - `output-evidence-augmentor.cjs` (PostToolUse, **默认 disabled**) — review 阶段 Edit/Write 后，没生成 review-report.md → 在工具输出尾部追加软提示。`updatedToolOutput` 字段（v2.1.121+ 全工具支持）
  - `session-end-reminder.cjs` (SessionEnd, async) — 退出时检查 tasks 未完成 + git 未提交 → systemMessage
  - `task-created-advisor.cjs` (TaskCreated, async) — 任务主题与当前 stage 不符 → 软提示
- **effort.level 感知** — `session-start.cjs` 和 `subagent-retry.cjs` 读 CC 2.1.133+ 输入的 effort.level，max effort 时降低注入频次
- **PACE 节点插件推荐表** — pace/SKILL.md 列出每个路径 best-fit 插件（superpowers / debugger / shipyard / context-mode 等），不强依赖
- **跨平台路由建议** — pace/SKILL.md 提示终端密集任务可委派 Codex（Terminal-Bench +12pp）

### 修订

- 铁律 4 措辞 — `Review 强制（Feature+ 至少一次交叉审查）` 不变，但 evaluator 反伪装检查改引"铁律 4 + 铁律 6"
- 失败处理协议 — 移到 pace/SKILL.md，作为流程文档而非铁律条目
- subagent-retry 触发消息 — 350 → ~200 字符，引用铁律 6（完成度证据）

## Hook 清单（v9.4.5 → v9.5）

| Hook | v9.4.5 | v9.5 | 备注 |
|------|--------|------|------|
| session-start | ✓ | ✓ (改) | 删 INDEX 注入 / just-in-time / effort 感知 |
| pre-bash-guard | ✓ 9 条 | ✓ 3 条 | 仅灾难级 |
| subagent-retry | ✓ | ✓ (改) | 引铁律 6 / effort 感知 |
| delivery-gate | ✓ | ✓ | 微调 |
| permission-request | ✓ | ✓ | 不变 |
| pre-compact-save | ✓ | ✓ | 不变 |
| post-compact-restore | ✓ | ✓ (改) | just-in-time |
| **output-evidence-augmentor** | — | ✓ 新（默认 off） | review 阶段提示 |
| **session-end-reminder** | — | ✓ 新（async） | 退出提醒 |
| **task-created-advisor** | — | ✓ 新（async） | 阶段一致性 |
| ~~lesson-drafter~~ | ✓ | ✗ 删 | |
| ~~lesson-archiver~~ | ✓ | ✗ 删 | |

净增: +1（7 个 cjs 文件 → 10 个，删 2 个 + 加 3 个）。settings.json 覆盖事件 7 → 9（+SessionEnd、+TaskCreated）。

## 平台升级

- CC 最低版本 v2.1.111 → v2.1.121（updatedToolOutput 全工具支持）
- 利用 v2.1.116+ 的 SessionEnd / TaskCreated 事件
- 利用 v2.1.121+ 的 updatedToolOutput 字段（PostToolUse 任意工具，不仅 MCP）
- 利用 v2.1.128+ 的 subagent prompt cache（~3× cache_creation 减少）
- 利用 v2.1.133+ 的 effort.level 输入字段

## 升级路径（从 v9.4.5）

```bash
# 备份
mv ~/.claude ~/.claude.bak.v94

# 解压新版到 ~/.claude
unzip -d ~ vibecoding-hermes-v95-claude-code.zip

# 用户级 settings 合并 (本地 customizations)
diff ~/.claude.bak.v94/settings.json ~/.claude/settings.json
# 手动合并需要保留的 customizations

# 全局 lessons 数据可保留参考但不再被 Hermes 引用
mv ~/.claude.bak.v94/lessons ~/legacy-lessons/

# 验证
claude --version  # ≥ 2.1.121
ls ~/.claude/hooks/*.cjs | wc -l  # 应 ≥ 7
```

## 已知限制

- `output-evidence-augmentor` 默认 disabled。开启需要在 settings.json 加 `env.VIBECODING_AUGMENTOR=1`
- `SessionEnd` / `TaskCreated` async hook 不阻塞主流程，仅产生 systemMessage
- 跨平台一致性：Codex 端无 SessionEnd / TaskCreated / updatedToolOutput 平台支持，相应 hook 仅 CC 端

## 致谢

设计灵感：
- [Anthropic — Effective context engineering for AI agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
- HumanLayer 团队的 CLAUDE.md ~60 行经验
- claude-mem / superpowers 跨 session 记忆方案
