---
title: "Athena 9.9.6 prompt-engineering research"
created: "2026-07-25"
status: "research-complete"
scope: ["claude-code", "codex", "skills", "pace", "ai_state", "external-harnesses"]
implementation_authorized: false
---

# 9.9.6 调研底稿

## 结论先行

9.9.6 应定位为一次 **平台契约刷新 + 提示词控制面减重**，不是再叠一套工作流。当前 9.9.3 的 PACE / `.ai_state` 双内核仍成立；真正需要更新的是三类漂移：

1. 平台已原生提供、包内仍重复开启或解释的能力。
2. 已过期、会覆盖新模型或角色配置的设置。
3. 同一语义散落在根提示词、skills、agents、hooks 与双端副本中，缺乏可执行的行为回归。

推荐的 9.9.6 主题：**Lean Kernel · Native Defaults · Tested Skills**。

## 调研方法与证据等级

- 官方事实：只采用 Anthropic / OpenAI 官方文档、官方 GitHub release 或仓库源码。
- 外部工程：只采用项目主仓库 README、skill 源文件与 release notes；博客/社区讨论不作为配置依据。
- 本地事实：以 `vibeCoding/{claude,codex}/9.9.3` 和当前 `.ai_state` 的可复核统计为准。
- 推论均明确标为“设计建议”，不伪装成平台事实。

检索日期：2026-07-25。

## Claude Code 官方变化

### 已确认事实

| 主题 | 当前合同 | 对 Athena 的含义 |
|---|---|---|
| Opus 5 | Claude Code `2.1.219` 新增 `claude-opus-5`，并成为 `opus` 的默认模型；支持 1M context | 兼容 floor 提升到 `2.1.219`；使用动态 `opus` alias，不在一方 API 基线中钉死 4.x ID |
| 嵌套 subagent | `2.1.219` 默认允许 subagent 嵌套到 depth 3 | 平台能力已存在，但 Athena 的文件所有权与 gate 仍要求显式拓扑；本版不默认放开 agent 自繁殖 |
| 动态 workflow | 默认 size guideline 改为 medium，目标少于 15 agents | 不再用提示词重复“开启 workflow”；Athena 只保留红黄绿区和所有权约束 |
| 新 hook / sandbox | 新增 `DirectoryAdded` 与 `sandbox.network.strictAllowlist` | 仅在多根目录或严格联网白名单有真实场景时接入，不为追新而默认配置 |
| tool search | 一方连接下 unset 即默认开启 | 删除 `ENABLE_TOOL_SEARCH=1`；第三方 gateway 才显式配置 |
| API timeout | 官方默认每次请求 600000 ms | 删除当前 `API_TIMEOUT_MS=30000`，它把长 agent 请求错误压缩到 30 秒 |
| model aliases | `best` / `opus` / `sonnet` 会随提供商更新；版本 pin 面向受控第三方部署 | 主会话保留 `best`；关键评审用 `opus`；gateway 才使用 `ANTHROPIC_DEFAULT_*` |
| subagent model precedence | `CLAUDE_CODE_SUBAGENT_MODEL` 会覆盖调用参数和 agent frontmatter | 删除全局 override，否则 architect / evaluator / generator 的角色模型矩阵不生效 |
| effort | 全局 setting、会话命令、skill/agent frontmatter 均可控制；frontmatter 适合角色级差异 | 基线删除全局 `xhigh`，只对高价值角色保留显式高 effort；不靠 `ultrathink` 关键词模拟 API effort |
| memory | CLAUDE.md 适合短规则，procedure 应进入 skills；auto memory 是平台召回，不是强约束 | `.ai_state` 继续是权威事实；不在根提示词重复启用或解释平台 memory |
| skills | name/description 常驻发现层，正文按需加载；副作用 skill 可限制模型隐式调用 | skill description 改为 trigger-only；setup/migrate/preferences 等维护 skill 默认显式调用 |

### 9.9.3 设置处置建议

