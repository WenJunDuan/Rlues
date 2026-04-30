# VibeCoding Hermes Kernel (Codex CLI 端) v9.5

> 给 Codex CLI 装一个工程纪律。

## 这是什么

Codex CLI 配置 + hooks + skills + subagents, 把工程化纪律装进 `~/.codex/`。

**v9.5 核心改动**: 与 CC 端 v9.5 同步, PACE 升级为状态机驱动引擎。Codex 平台特性受限部分, 用 prompt 注入 + Stop hook 硬检查模拟。

## v9.5 vs v9.4.5

| 维度 | v9.4.5-codex | v9.5-codex |
|------|--------------|------------|
| PACE 阶段转换 | prompt 描述 | **delivery-gate 硬检查 11 种条件** |
| 改已有项目 | 提示要先勘察 | **change-plan.md 强制 deliverable** |
| spawn_agent 检查 | 弱提醒 | **user-prompt-submit 强化阶段一致性** |
| review 阶段证据 | 文字要求 | **PostToolUse updatedToolOutput 改写** |
| sprint 间记忆 | lessons.md | **+ sprint-N-summary.md 双输出** |
| 4 元素口诀 | 无 | **AGENTS.md 顶部** |
| 场景识别 | 隐式 | **scenario 字段** |

## Quick Start (3 分钟)

```bash
# 0. 检查 Codex ≥ v0.124.0
codex --version

# 1. 备份
cp ~/.codex/config.toml ~/.codex/config.toml.bak

# 2. 解压
unzip vibecoding-hermes-v95-codex.zip -d ~/

# 3. 加权限
chmod +x ~/.codex/hooks/*.py

# 4. 重启 codex
codex

# 5. 项目里:
/vibe-init                # 自动判定 scenario
/vibe-dev "我要做的事"     # 主入口
```

## 必选 vs 可选

| 项 | 必需 | 说明 |
|---|------|------|
| `~/.codex/AGENTS.md` | ✅ | 4 元素口诀 + 9 铁律 + 调度协议 |
| `~/.codex/skills/pace/` | ✅ | PACE 路由器 (内含 prompts/ + templates/) |
| `~/.codex/hooks/*.py` | ✅ | 11 个 Python hook |
| `~/.codex/config.toml` | ✅ | hooks 注册 + 模型 + version 9.5-codex |
| `~/.codex/agents/{evaluator,generator,reviewer}/AGENTS.md` | ✅ | 3 个 subagent 角色 |

## ChatGPT 订阅 vs API key 用户

- **ChatGPT 订阅** (Plus/Pro/Business): 默认 `gpt-5.5` 直接可用
- **API key**: GPT-5.5 未上 API → `codex --profile api` (走 gpt-5.4)

## v9.5 工作流示意

### 场景 1: 从 0 项目

```
/vibe-init   → 检测无代码 → from-zero
/vibe-dev "做个聊天 bot"
  → PACE Feature
  → stage=plan: include prompts/from-zero.md (图 04 五步)
  → 用户确认 design + tasks
  → delivery-gate 通过 → stage=impl
  → spawn_agent generator (并行实现)
  → stage=review: spawn_agent reviewer + /review 内置
  → delivery-gate 验 verdict → ship
  → compound 双输出
```

### 场景 2: 改已有项目

```
/vibe-init   → 检测有代码 → modify-existing
/vibe-dev "加 OAuth2"
  → PACE Feature
  → stage=plan: include prompts/change-existing.md (RLPPV)
  → Read → Locate → Plan (写 change-plan.md)
  → ⚠ 用户确认
  → delivery-gate 检查 change-plan.md 必存在 → 通过
  → stage=impl: spawn_agent generator (small batch)
  → 每 task 完成 → tasks.md 勾选 + progress.md 追加
  → stage=review: spawn_agent reviewer
  → delivery-gate verdict=PASS → ship
  → compound
```

## hooks 全景 (Codex 6 事件)

| Hook | 行为 |
|------|------|
| SessionStart (startup\|resume\|clear) | 注入铁律 + project state + 4 元素自检 |
| **UserPromptSubmit** (Codex 独有) | 关键词驱动注入 (R₀ / 铁律 8 / spawn-truth + 阶段一致性) |
| PreToolUse:Bash | 拦截危险命令 |
| PostToolUse | subagent-retry + lesson-drafter + output-evidence-augmentor |
| Stop | **delivery-gate 状态机** (11 种 check) |
| PermissionRequest | systemMessage (Codex 协议受限) |

## 与 CC 端的差异

| 特性 | CC | Codex |
|------|----|----|
| TaskCreated 事件 | ✓ | ✗ → user-prompt-submit 替代 |
| SessionEnd 事件 | ✓ | ✗ → 仅独立脚本 |
| type:"agent" hook | ✓ (lesson-drafter 双轨) | ✗ |
| async:true | ✓ | ✗ (全同步, 实测 <100ms) |
| Stop hook 协议 | `{decision:"block"}` | `{continue:false,stopReason}` |

**结论**: Codex 端覆盖 v9.5 的 80% 功能, 不可对位的部分用替代方案。

## 跨平台

`.ai_state/` schema 与 CC 端完全一致, scenario 字段两端共享。

## 出问题

1. `/vibe-status`
2. `.ai_state/hook-trace.jsonl`
3. `~/.codex/lessons/draft-*.md`
4. `RELEASE-NOTES.md` 完整说明

## 设计哲学

> PACE 是 prompt + state + hook 三位一体的自循环引擎。Codex 平台 hook 受限, 用 prompt 注入 + Stop hook 状态机 弥补。
