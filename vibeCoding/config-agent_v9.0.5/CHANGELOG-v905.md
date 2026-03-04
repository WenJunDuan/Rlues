# VibeCoding Kernel v9.0.5 — CHANGELOG

## 版本概览
- 基线: v9.0.2
- 日期: 2026-03-04
- CC: 37 files / 868L
- Codex: 26 files / 619L
- Total: 63 files / ~1550L

## 平台同步 (已验证, 非幻觉)

### Claude Code 新特性集成 (2.1.49→2.1.63)

| 特性 | 集成方式 |
|:---|:---|
| Auto-memory (/memory) | CLAUDE.md 记录, 减轻手动 knowledge 维护 |
| background: true agent | builder.md 添加 background: true |
| ConfigChange hook event | settings.json 新增 ConfigChange hook |
| last_assistant_message | SubagentStop prompt hook 利用此字段 |
| agent model 别名 (sonnet) | 所有 5 个 agent 改为 model: sonnet |
| /simplify /batch /copy | 文档记录, 不重复造轮子 |
| /voice | 文档记录 (experimental) |
| BashTool skip login shell | 移除 CLAUDE_BASH_NO_LOGIN 配置 |
| HTTP hooks support | 文档记录, 保留 command type 兼容 |

### Codex CLI 新特性集成 (0.104→0.107)

| 特性 | 集成方式 |
|:---|:---|
| steer always on | 移除 steer=true 配置 (无需显式启用) |
| Sub-agent fork | AGENTS.md + agent-teams skill |
| spawn_agents_on_csv | agent-teams skill 说明 |
| /review | 集成进 T(测试) 阶段 |
| command_attribution | config.toml 启用 |
| GPT-5.3-Codex 默认 | config.toml model 更新 |
| Configurable memories | 文档记录 |
| Voice transcription | config.toml 注释记录 |

## 自审修复

| # | 类型 | 文件 | 问题 | 修复 |
|:---|:---|:---|:---|:---|
| F1 | BUG | pre-bash.cjs | rm -rf / 正则未匹配 (T4 失败) | 修复 `\s\/(\s\|$)` 正则 |
| F2 | BUG | codex agent-teams | 引用 CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS | 重写为 Codex collab/parallel 描述 |

## 精简优化

| 维度 | v9.0.2 | v9.0.5 | 变化 |
|:---|:---|:---|:---|
| CLAUDE.md | ~45L | 32L | -29% (移除 AI 已知信息) |
| Skill 平均行数 | ~30L | ~19L | -37% (只保留关键指令) |
| 总行数 | ~2625L | ~1550L | -41% (移除冗余) |
| CC 文件数 | 43 | 37 | -14% (合并精简) |
| Codex 文件数 | 30 | 26 | -13% |
| Hook 测试 | 9/9 | 11/11 | +2 新测试用例 |

## 数据流管道

```
用户输入
  │
  ├─ /vibe-init → 创建 .ai_state/ (从 templates)
  │
  ├─ /vibe-resume → context-loader.cjs 断点恢复
  │
  └─ /vibe-dev {需求}
       │
       ├─ .ai_state/ 不存在 → quickstart skill → /vibe-init
       │
       └─ P.A.C.E. 评估
            │
            ├─ Path A (≤30min)
            │   加载: CLAUDE.md + rules.md (~130L)
            │   R→E→T(轻)→V
            │   cunzhi [DELIVERY_CONFIRMED]
            │
            ├─ Path B (6-12h)
            │   加载: + workflows + 6 skills (~540L)
            │   R₀b(brainstorm)→R→D→P(plan-first)→E(tdd)→T(verification+review)→V
            │   cunzhi: [DESIGN_DIRECTION]→[DESIGN_READY]→[PLAN_CONFIRMED]→[DELIVERY_CONFIRMED]
            │
            └─ Path C/D (1-3周+)
                加载: + agent-teams + e2e-testing (~700L)
                同B + agent-teams并行(builder×N) + e2e + security
                cunzhi: + [TESTS_PASSED] + [SECURITY_PASSED]
```

## 组件清单

### MCP 工具 (3)
| MCP | CC | Codex | 用途 |
|:---|:---|:---|:---|
| augment-context-engine | ✓ | ✓ | 语义代码搜索 |
| cunzhi | ✓ | ✓ | 人工确认检查点 |
| mcp-deepwiki | ✓ | ✓ | 开源库文档 |

### Skills (9)
brainstorm / context7 / plan-first / tdd / verification / code-review / agent-teams / e2e-testing / quickstart

### Agents (5, CC only)
builder (background) / validator / explorer / e2e-runner / security-auditor

### Hooks
| Hook | Event | CC | Codex |
|:---|:---|:---|:---|
| context-loader.cjs | SessionStart | 自动 | 手动 |
| delivery-gate.cjs | Stop | 自动 | 手动 |
| post-edit.cjs | PostToolUse(Write) | 自动 | N/A |
| pre-bash.cjs | PreToolUse(Bash) | 自动 | 手动 |

### Commands (4, CC only)
/vibe-dev / /vibe-init / /vibe-resume / /vibe-status