| 当前项 | 9.9.6 | 原因 |
|---|---|---|
| `model: best` | 保留 | 动态选择当前最强可用模型 |
| `fallbackModel: [opus, sonnet]` | 保留 | 合法动态 alias 链 |
| `effortLevel: xhigh` | 删除并做 A/B | 角色 frontmatter 已能精确配置，避免每个日常 turn 都付最高成本 |
| `ANTHROPIC_DEFAULT_OPUS_MODEL=claude-opus-4-8` | 删除，P0 | 已把 `opus` 固定在旧版本，阻止 Opus 5 |
| 其他 `ANTHROPIC_DEFAULT_*` | 一方基线删除 | alias 本来会更新；只在 gateway profile 中 pin |
| `CLAUDE_CODE_SUBAGENT_MODEL=claude-sonnet-5` | 删除，P0 | 覆盖所有 agent role 的模型配置 |
| `ENABLE_TOOL_SEARCH=1` | 删除 | 一方连接默认开启；值也不如官方 `true/auto/false` 语义清楚 |
| `API_TIMEOUT_MS=30000` | 删除，P0 | 官方默认 10 分钟，当前值会误杀长任务 |
| `DISABLE_INSTALLATION_CHECKS=1` | 删除 | 官方仅建议手工管理安装位置时使用，会遮蔽安装问题 |
| `CLAUDE_CODE_ATTRIBUTION_HEADER=0` | 基线删除 | 只对 gateway cache 命中有价值，一方 API 无收益 |
| `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1` | 移出 release-owned 默认 | 属用户隐私/更新策略；迁移必须保留用户已有选择 |
| `workflowSizeGuideline` | 不新增 | 平台已有 medium 默认，Athena 无需复述 |
| Agent Teams | 维持 opt-in | 仍不是 PACE 的默认执行原语 |

### 候选角色矩阵

| 角色 | model alias | effort | 说明 |
|---|---|---|---|
| main | `best` | platform default | 保留账户能力自适应 |
| architect / critic / evaluator | `opus` | `xhigh` | 在 2.1.219 上落到 Opus 5；只用于高价值边界 |
| generator / reviewer / spec-compliance | `sonnet` | `high` | 日常代码与审查的成本/能力平衡 |
| polish worker | `sonnet` | `high` | 清理不需要 Opus 级全局成本 |

Fable 继续作为显式实验候选，不再让包内静态 pin 决定整个角色层。最终矩阵必须经真实 prompt eval 后冻结。

## Codex 官方变化

### 已确认事实

| 主题 | 当前合同 | 对 Athena 的含义 |
|---|---|---|
| 最新模型解析 | 官方 resolver 返回 `gpt-5.6-sol`；当前提示指南强调 lean prompt、紧凑自治策略与成功标准 | 继续以 Sol 为主会话/高价值推理模型，删除重复步骤和同义约束 |
| 模型分工 | GPT-5.6 提供 Sol / Terra 等不同成本能力档 | 高价值设计/裁决用 Sol；读密集、实现与常规 review 候选 Terra，需 eval 验证 |
| stable CLI | 当前稳定 patch 为 `0.144.4`，该 patch 无用户可见变化 | floor 从 0.144.1 刷到 0.144.4；发布时再核对最新稳定版，不追 alpha |
| feature defaults | goals/hooks/multi_agent/personality/shell_snapshot/shell_tool 默认 true，unified_exec 除 Windows 外默认 true | 删除这些 `[features]` 重复开关 |
| memories | 默认 false，Experimental；它是召回层，不是规则层 | 删除 9.9.3 的显式 memories 开启；`.ai_state` 保持唯一权威状态 |
| subagents | 默认 enabled；正式并发字段是 `max_concurrent_threads_per_session`，`max_threads` 只是 legacy alias | 改用正式字段；删除未在当前合同中的 `max_depth` / `job_max_runtime_seconds` |
| skills | 自动发现 `~/.agents/skills`；`[[skills.config]]` 用于禁用/重启具体 skill | 删除 26 个 `enabled=true` 的手工注册 |
| context window | unset 时使用模型/预设元数据 | 删除 1M/900k 人工覆盖，避免模型换代后错误压缩 |
| provider | built-in `openai` 是默认；代理只需 `openai_base_url`，自定义 provider 必须有真实 endpoint | 删除空 `custom_openai` provider；这是 9.9.1 已修、9.9.3 又回归的漂移 |
| skills budget | 初始 skill 列表上限为上下文 2%，未知窗口时为 8000 chars | 当前 CX frontmatter 合计约 8860 bytes，需缩短 trigger descriptions 并限制隐式 skill |
| hooks | default enabled；同一事件的 command hooks 并发，不能依赖顺序 | 删除 feature flag；保留 fail-closed gate，不把 hook 先后当合同 |

