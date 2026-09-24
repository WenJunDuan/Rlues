# Claude Code platform contract (Athena 9.9.9 candidate)

## 单平台基础与用户配置

CC-only 完成适用的全部 PACE 阶段。CX、Grok、Antigravity、VM 和付费插件只在用户选择且实际可用时增强；没有另一端账号不阻塞 CC 的实现与独立审查。不宣称 Grok-only 发行支持。

新安装采用原生 `permissions.defaultMode: default`；迁移保留用户有效模型、effort、provider、权限、凭证、plugins 与第三方 hooks/skills。模型默认继承当前会话，不固定厂商分工，不通过全局模型变量覆盖用户选择。可调用能力与副作用授权分别核对。

## 原生边界

全部 Athena agent 定义统一 `maxTurns: 70`（包括仍禁止 live 调度的 stub）。按 [原生字段](https://code.claude.com/docs/en/subagents#supported-frontmatter-fields) 限制 agentic turns；到限返回实际进度，不算 PASS，不自动续派绕限。这不配置主会话或平台内置 reviewer 的隐藏子任务，也不保证终止单次挂起的工具。

- CC 使用 Agent tool 和 `.claude/agents/*.md` frontmatter。原生 `isolation: worktree` 只在需要隔离时使用；默认不注册 WorktreeCreate/Remove override。
- 只读 reviewer 是本端完整 fallback；使用 plan 权限和只读工具，返回结果，由主 agent 持久化。writer 绑定与恢复见 [execution-contracts.md](execution-contracts.md)。
- 实际异步入口才写 `await-review-result`；前台返回直接接收。当前入口不支持后台时不假设有通知。
- 可选增强不可用时沿本端可用路径继续；独立审查或必需环境缺失时保留相关验收未完成。
- 红区门禁保持同步、fail-closed；提示/诊断是否异步不改变授权或验收。

## 版本与能力证明

本机研究观察为 Claude Code 2.1.236；这是观察值，不是最低兼容或最新版本保证。发布前须逐项记录实际版本、入口、hook payload、review 返回、worktree 内容和运行结果。探测成功不等于对应项目场景通过。

官方文档（滚动更新，承重行为还需现场实测）：
- [Subagents/frontmatter](https://code.claude.com/docs/en/sub-agents)
- [Settings/permissions](https://code.claude.com/docs/en/settings)
- [Model configuration](https://code.claude.com/docs/en/model-config)
- [Hooks](https://code.claude.com/docs/en/hooks)
- [Code Review](https://code.claude.com/docs/en/code-review)
