---
title: "Athena 9.9.3 current-state audit for 9.9.6"
created: "2026-07-25"
baseline_commit: "7d92a21"
status: "complete"
---

# 9.9.3 现状审计

## 审计边界

只审计当前不可变发行源：

- `vibeCoding/claude/9.9.3/.claude`
- `vibeCoding/codex/9.9.3/.codex`
- `.ai_state/_index.md`
- `vibeCoding/scripts/*9.9.3*`

没有修改 9.9.3 包、用户 HOME 配置或主工作树。

## 可复核基线

| 面 | Claude Code | Codex |
|---|---:|---:|
| 根提示词 | 21 行 / 2874 bytes | 23 行 / 3468 bytes |
| settings/config | 347 行 | 191 行 |
| skills | 26 / 2542 SKILL.md 行 | 26 / 2439 SKILL.md 行 |
| skill frontmatter 总量 | 约 8647 bytes | 约 8860 bytes |
| custom agents | 7 | 9 |
| hooks | 17 files / 3326 行 | 11 files / 3046 行 |
| runtime tests | 107/107 历史基线 | 67/67 历史基线 |
| release validator | colspan: 223/223 历史基线（exact Codex 0.144.1） |

Codex 官方在上下文窗口未知时给初始 skill 列表 8000 chars 预算；当前 8860-byte frontmatter 已没有安全余量，且最长 description 集中在 `quantum-data`、`pace`、`quantum-codegen`、`brainstorm`、`antigravity`。

## P0：配置会改变或破坏预期行为

### A1 · Claude 角色模型被全局覆盖

`settings.json` 同时存在：

- agent frontmatter 的 `model: fable|opus|sonnet`
- `CLAUDE_CODE_SUBAGENT_MODEL=claude-sonnet-5`

官方 precedence 表明后者覆盖调用参数和 frontmatter。结果是 architect / critic / evaluator 的高价值模型配置只存在于文本，运行时会统一落到 Sonnet 5。

修复合同：9.9.6 删除全局 override，并为每个 agent 做可执行 model-resolution 检查。

### A2 · Claude Opus alias 被固定在 4.8

`ANTHROPIC_DEFAULT_OPUS_MODEL=claude-opus-4-8` 会阻止 `opus` alias 自动升级到 2.1.219 的 Opus 5。Fable/Sonnet pin 也会形成下一次同类漂移。

修复合同：一方 API 基线只用 alias；provider/gateway pin 进入用户自有配置或显式 profile。

### A3 · Claude 请求超时被缩短 20 倍

当前 `API_TIMEOUT_MS=30000`，官方默认 `600000`。长生成、subagent 或重试可能被本包提前杀死。

修复合同：删除 package override；只有真实慢代理场景才由用户升高，不在通用包降低。

### A4 · Codex 9.9.1 修复在 9.9.3 回归

9.9.3 `CHANGELOG.md` 自己记载 9.9.1 已完成：

- 使用 built-in `openai` provider；
- 删除空 `custom_openai`；
- 删除伪造的 1M / 900k 上下文设置。

但当前 9.9.3 `config.toml` 又包含这三项。它们属于发布间漂移，不是新设计选择。

修复合同：validator 新增“已关闭 regression 不得复活”的负向 fixture。

## P1：平台默认与包内重复

### B1 · Codex stable features 重复开启

以下当前均是 Stable default-on：

- goals
- hooks
- multi_agent
- personality
- shell_snapshot
- shell_tool
- unified_exec（Windows 除外）

重复配置增加版本漂移和 warning 面积，却不提供 Athena 语义。9.9.6 只配置偏离默认的产品决策。

### B2 · Codex skills 被当作注册表

26 个 `[[skills.config]] enabled=true` 没有注册价值；Codex 会自动发现 `~/.agents/skills`。该表的正式用途是禁用/重启某个已发现 skill。

影响：配置多 100+ 行，并把安装路径硬编码成 `<USER_HOME>` 模板替换合同。

### B3 · Codex experimental memory 与 `.ai_state` 重叠

当前显式开启 Experimental memories 并隐藏 unstable warning。官方定义它为跨聊天召回，而不是规则或权威状态。

修复合同：默认关闭/省略 Codex memories；host memory 可辅助召回，但任何 gate 与交付结论只读 `.ai_state`。

### B4 · Claude 默认能力被重复配置

- `ENABLE_TOOL_SEARCH=1`：一方连接 unset 已默认开启。
- `DISABLE_INSTALLATION_CHECKS=1`：会遮蔽安装告警。
- `CLAUDE_CODE_ATTRIBUTION_HEADER=0`：只对 gateway cache 有价值。
- `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1`：是用户隐私/更新策略，不应由 release-owned 模板替用户决定。

### B5 · 机器/用户态偏好混入发行模板

Codex 包包含 WSL acknowledgement 与 desktop UI preferences。迁移应保留已存在用户值，但新发行包不应注入这些个人偏好。

## P1：提示词与 skill 架构

### C1 · 根提示词已经短，但语义仍多处重复

根提示词本身只有 21/23 行，不应为追求行数盲目再压缩。问题在于相同概念还同时存在于：

- `pace/SKILL.md`
- `pace/references/stages.md`
- agent developer instructions
- hook block messages
- `_index` 的“工具调度建议”