### 9.9.3 设置处置建议

| 当前项 | 9.9.6 | 原因 |
|---|---|---|
| `model=gpt-5.6-sol` | 保留 | 官方 resolver 当前结果 |
| `model_reasoning_effort=high` | 先保留，做 medium/high A/B | GPT-5.6 指南建议从更低 effort 比较，不凭感觉降级 |
| `plan_mode_reasoning_effort=xhigh` | 保留 | plan/design 是高价值边界 |
| `model_provider=custom_openai` + 空 provider | 删除，P0 | built-in OpenAI 已满足当前连接，空自定义层没有实际 endpoint |
| `model_context_window` / auto compact pin | 删除，P0 | 应由模型/preset 元数据决定 |
| stable `[features]` true 项 | 删除 | 全部是平台默认 |
| `memories=true` + `[memories]` | 删除 | Experimental 且与 `.ai_state` 权威层重叠 |
| `[features.multi_agent_v2]` | 删除 | 当前官方配置合同没有该表 |
| `[agents].max_threads` | 改正式字段 | legacy alias 可读但不该成为新版本模板 |
| `max_depth` / `job_max_runtime_seconds` | 删除 | 当前正式 subagent 配置表不含这些字段 |
| 26 个 `[[skills.config]] enabled=true` | 删除 | 自动发现已覆盖，配置表不是注册表 |
| `project_doc_max_bytes=65536` | 删除，除非测试证明需要 | 当前根 AGENTS.md 远小于默认预算 |
| extra project root markers | 删除，除非仓库实测需要 | 当前项目以 `.git` 为根 |
| `windows_wsl_setup_acknowledged` | 移出 package | 机器/用户态，不是发行默认 |
| `[desktop]` UI 偏好 | 移出 package | 迁移保留用户选择，发行包不覆盖 |
| `suppress_unstable_features_warning` | 删除 | 不再默认开启 Experimental memories |
| `web_search=live` | 暂保留为 Athena 证据策略 | 这是显式产品选择，不是默认开关；后续可由用户 preference 接管 |
| `approval_policy=never` / `danger-full-access` | 保留现状但单列风险决策 | 合法但高权限；本次不暗改用户既有授权边界 |

### 候选角色矩阵

| 角色 | model | effort | 说明 |
|---|---|---|---|
| main / architect / critic / evaluator | `gpt-5.6-sol` | high / xhigh | 复杂路由、设计与最终裁决 |
| generator / reviewer / spec-compliance / pr-explorer | `gpt-5.6-terra` | medium / high | 常规实现、读取与审查；以 eval 为冻结条件 |
| docs researcher | `gpt-5.6-terra` | medium | 文档检索重点是来源完整性，不是最大推理预算 |

## 外部工程提炼

