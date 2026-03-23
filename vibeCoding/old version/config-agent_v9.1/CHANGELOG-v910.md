# VibeCoding Kernel v9.1.0 — CHANGELOG

> 基于全网热门提示词仓库调研 + CC v2.1.70 / Codex 0.108+ 官方文档交叉验证

## 调研来源
- NeoLabHQ/context-engineering-kit (SDD, LLM-as-Judge)
- obra/superpowers (TDD 强制, subagent-driven-development)
- github/spec-kit (官方 SDD 工具链)
- trailofbits/claude-code-config (安全加固, prompt hooks)
- gotalab/cc-sdd (Kiro 式 spec 工作流)
- NeoLabHQ/kaizen (持续改进循环)

---

## 新增 (v9.0.8 → v9.1.0)

### 🧠 质量门升级

**CC: LLM-as-Judge 交付审查**
- Stop hook 新增 prompt hook: 让 LLM 审查代码质量、测试覆盖、commit 规范、密钥泄露
- 与原有 delivery-gate command hook 双层检查 (机械+语义)
- 来源: NeoLabHQ SDD + trailofbits prompt hook 模式

**CC: TDD 强制检查 hook**
- PostToolUse 新增 prompt hook: 写源码时检查是否有对应测试
- 违规时 LLM 提醒 "先写测试再写实现"
- 来源: obra/superpowers 的 "删代码" 理念, 降级为 "提醒"

**Codex: TDD 强制规则 (AGENTS.md 指令)**
- 铁律新增 "先测后码", E 阶段强制 RED→GREEN→REFACTOR
- Codex 无 hooks, 用规则指令实现同等效果

### 📋 Spec 驱动的需求阶段

**两端 brainstorm skill 增加 Spec 模板输出**
- R₀b 阶段输出结构化需求: MUST/SHOULD/COULD + 验收标准
- 对齐 SDD 社区共识, 但不引入外部工具链
- 来源: github/spec-kit + NeoLabHQ/sdd

### 🔄 Kaizen 持续改进

**两端新增 kaizen skill (V 阶段自动触发)**
- 交付后: git diff→提炼经验→knowledge.md + lessons.md
- 铁律新增 "交付必复盘"
- 来源: NeoLabHQ/kaizen 理念

### ⚡ Skills 自动触发机制

**workflows/ 重写: 每个 RIPER 阶段标注必须加载的 skills**
- 不再靠 agent "按需读取", 而是阶段转换时自动注入
- CC: R₀b→brainstorm, R/D→context7, P→plan-first, E→tdd, T→verification+code-review, V→kaizen
- Codex: 同上, 额外集成 /plan /review 原生命令
- 来源: obra/superpowers 的 "mandatory workflows, not suggestions"

### 🔧 Codex 原生能力集成

**Profiles — 三预设配置**
- `dev`: gpt-5.4 + high reasoning + on-request
- `ci`: gpt-5.3-codex + medium + never (全自动)
- `review`: gpt-5.4 + xhigh + read-only (只读审查)

**exec_policy 启用**
- 替代手写 pre-bash 安全逻辑, 使用 Codex 原生命令级权限

**模型升级: gpt-5.4**
- 最新最强模型, 支持降级到 gpt-5.3-codex

**Agent 角色引用 config_file**
- builder/reviewer/explorer 现在引用 .codex/agents/*.toml

### 📐 CC 原生能力利用提示

**CLAUDE.md 提及 /fork**
- Path B+ brainstorm 可用 /fork 并行探索方案
- workflows/pace.md 标注此能力

---

## 平台差异矩阵 (v9.1.0)

| 能力 | Claude Code | Codex CLI |
|------|------------|-----------|
| 质量门 | Stop prompt hook (LLM-as-Judge) | AGENTS.md 规则 + /review |
| TDD 强制 | PostToolUse prompt hook | AGENTS.md 铁律指令 |
| 安全控制 | PreToolUse hook + deny rules | exec_policy + sandbox |
| 多代理 | agents/ + Task() + background | [agents] + multi_agent |
| 配置预设 | 无 (单配置) | profiles (dev/ci/review) |
| 持久化 | .ai_state/ + /memory | .ai_state/ + memories |
| 分发 | .claude-plugin + marketplace | config.toml + skills/ |
| 方案对比 | /fork | 无 |
| 周期监控 | /loop | 无 |
| 原生规划 | 无 (/plan 非官方) | /plan |
| 原生审查 | 无 (/review 非官方) | /review |

## 文件统计

| 包 | 文件数 | 新增 | 修改 |
|----|--------|------|------|
| Claude Code | 40 | +1 (kaizen) | ~12 |
| Codex CLI | 27 | +1 (kaizen) | ~10 |
