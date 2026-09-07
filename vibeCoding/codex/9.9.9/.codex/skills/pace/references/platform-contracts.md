# Codex platform contract（Athena 9.9.9 candidate）

这是原生平台边界与待实测项的冷路径参考，不是第二状态树或厂商角色路由器。CX-only 必须能完成适用 PACE；CC/Grok 仅在用户选择、能力可用且有收益时增强。

## 配置与模型

发行 config.toml 是用户级 `~/.codex/config.toml` 的首装模板。provider、model、effort、权限、sandbox、插件、网关等用户现值在迁移时保留；不把示例值当覆盖指令。`VIBECODING_VERSION` 当前身份为 9.9.9。
独立 agent TOML 保留 name、description、developer_instructions 与职责所需 sandbox；省略 model/effort，让原生配置继承生效。用户明确指定的模型优先，不按厂商固定 architect/generator/reviewer。
项目级配置与用户级配置的支持键不同；provider/网关设置按官方用户级 schema 放置，release 包不含凭证。

## 原生协作与权限

所有 Athena agent 每次任务最多70轮，到限返回实际进度与未完成项，不自动续派绕限。2026-09-07 核对本机 Codex 0.153.4、当前 spawn_agent schema 与下方官方配置参考，未发现原生 maxTurns/max_turns；本版写入 developer_instructions，属于指令约束，不是运行时强制限制，不用并发线程数或秒数冒充轮次。

只用当前界面实际提供的 spawn_agent/send_message/followup_task/wait_agent 与其 schema；不假定每个版本拥有相同参数。
红区主 thread 创建绝对 worktree，派工携带路径，writer `pwd`/显式 workdir；不是 CC `isolation: worktree` frontmatter。握手和恢复见 [orchestration](orchestration.md)、[execution-contracts](execution-contracts.md)。
保留包内既有 multi_agent_v2 配置，不凭滚动文档机械迁移开关；发行前在目标 CLI/App 对实际配置加载与承重工具入口实测。可调用能力不等于外部副作用授权，原生权限仍生效。

## Review 与 hooks

优先本端原生 review；不可用时一个本端只读 reviewer/独立会话。只有入口真实异步才设置 await-review-result；通知、等待和回读按实际平台支持恢复。独立结果按持久请求与当前输入绑定后接受。
红区门禁不能改成非阻断异步 hook。hook 配置、payload、handler/matcher、退出码与可见结果均以当前版本实测为准；静态文档不是支持证明。AC14（SessionStart/UserPromptSubmit/PostCompact/SubagentStart/Stop `decision:block`/`statusMessage`、`apply_patch` 的 `file_path`/`patch`、`CODEX_THREAD_ID` 注入）包内无现场出处，装机前保持未验证。

## 待发布证据

candidate 不声明完成 ship。正式发行前按设计验收记录目标平台/版本/入口的启动、配置加载、单端闭环、review、worktree、关键 hooks、迁移与回滚结果。模型、账号、网关可用性只采用现场事实，未知保持未验证。

官方依据：[configuration reference](https://learn.chatgpt.com/docs/config-file/config-reference)、[subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents)、[hooks](https://learn.chatgpt.com/docs/hooks)。