| 工程 | 可吸收亮点 | 明确不复制 |
|---|---|---|
| Pi | 极薄 harness，plan/subagent 等能力按扩展包安装；交互、print、JSON、RPC、SDK 共用核心 | 不删除 PACE；Athena 的使命本来就是受约束交付，不做另一个无流程终端 |
| Matt Pocock skills / grill-me | 一次只问一个最高价值未决问题；先读 repo；给推荐答案；用共享领域语言降噪 | 不把每个任务都变成长访谈，不保存逐问逐答流水账 |
| Trellis | 按 task 注入相关 spec；任务目录承载 PRD/实现/检查上下文；结束时把验证后的学习提升为长期规范 | 不新增 `.trellis` 第二状态树；映射到现有 sprint / compound / architecture |
| Superpowers | skill 本身做 RED→GREEN→REFACTOR 行为测试；description 只写 trigger；机械约束交给自动化；review prompt 单一真相 | 不安装全局 bootstrap，不复制第二套 brainstorm/TDD/review 状态机 |
| OpenSpec | proposal/spec/design/tasks 同目录，变更可迭代，验收场景可直接映射测试 | 不新增 `openspec/`；用现有 sprint artifact 承载同等语义 |
| GitHub Spec Kit | intent→spec→plan→tasks→implement 的可追溯链，以及跨 artifact 一致性检查 | 不照搬刚性模板和额外 constitution；Athena 已有铁律与 gate |
| GSD | 把 context rot 当一等问题；先 map brownfield，再为单阶段提供小而完整的上下文包 | 不引入大型命令面和另一份 STATE/ROADMAP；只吸收 context budget 与 handoff 测试 |

## 9.9.6 应形成的架构原则

1. **政策核只写一次**：根提示词只保留目标、权限边界、PACE 路由入口、完成判据。
2. **平台默认不入包**：默认开启的 feature 不配置；平台已注入的工具说明不复述。
3. **角色配置优先于全局 override**：模型与 effort 在角色边界声明。
4. **判断放 skill，机械规则放 hook**：skill 处理何时/为何，gate 处理必须发生的可验证事实。
5. **状态只保留当前真相**：`_index` 是小型索引，历史与研究留在 sprint/roadmap/compound。
6. **skill description 是路由索引**：只写触发条件，不在 description 摘要完整工作流。
7. **先测失败再改提示词**：每个删减项要有 9.9.3 baseline 与 9.9.6 对照场景。
8. **双端语义一致、机制诚实不对称**：CC/CX 共享合同，worktree、hook、agent wire 使用各自真实 API。

## 一手来源

### Anthropic

- [Claude Code 2.1.219 release](https://github.com/anthropics/claude-code/releases/tag/v2.1.219)
- [Model configuration](https://code.claude.com/docs/en/model-config)
- [Environment variables](https://code.claude.com/docs/en/env-vars)
- [Tool search](https://code.claude.com/docs/en/agent-sdk/tool-search)
- [Subagents](https://code.claude.com/docs/en/sub-agents)
- [Agents and workflows](https://code.claude.com/docs/en/agents)
- [Git worktrees](https://code.claude.com/docs/en/worktrees)
- [Hooks](https://code.claude.com/docs/en/hooks)
- [Memory](https://code.claude.com/docs/en/memory)
- [Skills / commands](https://code.claude.com/docs/en/slash-commands)

### OpenAI

- [GPT-5.6 model guidance](https://developers.openai.com/api/docs/guides/latest-model)
- [GPT-5.6 Sol](https://developers.openai.com/api/docs/models/gpt-5.6-sol)
- [Codex subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents.md)
- [Codex configuration reference](https://learn.chatgpt.com/docs/config-file/config-reference.md)
- [Codex skills](https://learn.chatgpt.com/docs/build-skills.md)
- [Codex memories](https://learn.chatgpt.com/docs/customization/memories.md)
- [Codex hooks](https://learn.chatgpt.com/docs/hooks.md)
- [AGENTS.md discovery](https://learn.chatgpt.com/docs/agent-configuration/agents-md.md)
- [Codex 0.144.4 release](https://github.com/openai/codex/releases/tag/rust-v0.144.4)

### 外部工程

- [Pi coding agent](https://github.com/badlogic/pi-mono/blob/main/packages/coding-agent/README.md)
- [Matt Pocock skills](https://github.com/mattpocock/skills/blob/main/README.md)
- [Trellis](https://github.com/mindfold-ai/trellis)
- [Superpowers](https://github.com/obra/superpowers)
- [Superpowers skill testing](https://github.com/obra/superpowers/blob/main/skills/writing-skills/testing-skills-with-subagents.md)
- [OpenSpec](https://github.com/Fission-AI/OpenSpec)
- [GitHub Spec Kit](https://github.github.com/spec-kit/)
- [GSD](https://github.com/gsd-build/get-shit-done)
