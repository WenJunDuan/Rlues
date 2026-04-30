# VibeCoding Hermes Kernel v9.5 (Claude Code)

发布日期: 2026-04-29
基线: v9.4.5-hotfix (35 文件 2269 行)
性质: **工程化升级**, PACE 从"流程描述"进化到"prompt + state + hook 三位一体的自循环引擎"

## 核心定位

> v9.4.5: PACE 是 prompt 描述, 靠 agent 自觉
> v9.5: PACE 是状态机硬约束, agent 想偷懒越不过 hook 这一层

v9.5 不是新功能堆叠, 是**把 v9.4.5 的"建议"升级成"硬规矩"**。所有进化都为这一个主轴服务。

---

## 11 项进化 (按 4 类分组)

### A 类: 核心 PACE 工程化 (核心)

#### A1: delivery-gate 状态机硬化

旧版: 只在 review 阶段检查 (单点把关)
新版: **全 stage 出口条件硬检查** (plan → impl → review → ship 每个转换都查)

11 种检查规则:
- `file` — 文件存在
- `has-pending-task` — tasks.md 含待办
- `all-tasks-done` — tasks.md 全部 [x]
- `has-section` — design.md 含指定段落 (例如 ## File Structure Plan)
- `has-progress` — progress.md 有本 sprint 记录
- `tasks-have-boundary` — tasks.md 含 _Boundary:_ 标注 (cc-sdd 边界优先)
- `review-report` — reviews/sprint-N.md 存在
- `review-has-test` — 审查报告含测试通过证据
- `review-has-external` — Feature+ 审查报告含外部审查 (codex/reviewer)
- `verdict-ok` — VERDICT 是 PASS/CONCERNS
- `scenario-conditional` — modify-existing 场景额外检查 change-plan.md

不满足出口条件 → `{decision:"block", reason:<具体修复指令>}` 让 agent 用 reason 作为新 prompt 继续, 不放过。

#### A2: change-plan.md 强制 deliverable

新增 `templates/change-plan.md` 模板, 7 字段格式 (图 06 工程化吸收):
1. 相关文件列表
2. 当前实现逻辑
3. 这个需求会影响哪些模块/页面/接口
4. 推荐修改方案
5. 不建议修改的文件
6. 可能风险
7. 验证方式

`scenario="modify-existing"` 场景下, plan→impl 转换前 **delivery-gate 硬检查 change-plan.md 必须存在**, 不存在直接阻断。

#### A3: TaskCreated 软提示 hook

利用 CC v2.1.84+ 的 TaskCreated 事件, 检测 `stage` 与 `task_subject` 是否一致:
- stage="plan" + subject 含 "implement/write code/build" → 软提醒
- stage="impl" + subject 含 "design/architect" → 软提醒
- stage="review" + subject 含 "implement/fix" → 软提醒

**只 systemMessage 不阻断**, 避免死锁 (subagent 创建 reviewer 类 task 是合理的)。

### B 类: 吸收图的工程化思维

#### B1: prompts/from-zero.md (吸收图 04)

从 0 项目按 Idea → Spec → Architecture → Tasks → Code 五步引导。
**不是独立 slash command**, 是 PACE skill 在 `scenario="from-zero"` 下 include 的内部模板 (按需加载)。

#### B2: prompts/change-existing.md (吸收图 05/06)

改已有项目按 Read → Locate → Plan → Patch → Verify 五步 (RLPPV)。
PACE skill 在 `scenario="modify-existing"` 下 include。强制输出 change-plan.md。

#### B3: 4 元素口诀 (吸收图 07)

CLAUDE.md 顶部加一段, 作为 9 条铁律的"压缩索引":

```
上下文 + 目标 + 约束 + 验证 = 稳定的 AI Coding
```

四个元素都齐 → 干。任何一个空 → 先补再干。

#### B4: PACE SKILL.md 加 scenario + RLPPV

- scenario 字段说明 (from-zero / modify-existing)
- 场景驱动的工作流差异 (modify-existing 必须 change-plan.md)
- RLPPV 五步显式命名 (改已有项目专用)
- project.json 模板加 `scenario` 字段
- vibe-init 加场景启发式判定 (有 build 文件 + src/ + git history → modify-existing)

### C 类: 平台特效正确使用

#### C1: PostToolUse:updatedToolOutput — review 阶段证据增强

用 CC v2.1.117+ 的 `hookSpecificOutput.updatedToolOutput` (4 月 stable 后扩展到所有 tools, 不再仅 MCP):

`output-evidence-augmentor.cjs/.py`:
- 自维护 `~/.claude/state/recent-tool-uses.jsonl` (ring buffer, 50 条上限)
- 每次 PostToolUse 写一条简短记录 (tool 名 / has_error / is_subagent_tool)
- **仅 review 阶段 + Edit/Write 类工具 + 路径 ∈ {Feature, Refactor, System}** 时检查 ring buffer 是否含 reviewer 调用证据
- 没证据 → `updatedToolOutput` 在原 tool 输出后追加 `💡 Hermes 提示` 行 (不阻断)

设计修正: 不读 transcript JSONL (太重), 自维护 ring buffer 比 transcript 解析快 100 倍。

#### C2: lesson-drafter 双轨 (cjs 默认 / agent 可选)

利用 CC v2.1.116+ 的 `type: "agent"` hook (hook 本身可以是多轮 LLM):
- 默认: cjs 版本 (零成本零延迟, 正则识别失败模式)
- 可选: 替换 settings.json 注册为 `type: "agent"` + claude-haiku-4-5, 智能识别新颖错误

切换说明见 `~/.claude/hooks/lesson-drafter-agent-mode.md`。

#### C3: SessionEnd 提醒 hook

利用 CC v2.1.116+ 的 SessionEnd 事件:
- 用户 `/clear` 或退出 session 时检查 tasks.md 完成数 + git 未提交修改
- 都满足 → systemMessage 提醒下次 session commit

不阻断, 仅信息层面。

#### C4: async:true 应用到非阻断 hook

利用 CC 的 `async: true` 标记:
- `lesson-drafter.cjs` (起草是 fire-and-forget, 不阻塞主线)
- `session-end-reminder.cjs` (退出时记账, 不耽误退出)

延迟敏感的 hook 仍同步 (delivery-gate 不能 async, 否则 Claude 已经停了 hook 才返回)。

### D 类: 吸收 claude-mem 思想

#### D1: sprint-N-summary.md (compound skill 双输出)

claude-mem (13.1k stars) 用 LLM 压缩 session 全过程。我们用 sprint 边界天然分块, 不需要 LLM 压缩:

| 文件 | 内容 | 长度 | R₀ 加载 |
|------|------|------|--------|
| `lessons.md` | Pattern/Pitfall/Constraint 结构化 | append-only, 0-N 条/sprint | 全文最近 10 条 |
| `sprint-N-summary.md` | 叙事化故事 (做了/决定了/遗留) | **严格 5-8 行** | 最近 2 个 |

compound skill 升级:
- 双输出 (lessons.md + sprint-N-summary.md)
- 自核对: 重复检查 (≥80% 相似就改写) / 长度检查 (>10 行截断) / 空内容跳过 / 引用检查 (必须含文件路径或行号)

R₀ 阶段下次 sprint 只读最近 2 个 summary, 旧的不自动加载 (按需查阅, 不膨胀 context)。

---

## 按需加载策略 (核心洞察)

> 文件数量增加 ≠ context 加载增加

| 文件 | 何时加载 | 加载方式 |
|------|---------|---------|
| CLAUDE.md (含 4 元素口诀 + 9 铁律) | session 启动 | CC 自动加载 |
| skills/pace/SKILL.md | 用户提到 PACE/vibe-dev | skill 触发 |
| skills/pace/context-essentials.md | SessionStart hook | 主动注入 |
| **prompts/from-zero.md** | scenario=from-zero 时 | PACE 内部 include |
| **prompts/change-existing.md** | scenario=modify-existing 时 | PACE 内部 include |
| templates/change-plan.md | impl 阶段需要写时 | Read 加载 |
| **templates/sprint-N-summary.md** | compound 触发时 | Read 加载 |
| 旧 sprint-N-summary (N-2 之前) | **永不自动加载** | 用户主动查 |
| ~/.claude/lessons/INDEX.md | R₀ 阶段 | SessionStart 注入摘要 |
| ~/.claude/lessons/{date}-{slug}.md | INDEX 命中主题时 | 按需 Read |

**结果**: v9.5 增加了 8 个文件, 但**单次 session 启动加载只多 ~200 chars** (4 元素口诀那段)。规模在 disk 上, 不在 context 上。

---

## 文件变化

### 新增 (8)

- `.claude/hooks/output-evidence-augmentor.cjs` — C1
- `.claude/hooks/session-end-reminder.cjs` — C3
- `.claude/hooks/task-created-advisor.cjs` — A3
- `.claude/hooks/lesson-drafter-agent-mode.md` — C2 双轨说明
- `.claude/skills/pace/templates/change-plan.md` — A2
- `.claude/skills/pace/templates/sprint-N-summary.md` — D1
- `.claude/skills/pace/prompts/from-zero.md` — B1
- `.claude/skills/pace/prompts/change-existing.md` — B2

### 修改 (8)

- `.claude/CLAUDE.md` (+4 元素口诀段)
- `.claude/skills/pace/SKILL.md` (+scenario + RLPPV + 模板引用)
- `.claude/skills/pace/context-essentials.md` (+ sprint-summary R₀ 项 + 4 元素自检)
- `.claude/skills/pace/templates/project.json` (+scenario 字段)
- `.claude/skills/vibe-init/SKILL.md` (+场景判定)
- `.claude/skills/vibe-dev/SKILL.md` (+scenario 分支 + sprint-summary R₀)
- `.claude/skills/compound/SKILL.md` (双输出 + 自核对)
- `.claude/hooks/delivery-gate.cjs` (状态机硬化, 11 种 check)
- `.claude/settings.json` (+TaskCreated/SessionEnd hook + async 标记 + version 9.5)

### 未动 (避免改坏)

- 其他 hooks (lesson-drafter / subagent-retry / pre-bash-guard / session-start / pre-compact-save / post-compact-restore / lesson-archiver / permission-request / _redact)
- agents/evaluator.md / generator.md
- skills/lesson-curator/SKILL.md / vibe-review/SKILL.md / vibe-status/SKILL.md / vibe-setup/SKILL.md
- 其他 templates (design / handoff / lessons / progress / review-report / tasks / init.sh)
- lessons/INDEX.md / README.md

## 规模

| 维度 | v9.4.5-hotfix | v9.5 | 增量 |
|------|--------------|------|------|
| 文件数 | 35 | 43 | +8 |
| 行数 | 2269 | ~3030 | +761 |
| Hook 事件注册 | 7 | 9 (+TaskCreated +SessionEnd) | +2 |
| Hook 文件 | 9 cjs | 12 cjs + 1 md | +3 cjs +1 md |
| Session 启动 context 加载 | ~2400 chars | ~2600 chars | +200 (按需加载策略生效) |

## 测试

5 轮 review 全过:
1. 语法 + 协议正确性 ✓
2. 12 场景行为级端到端 ✓
3. 架构一致性 (两端对位) ✓
4. 死锁/冲突 + 链式状态转换 ✓
5. 完整性 + 文档关联 ✓

## 部署

```bash
# 备份现有
cp ~/.claude/settings.json ~/.claude/settings.json.bak

# 解压
unzip vibecoding-hermes-v95-claude-code.zip -d ~/

# 加权限
chmod +x ~/.claude/hooks/*.cjs

# 重启 Claude Code
# 验证
/vibe-status
```

## 跨平台

`.ai_state/` schema 与 Codex 端 v9.5 完全一致 (含新 `scenario` 字段)。同一项目可在两端切换。

## 不在本版范围 (v9.6+)

- 跨平台共享层 (F 类) — 你已说不做
- compound 提炼仍靠 LLM 主观 — 暂无替代方案
- 33 → 43 文件复杂度 — 通过按需加载缓解, 但 disk 上仍是事实
- agent hook 用在 delivery-gate — 自审认为是炫技, 不做

## 设计哲学

v9.5 一句话总结:

> PACE 是 prompt + state + hook 三位一体的自循环引擎: 
> prompt 描述意图, state 是单一真相, hook 是不可绕过的硬规则。
> agent 想偷懒越不过 hook 这一层。
