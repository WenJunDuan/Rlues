# VibeCoding Hermes Kernel v9.5 (Codex CLI)

发布日期: 2026-04-29
基线: v9.4.5-hotfix-codex (35 文件 2467 行)
性质: **工程化升级**, 与 CC 端 v9.5 同步发布。Codex 平台特性受限, 部分 hook (TaskCreated/SessionEnd/agent hook) 在 CC 端实现, Codex 端用 process hook 模拟。

## 核心定位

> v9.4.5: PACE 是 prompt 描述, 靠 agent 自觉
> v9.5: PACE 是状态机硬约束, agent 想偷懒越不过 hook 这一层

CC + Codex 双端同步, 共享同一份 `.ai_state/` schema。

---

## 11 项进化 (Codex 端实现)

### A 类: 核心 PACE 工程化

#### A1: delivery-gate 状态机硬化

`hooks/delivery-gate.py` 重写, 11 种 check 规则与 CC 端完全对齐:
- file / has-pending-task / all-tasks-done / has-section / has-progress
- tasks-have-boundary / review-report / review-has-test / review-has-external
- verdict-ok / scenario-conditional

不满足出口条件 → `{"continue": false, "stopReason": <具体修复指令>}` (Codex Stop hook 协议, 等价于 CC 的 `{decision: "block", reason}`)。

#### A2: change-plan.md 强制 deliverable

新增 `templates/change-plan.md`, 与 CC 端完全一致 (图 06 七字段)。

#### A3: TaskCreated 等价 — user-prompt-submit hook 增强

**Codex 平台没有 TaskCreated 事件** (CC 独有). 替代方案:
- `user-prompt-submit.py` 的 `spawn-truth` trigger 增强:
  - 当 prompt 含 spawn_agent / reviewer / generator 关键词
  - 注入"阶段一致性提醒" (stage=plan 不要立即 spawn 写代码; stage=review 不要 spawn 改代码)

是 prompt 层注入, 不是事件 hook, 但触发面接近。

### B 类: 吸收图的工程化思维

#### B1: prompts/from-zero.md (吸收图 04)

与 CC 端完全一致, 无路径引用差异。

#### B2: prompts/change-existing.md (吸收图 05/06)

与 CC 端文本一致, 仅路径引用从 `.claude/` 改 `.codex/`。

#### B3: 4 元素口诀 (吸收图 07)

AGENTS.md 顶部加同样的 4 元素口诀 + 表格, 与 CC 端 CLAUDE.md 对位。

#### B4: PACE SKILL.md 加 scenario + RLPPV

- scenario 字段 + 场景驱动工作流差异
- RLPPV 五步显式命名
- project.json 模板加 `scenario` 字段
- vibe-init prompt 加场景启发式判定

### C 类: 平台特效正确使用

#### C1: PostToolUse:updatedToolOutput

`hooks/output-evidence-augmentor.py`:
- 自维护 `~/.codex/state/recent-tool-uses.jsonl` (ring buffer, 50 条)
- review 阶段 + apply_patch/write/edit 类工具触发, 检查 spawn_agent reviewer 调用证据
- 没证据 → `updatedToolOutput` 追加 `💡 Hermes 提示`

注: Codex stable 后扩展 hook 协议支持此特性, 与 CC 一致。

#### C2: lesson-drafter (Codex 端单轨)

**Codex 不支持 type:"agent" hook**, 仅有 process-based hooks。lesson-drafter 只有 Python 版本, 没有双轨。

跨端使用建议: 在 CC 端启用 agent 版本, 起草的 lessons 在 Codex session 也能 R₀ 读取 (共享 `~/.codex/lessons/` 通过用户手动同步, 或用 symlink)。

#### C3: SessionEnd 等价

**Codex 没有 SessionEnd hook** (单事件 notification 系统). 提供 `session-end-reminder.py` 作为独立脚本, 可被其他 hook include 或用户手动调用。

CC 端在 SessionEnd 自动触发, Codex 端依赖 Stop hook 在 sprint 完成时附带提醒 (delivery-gate review→ship 通过时已带 lessons.md soft warn)。

#### C4: async:true (Codex 不支持)

Codex hooks 全是同步执行。CC 端的 async 优化在 Codex 端不可移植, 但因为 lesson-drafter / lesson-archiver 都是文件 IO 不慢, 实测影响 < 100ms, 可接受。

### D 类: 吸收 claude-mem 思想

#### D1: sprint-N-summary.md (compound skill 双输出)

