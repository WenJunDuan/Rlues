# VibeCoding Hermes Kernel v9.5 (Codex)

发布日期: 2026-05-09
基线: v9.4.5-codex
平台版本要求: Codex CLI ≥ v0.124.0（codex_hooks stable 起点；建议 ≥ v0.119 以用上插件市场）

## 哲学定位

v9.5 是 **架构级减重 + Codex 平台 3-4 月新能力接入** 版本。

v9.4.x 系列的全局 lessons 系统、过度的反 LLM 偏见自检、僵硬的硬约束在 Codex 端同样表现为干扰多于帮助。v9.5 拆掉这些，用更少的硬约束 + 更明确的正向证据要求 + just-in-time 上下文注入，让 agent 自然按工程纪律工作。

## 核心变更

### 减重（删除）

- `~/.codex/lessons/` 全局系统 + `lesson-drafter.py` + `lesson-archiver.py` + `lesson-curator.md` prompt
  - 知识管理不是 Hermes 职责。Codex 端推荐 superpowers
- `pre-bash-guard.py` 9 → 3 条灾难级（rm 根 / curl-pipe / mkfs-dd）
  - 其他靠 sandbox + approval_policy 兜底
- AGENTS.md `反 LLM 偏见` 段（6 条禁止）
  - 反复"禁止 X" 是 anti-pattern。改铁律 6（完成度证据）正向要求
- 铁律 9 → 7：合并 8/9 为铁律 6（完成度证据）+ 铁律 7（出处优先）

### 增量（新增）

- **AGENTS.md altitude 注释** — 明确这是 constitution（identity + iron rules + design principles）
- **just-in-time R₀** — 不预加载 tasks/lessons 内容，只注入计数；按需 read
- **subagent token 预算 ≤ 2000** — generator/evaluator/reviewer 全部加上（Anthropic 多 agent research 经验）
- **`[[skills.config]]` 段** — Codex 3/2026 新增的 per-skill 启用控制，默认开 pace + compound
- **PACE 节点插件推荐表** — pace/SKILL.md 列出 Codex 端 best-fit（superpowers / @plugin-creator）
- **跨平台优势提示** — pace/SKILL.md 提示 Codex Terminal-Bench +12pp，token 0.25-0.33×

### 修订

- 铁律 4 措辞 — `Review 强制（Feature+ 至少一次交叉审查）` 不变，但 evaluator 反伪装检查改引"铁律 4 + 铁律 6"
- 失败处理协议 — 移到 pace/SKILL.md，作为流程文档而非铁律条目
- subagent-retry 触发消息 — 350 → ~200 字符，引用铁律 6
- `vibe-setup` Step 4 — 新接入 Codex 插件市场（3/27/2026 上线，90+ 插件）

## Hook 清单（v9.4.5-codex → v9.5-codex）

| Hook | v9.4.5 | v9.5 | 备注 |
|------|--------|------|------|
| session-start | ✓ | ✓ (改) | 删 INDEX 注入 / just-in-time |
| pre-bash-guard | ✓ 9 条 | ✓ 3 条 | 仅灾难级 |
| subagent-retry | ✓ | ✓ (改) | 引铁律 6 |
| delivery-gate | ✓ | ✓ | 微调 |
| permission-request | ✓ | ✓ | 不变 |
| user-prompt-submit | ✓ | ✓ (改) | just-in-time R₀ / 删全局 lessons |
| ~~lesson-drafter~~ | ✓ | ✗ 删 | |
| ~~lesson-archiver~~ | ✓ | ✗ 删 | |

净 -2（8 → 6）。

## 跨平台对齐

`.ai_state/` schema 与 CC v9.5 完全一致：项目可以在 Codex / CC 之间切换不丢状态。
铁律编号、VERDICT 四档、failure 处理协议三轮、subagent token 预算 — 双端语义一致。

注：Codex 平台不支持的事件 — SessionEnd / TaskCreated / updatedToolOutput — 对应的 CC 端 hook（output-evidence-augmentor / session-end-reminder / task-created-advisor）无法在 Codex 端镜像。这是平台限制，不是 Hermes 设计取舍。

## 升级路径（从 v9.4.5-codex）

```bash
# 备份
mv ~/.codex ~/.codex.bak.v94

# 解压新版
unzip -d ~ vibecoding-hermes-v95-codex.zip

# 合并 config.toml (本地 customizations)
diff ~/.codex.bak.v94/config.toml ~/.codex/config.toml

# 全局 lessons 数据可保留参考
mv ~/.codex.bak.v94/lessons ~/legacy-codex-lessons/

# 验证
codex --version
grep "codex_hooks = true" ~/.codex/config.toml
ls ~/.codex/hooks/*.py | wc -l  # 6
```

## 致谢

设计灵感：
- [Anthropic — Effective context engineering for AI agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
- Codex 插件市场（3/27/2026 上线 90+ 插件）
- superpowers 跨 session 记忆方案
