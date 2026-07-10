---
roadmap_slug: "athena-9-9-1-release"
created: "2026-07-10"
trigger: "main_agent_3_modules_detected"
estimated_total_complexity: "XL"
---

# Roadmap — athena-9-9-1-release

## 背景

Athena 9.9.0 在 Codex CLI 0.144.1 上可加载，但 hooks wire、原生 multi-agent、安装迁移、agent 写入合约、skill frontmatter 与 GPT-5.6 提示词策略存在确定漂移。9.9.1 以 9.9.0 为只读基板，发布一套可安装、可验证、可审查的双端补丁版。

## 总体方案

保留 9.9.0 目录不变，复制生成 CC/CX 9.9.1；先修 CX runtime contract，再统一双端 skills/agents/提示词，最后闭合 setup/migrate、行为 fixtures、runtime-verify、review、polish 与 architecture 档案。

## 子 feature 拆分

| # | slug | title | 复杂度 | 依赖 |
|---|---|---|---|---|
| 1 | cx-runtime-contract | CX config/hooks/native multi-agent 兼容 | XL | 无 |
| 2 | agent-skill-contract | Agent 落盘模型、路径与 skill schema | L | cx-runtime-contract |
| 3 | installer-release | setup/migrate/版本/双端发布包 | L | agent-skill-contract |
| 4 | validation-delivery | runtime-verify/review/polish/architecture/ship | L | installer-release |

## 推进顺序

1. CX runtime、agent/skill、installer 三个互斥写集在同一隔离 worktree 并行实现，各自使用独立 sprint 与验收。
2. 三项全部完成后进入 validation-delivery，统一运行 runtime-verify、review、polish、architecture 与 ship。

每个 item 使用独立 `sprint_slug`；前三项无文件依赖，可并行实现但分别留证，validation item 必须等待三项全部完成。`2026-07-10-athena-9-9-1-release` 仅保存跨 item 的总设计与发布验收，不作为 roadmap item 复用。

## 风险与权衡

- 风险：原生 spawn 工具不提供 cwd，无法继续承诺参数级 worktree 隔离。
  - 缓解：主线程先建 worktree，subagent 任务携带绝对路径并要求每次命令显式 workdir/pwd；强隔离改由独立 task/thread 或 managed worktree 承担。
- 风险：PostToolUse 不提供结构化 exit code。
  - 缓解：未知结果一律记录 unknown；显式 sentinel/独立测试报告才可判 pass。
- 风险：覆盖 config 会损坏用户 provider/MCP/project/desktop 状态。
  - 缓解：首装使用 portable base config；升级走定点迁移并保留用户表。

## 历史决策对齐

- 保留 PACE 单一状态机、CC/CX 双端包对称与 .ai_state 单一事实源。
- 保留用户的执行优先偏好，但不再把 hook 描述成完整安全边界。

## 验收

- [x] items.yaml 全部 completed
- [x] 9.9.1 CC/CX 包存在，9.9.0 无改动
- [x] 行为 fixtures、strict config、skill validator、包一致性全部通过
- [x] runtime-verify、三维 review、polish、architecture 更新完成
- [x] 产生 compound learning
