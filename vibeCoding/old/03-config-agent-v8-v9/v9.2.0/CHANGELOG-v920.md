# VibeCoding Kernel v9.2.0 Changelog

基线: v9.1.9 (双 Agent 对抗协作)

## 新增特性

### P0-1: 双 Agent 通信层完善
- codex-bridge.cjs: `resumeSession()` — session resume 多轮上下文保持
- codex-bridge.cjs: `generateReviewId()` — UUID 并发安全
- codex-bridge.cjs: `ensureServe()` — 自动启动 codex serve
- codex-bridge.cjs: `getSessionMessages()` — 获取历史消息
- codex-review: 对抗循环改为 resume 同一 session
- codex-review: 强制 `VERDICT: APPROVED` 或 `VERDICT: REVISE`
- 新增 `reviews/` 目录用于审查结果持久化
- .gitignore 模板新增 reviews/

### P0-2: Reflexion 自我反思
- 新增 reflexion skill (CC + Codex)
- E 阶段每个 Task Micro-review 前触发
- 6 条自问清单: 捷径/边界/硬编码/过度工程/偏离spec/可读性
- 发现问题立即修复, 模式性问题追加到 lessons.md

### P0-3: 4 级 Quality Gate
- delivery-gate.cjs 从二元改为 4 级:
  - exit 0 = PASS (全通过)
  - exit 1 = CONCERNS (小问题, 标注后放行)
  - exit 2 = REWORK (中等问题, 阻断)
  - exit 3 = FAIL (严重问题, 阻断)
- LLM-as-Judge prompt 也对应 4 级输出

### P1-1: brainstorm 增强
- R₀ 阶段 brainstorm 先执行自主调研再提问
- 搜项目代码 + 读 lessons/conventions + 问 Codex 常见陷阱

### P1-2: 验收标准逐条确认
- T 阶段 verification 增加验收标准确认步骤
- 读 design.md "## 验收标准" 逐条确认
- 未满足标准标注到 quality.md

### P1-3: finish-branch skill
- V 阶段分支收尾: merge / PR / keep / discard
- PR 自动生成 description

### P1-4: conventions.md 增强
- 新增 "## Agent 易犯错误" 段
- context-loader.cjs SessionStart 时输出提醒
- reflexion/kaizen 发现的模式性错误自动追加

### P2-1: superpowers 可选安装说明
- README + CLAUDE.md 说明安装方式和优先级

### P2-2: Review Templates
- 4 个审查模板: API / Frontend / Infra / General
- codex-review 根据 design.md 关键词自动选择

### P2-3: Codex 通信层增强
- ensureServe(): 自动启动 serve
- getSessionMessages(): 获取历史
- healthCheck(): 2s 超时 + 自动降级

## 平台更新同步
- CC: 支持 Elicitation/ElicitationResult hooks, PostCompact hook (不在本框架使用但已验证兼容)
- CC: /effort, /loop, /simplify, /batch 为平台原生命令, 不冲突
- Codex: gpt-5.4 为推荐模型 (更新自 gpt-5.3)
- Codex: wait_agent 命名对齐 spawn_agent
- Codex: userpromptsubmit hook 可用 (本版本未使用, 后续可扩展)

## 自审修复 (构建后)

| # | 严重度 | 问题 | 修复 |
|---|--------|------|------|
| 1 | **CRITICAL** | settings.json hooks 格式错误: 用了 `{command: "..."}` 平铺格式 | 改为官方嵌套格式 `{hooks: [{type: "command", command: "..."}]}` |
| 2 | **CRITICAL** | settings.json `env` 字段不存在 | 改为官方 `environmentVariables` |
| 3 | **CRITICAL** | delivery-gate exit(3) FAIL / exit(1) CONCERNS 不是 Stop hook 标准码 | FAIL/REWORK 统一 exit(2) 阻断停止; CONCERNS 改 exit(0)+stdout 警告放行 |
| 4 | **HIGH** | CC agent frontmatter `worktree: true` 非官方字段 | 改为 `isolation: worktree` |
| 5 | **HIGH** | Codex config.toml `web_search = true` 放在 [features] 下, 类型也错 | 移到根级, 改为 `web_search = "cached"` (字符串) |
| 6 | **MEDIUM** | Codex config.toml `[environment]` 不是有效 section | 改为 `[shell_environment_policy] set = {...}` |
| 7 | **MEDIUM** | Codex config.toml `[options] notify = true` 非官方格式 | 移除 (notify 配置方式不同) |
| 8 | **MEDIUM** | Codex config.toml [agents] 缺 role 定义 | 添加 [agents.builder/validator/explorer] 指向 config_file |
| 9 | **LOW** | pre-bash 用 exit(2) 阻断而非 JSON decision output | 改为 JSON `{permissionDecision: "deny"}` (官方推荐) |
| 10 | **LOW** | delivery-gate.cjs grep regex 转义语法错误 | 简化 regex |

## 自审第二轮 (agent 视角)

| # | 严重度 | 问题 | 修复 |
|---|--------|------|------|
| 11 | **MEDIUM** | codex-bridge execSync 拼接 shell 字符串, `$()` 和反引号可注入 | 改为 execFileSync (参数直接传递, 不经 shell) |
| 12 | **MEDIUM** | augment-context-engine 是外部 MCP, 未装时 agent 困惑 | 加 fallback: "Grep/Glob, 或 augment-context-engine 如已安装" |
| 13 | **MEDIUM** | cunzhi 8 处引用, 未装时 agent 卡在确认门控 | 每处加 fallback: "cunzhi 不可用时直接输出确认提示" |
| 14 | **LOW** | codex-review SKILL.md 用 JS 函数名, agent 读不懂 | 改为自然语言指令 (uuidgen, codex exec resume) |

## 文件统计
- CC: ~47 files
- Codex: ~29 files
- 新增 files: 8 (CC: 6, Codex: 2)
- 修改 files: 16 (CC: 10, Codex: 6)
