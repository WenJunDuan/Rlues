# VibeCoding Hermes Kernel (Claude Code 端) v9.5

> 给 Claude Code 装一个工程纪律。让它不偷懒、不伪装、不替你出馊主意。

## 这是什么

Claude Code 配置 + hooks + skills, 把工程化纪律装进 `~/.claude/`。

**v9.5 核心改动**: PACE 从"流程描述"升级为"状态机驱动的自循环引擎"——通过 hook 强制 agent 按规矩工作, 不能偷懒越过状态机。

## v9.5 vs v9.4.5

| 维度            | v9.4.5              | v9.5                                                   |
| --------------- | ------------------- | ------------------------------------------------------ |
| PACE 阶段转换   | prompt 描述, 靠自觉 | **delivery-gate 硬检查 11 种条件**                     |
| 改已有项目      | 提示要先勘察        | **change-plan.md 强制 deliverable**                    |
| 任务创建检查    | 无                  | **TaskCreated hook 软提醒**                            |
| review 阶段证据 | 文字要求            | **PostToolUse 改写输出补提示**                         |
| sprint 间记忆   | lessons.md          | **+ sprint-N-summary.md 叙事化双输出**                 |
| 4 元素口诀      | 无                  | **CLAUDE.md 顶部** (上下文+目标+约束+验证)             |
| 场景识别        | 隐式                | **scenario 字段** (from-zero / modify-existing)        |
| 平台特性        | v9.4.5              | **+TaskCreated +SessionEnd +updatedToolOutput +async** |

## Quick Start (3 分钟)

```bash
# 1. 备份
cp ~/.claude/settings.json ~/.claude/settings.json.bak 2>/dev/null

# 2. 解压
unzip vibecoding-hermes-v95-claude-code.zip -d ~/

# 3. 加 hook 执行权限
chmod +x ~/.claude/hooks/*.cjs

# 4. 重启 Claude Code (hooks 启动时 snapshot, 必须重启)

# 5. 进入 CC, 项目里跑:
/vibe-init       # 项目初始化, 自动判定 scenario
/vibe-dev "我要做的事"    # 开发主入口
```

## 必选 vs 可选

| 项                        | 必需 | 说明                                     |
| ------------------------- | ---- | ---------------------------------------- |
| `~/.claude/CLAUDE.md`     | ✅   | 4 元素口诀 + 9 条铁律 + 调度协议         |
| `~/.claude/skills/pace/`  | ✅   | PACE 路由器 (内含 prompts/ + templates/) |
| `~/.claude/hooks/*.cjs`   | ✅   | 12 个 hook 脚本                          |
| `~/.claude/settings.json` | ✅   | hooks 注册 + 权限 + version 9.5          |
| `~/.claude/lessons/`      | ⚠️   | 全局工具链经验库                         |

## 核心命令

| 命令               | 用途                       |
| ------------------ | -------------------------- |
| `/vibe-setup`      | 全局安装向导               |
| `/vibe-init`       | 项目初始化 + scenario 判定 |
| `/vibe-dev <需求>` | **主入口**                 |
| `/vibe-review`     | 单独跑审查                 |
| `/vibe-status`     | 状态面板                   |
| `/lesson-curator`  | 整理 draft 落档            |

## v9.5 工作流示意

### 场景 1: 从 0 项目 (scenario=from-zero, 图 04 五步)

```
/vibe-init     → 自动检测 from-zero
/vibe-dev "做个 todo app"
  → PACE 路由 Feature 路径
  → stage=plan: include prompts/from-zero.md
  → 用户回答 Idea/Spec/Architecture/Tasks/Code 5 步
  → design.md + tasks.md (含 Boundary/Depends)
  → delivery-gate 检查通过 → stage=impl
  → TDD 实现
  → stage=review: spawn /codex:review (Feature+ 必须)
  → delivery-gate 检查 verdict=PASS → ship
  → /compound 双输出 lessons + sprint-N-summary
```

### 场景 2: 改已有项目 (scenario=modify-existing, 图 06 RLPPV)

```
/vibe-init     → 检测有 src/ + package.json + .git → modify-existing
/vibe-dev "加邮箱登录"
  → PACE 路由 Feature 路径
  → stage=plan: include prompts/change-existing.md
  → Read (项目结构) → Locate (影响范围) → Plan (写 change-plan.md 7 字段)
  → ⚠ 用户确认 change-plan.md
  → delivery-gate: 无 change-plan.md → block, 提示先写
  → 写完 → 通过 → stage=impl
  → Patch 小步修改 + Verify 即时验证
  → stage=review (review 阶段 Edit 没 reviewer 调用 → output-evidence-augmentor 注入提示)
  → 跑 /codex:review → 写 reviews/sprint-N.md (含 VERDICT: PASS)
  → ship
  → /compound
```

## 关键 Hook 行为

| Hook                     | 时机                  | 行为                                                                |
| ------------------------ | --------------------- | ------------------------------------------------------------------- |
| SessionStart             | 启动 / resume / clear | 注入铁律 + project state + 4 元素自检                               |
| PreToolUse:Bash          | rm/git push/curl/wget | 拦截危险命令                                                        |
| TaskCreated (新)         | spawn Task            | stage 与 subject 不一致 → 软提醒 (不阻断)                           |
| PostToolUse              | 任意 tool 后          | subagent-retry + lesson-drafter (async) + output-evidence-augmentor |
| Stop (核心)              | agent 想停            | **delivery-gate 状态机硬检查 11 种规则**                            |
| PreCompact / PostCompact | 压缩前后              | 保存/恢复 .ai_state                                                 |
| SessionEnd (新)          | clear / quit          | 提醒未提交修改 (async)                                              |
| PermissionRequest        | 工具批准时            | behavior=ask + 写脱敏 hook-trace                                    |

## 安全提示 (v9.4.5-hotfix 已做, v9.5 保留)

- lesson-drafter / hook-trace 写盘前 redact (token/secret/JWT/SSH 全脱敏)
- 9 类敏感数据正则覆盖 (Authorization / api_key / sk-/sk-ant- / GitHub token / AWS / JWT / SSH 等)
- 未误命中 `"username": "alice"` 等正常字段 (false-positive 测试通过)

## 跨平台

`.ai_state/` schema 与 Codex 端 v9.5 完全一致 (含新 scenario 字段)。同项目两端切换无障碍。

## 出问题怎么办

1. `/vibe-status` 看健康面板
2. `.ai_state/hook-trace.jsonl` 看最近 hook 触发
3. `~/.claude/lessons/draft-*.md` 看自动起草问题
4. 完整说明: `RELEASE-NOTES.md`

## 设计哲学

> PACE 是 prompt + state + hook 三位一体的自循环引擎:
> prompt 描述意图, state 是单一真相, hook 是不可绕过的硬规则。
> agent 想偷懒越不过 hook 这一层。