与 CC 端完全对位:
- `templates/sprint-N-summary.md` (5-8 行严格上限)
- `compound/SKILL.md` 双输出 + 自核对 (重复 / 长度 / 空内容 / 引用)
- R₀ 只读最近 2 个 summary

---

## 按需加载策略 (与 CC 一致)

| 文件 | 何时加载 | 加载方式 |
|------|---------|---------|
| AGENTS.md (含 4 元素口诀 + 9 铁律) | session 启动 | Codex 自动加载 |
| skills/pace/SKILL.md | 用户提到 PACE | skill 触发 |
| skills/pace/context-essentials.md | session-start.py 注入 | 主动注入 |
| prompts/from-zero.md | scenario=from-zero | PACE 内部 include |
| prompts/change-existing.md | scenario=modify-existing | PACE 内部 include |
| templates/change-plan.md | impl 需要时 | Read 加载 |
| templates/sprint-N-summary.md | compound 触发 | Read 加载 |
| 旧 sprint-summary (N-2 之前) | **永不自动加载** | 用户主动查 |

---

## 文件变化

### 新增 (8, 与 CC 对位)

- `.codex/hooks/output-evidence-augmentor.py`
- `.codex/hooks/session-end-reminder.py` (作为独立脚本, 不绑定事件)
- `.codex/hooks/lesson-drafter-agent-mode.md` (Codex 不支持, 文档说明)
- `.codex/skills/pace/templates/change-plan.md`
- `.codex/skills/pace/templates/sprint-N-summary.md`
- `.codex/skills/pace/prompts/from-zero.md`
- `.codex/skills/pace/prompts/change-existing.md`

### 修改 (8)

- `.codex/AGENTS.md` (+4 元素口诀段)
- `.codex/skills/pace/SKILL.md` (+scenario + RLPPV)
- `.codex/skills/pace/context-essentials.md` (+sprint-summary R₀ + 4 元素自检)
- `.codex/skills/pace/templates/project.json` (+scenario 字段)
- `.codex/prompts/vibe-init.md` (+场景判定)
- `.codex/prompts/vibe-dev.md` (+scenario 分支 + sprint-summary R₀)
- `.codex/skills/compound/SKILL.md` (双输出 + 自核对)
- `.codex/hooks/delivery-gate.py` (状态机硬化)
- `.codex/hooks/user-prompt-submit.py` (spawn-truth 加阶段一致性)
- `.codex/config.toml` (+output-evidence-augmentor + version 9.5-codex)

### 未动

- 其他 hooks (_redact / lesson-drafter / subagent-retry / pre-bash-guard / session-start / lesson-archiver / permission-request)
- agents/evaluator/generator/reviewer 三个 AGENTS.md
- skills/lesson-curator / vibe-review / vibe-status / vibe-setup
- 其他 templates / lessons/INDEX.md / README.md

## 规模

| 维度 | v9.4.5-hotfix-codex | v9.5-codex |
|------|---------------------|-----------|
| 文件数 | 35 | 42 |
| 行数 | 2467 | ~3056 |
| Hook 事件 | 6 | 6 (Codex 平台限制) |

## 跨平台兼容

`.ai_state/` schema 完全兼容 CC 端 v9.5。同一项目可在两端切换。
新增 `scenario` 字段, CC 端写, Codex 端读, 无障碍。

## 与 CC 端的差异 (Codex 平台限制)

| 特性 | CC v9.5 | Codex v9.5 |
|------|---------|-----------|
| TaskCreated 事件 | ✓ task-created-advisor 软提醒 | ✗ user-prompt-submit 替代 |
| SessionEnd 事件 | ✓ session-end-reminder | ✗ 仅独立脚本 |
| type:"agent" hook | ✓ lesson-drafter 双轨 | ✗ Codex 不支持 |
| async:true hooks | ✓ 异步非阻塞 | ✗ 全同步 (实测影响 <100ms) |
| Stop hook 协议 | `{decision:"block",reason}` | `{continue:false,stopReason}` |
| updatedToolOutput | ✓ | ✓ |

**结论**: Codex 端覆盖 v9.5 的 80% 功能, 缺失部分 (TaskCreated/SessionEnd/agent hook) 用替代方案模拟。

## 部署

```bash
cp ~/.codex/config.toml ~/.codex/config.toml.bak
unzip vibecoding-hermes-v95-codex.zip -d ~/
chmod +x ~/.codex/hooks/*.py
# 重启 codex
codex
/vibe-status
```

## 设计哲学

> PACE 是 prompt + state + hook 三位一体的自循环引擎。
> Codex 平台 hook 系统受限, 用 prompt 注入 + Stop hook 状态机 弥补。