对 PACE 根提示词、pace 与 agents 做关键词抽样，TDD/worktree/stage/VERDICT/主线程边界等命中 442 次。9.9.6 的目标是单一权威出处和行为测试，不是电报体竞赛。

### C2 · 双端 26 skills 只有 6 个字节完全一致

完全一致：

- `athena-migrate`
- `athena-setup`
- `biz-delivery-loop`
- `deps-check`
- `quantum-codegen`
- `quantum-data`

其余 skill 含真实平台差异，也含称谓/路径/工具名的机械差异。直接强求文件相同会伪造平台对称；完全手工维护又会继续漂移。

修复合同：共享“语义 contract + trigger catalog”，端内保留真实 adapter；validator 验语义标记、触发器、stage 和 role parity。

### C3 · skill description 超预算且写了流程摘要

当前 description 不只是“何时用”，还包含版本历史、流程结论和实现细节。Superpowers 的行为测试记录了 description 会抢先支配正文；Codex 又会在 8000 chars 后截短或省略技能。

修复合同：

- description 仅含 trigger、对象和非目标；
- 目标总量 ≤ 6500 chars，给第三方 skills 留余量；
- maintenance/side-effect skills 禁止隐式调用；
- workflow 细节只在 SKILL.md / references。

### C4 · agent 提示词重复平台已提供的能力

部分 agent 文本反复强调只读、不能 spawn、模型 effort、返回格式；其中“只读/不能写/不能 spawn”能由 sandbox/tool policy 机械保证，模型与 effort 又有 frontmatter。

修复合同：frontmatter 承载 capability，正文只保留职责、输入、输出 schema 与判断标准。

## P1：PACE 与 `.ai_state`

### D1 · `_index` 不再是小型索引

当前 `_index.md` 为 165 行 / 9882 bytes，正文包含完整 stage 工具调度教程、十余条发布历史和空 stage 的 hook 历史。它同时承担：

- 当前状态；
- capability probe；
- routing history；
- workflow documentation；
- release diary。

这与“有界检索路由器”的自身说明冲突。

### D2 · capability snapshot 没有时效

`cc_version` 仍是 unknown，`cx_version` 固定 0.144.1；platform/tool features 没有 `detected_at`。外部能力会变化，却被写在权威索引中长期保留。

修复合同：将易变探测移到带时间戳的 `runtime-capabilities.yaml`，`_index` 只保留一个 pointer/摘要；init/status/router 是明确消费者。

### D3 · 低价值重复字段已表现出陈旧

`last_subagent=generator` 和时间仍停在 2026-07-10，机器账本另有 JSONL；`last_critic_round=2` 也属于前一 sprint。9.9.2 审计已把这些标为低价值但因风险保留，现在可用迁移 + consumer tests 安全移除或改为 sprint-scoped。

### D4 · route/history 格式已出现噪声

- `route_history` 是一条很长的 inline YAML list；
- body history 含空 stage/sprint 行；
- current status 超出恢复需要的最近 10 条语义。

修复合同：frontmatter 只保留最近 3 条 route 摘要；详细依据在每个 sprint 的 `route-note.md`；无效 hook 行不落盘。

### D5 · PACE stage 暂不应重命名

4 core + 5 conditional 已被 hooks、gates、templates、tests 和历史状态广泛消费。9.9.6 应先做来源收敛和 context budget；在没有路径使用数据前，不做 stage 合并或大规模重命名。

## P2：验证体系缺口

现有 validator 擅长语法、fixture、安装和 gate 行为，但没有把“提示词是否更好”作为可回归合同：

- 没有 9.9.3 vs 9.9.6 的相同任务 A/B；
- 没有误提问率、误路由率、隐式 skill 触发率；
- 没有角色 model resolution 断言；
- 没有 skill catalog 总预算；
- 没有已删除配置复活的 denylist；
- 没有 compaction 后恢复正确性场景。

9.9.6 必须先建立 prompt/skill eval baseline，再做大面积删减。

## 保留项

下列设计经审计仍有真实消费者或防御价值，本轮不因“减重”删除：

- PACE 4 core + 5 conditional stage 语义；
- fail-closed delivery/spec gates；
- per-AC evidence、review manifest 与 unknown≠success；
- worktree 红区隔离和主线程文件所有权；
- 2+1 review 结构；
- `.ai_state` 作为唯一交付权威；
- quantum 7→2 合并结果；
- canonical `~/.agents/skills` 安装路径；
- CC/CX 不伪造对称 hook/wire 机制。

## 本次审计命令

```bash
wc -l vibeCoding/claude/9.9.3/.claude/CLAUDE.md \
  vibeCoding/codex/9.9.3/.codex/AGENTS.md \
  .ai_state/_index.md
find vibeCoding/claude/9.9.3/.claude/skills -name SKILL.md | wc -l
find vibeCoding/codex/9.9.3/.codex/skills -name SKILL.md | wc -l
find vibeCoding/claude/9.9.3/.claude/hooks -type f -exec wc -l {} +
find vibeCoding/codex/9.9.3/.codex/hooks -type f -exec wc -l {} +
rg -l '9\.9\.3|0\.144\.1|2\.1\.203|opus-4-8|gpt-5\.6-sol' \
  vibeCoding/claude/9.9.3 vibeCoding/codex/9.9.3
```
