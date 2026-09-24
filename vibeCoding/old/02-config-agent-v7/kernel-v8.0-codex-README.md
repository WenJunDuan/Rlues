# VibeCoding Kernel v8.0 (Codex CLI)

> **"Talk is cheap. Show me the code."** — Linus Torvalds

AI 编程协作系统。支持 Claude Code / Codex CLI 双平台，Agent Teams 并行协作。

## 快速开始

```bash
# 安装
./install.sh          # Linux/macOS
.\install.ps1         # Windows

# 在项目中使用
cd your-project
vibe-init              # 初始化
vibe-dev "任务描述"     # 开发
vibe-plan "功能需求"    # 规划
vibe-review            # 审查
vibe-todos             # 查看看板
vibe-dev --team "大型重构"  # Agent Teams 并行
```

## v8.0 核心变更

### 对比 v7.9.1

| 特性 | v7.9.1 | v8.0 |
|:---|:---|:---|
| 上下文 | 200K | 1M (beta) |
| 思维模式 | Extended Thinking (手动 budget) | Adaptive Thinking (4 档 effort) |
| 并行 | 单 Agent | Agent Teams (多 Agent 协作) |
| 路由 | P.A.C.E. 3 路径 | P.A.C.E. v2.0 (4 路径 + Path D) |
| 状态管理 | active_context.md 单文件 | plan/todo/doing/done/archive 五文件 |
| 压缩策略 | 紧急 compact | Smart Archive + 服务端 Compaction |
| sequential-thinking | MCP 依赖 | 已移除，Adaptive Thinking 替代 |
| 模型路由 | 手动选择 | Model Router 自动路由 |

### .ai_state 状态体系

```
project_root/.ai_state/
├── plan.md          # 方案计划
├── todo.md          # 待办任务
├── doing.md         # 进行中 (max 3 并行)
├── done.md          # 已完成
├── archive.md       # 历史归档
├── decisions.md     # 架构决策 (ADR)
├── conventions.md   # 项目约定 + 用户纠正
└── session.md       # 会话状态
```

### P.A.C.E. v2.0 路由

| 路径 | 条件 | effort | 执行方式 |
|:---|:---|:---|:---|
| A | 单文件, <30行 | low | 快速修复 |
| B | 2-10文件 | medium | 计划开发 |
| C | >10文件 | high/max | 完整九步 |
| D | 架构级, 可并行 | max | Agent Teams |

### MCP 工具

Claude Code: `augment-context-engine`, `cunzhi`, `mcp-deepwiki`

Codex CLI: 上述 + `chrome-devtools`, `desktop-commander`

## 指令体系

### 增强官方 (先调用官方再增强)

| 指令 | 官方基础 | 增强 |
|:---|:---|:---|
| vibe-init | /init | + .ai_state + .knowledge |
| vibe-plan | /plan | + KB + EXP + effort |
| vibe-todos | /todos | + 三态流转 |
| vibe-review | /review | + 质量 + 安全 |
| vibe-status | /status | + 全状态汇报 |
| vibe-resume | /resume | + 上下文恢复 |

### 纯自定义

| 指令 | 用途 |
|:---|:---|
| vibe-dev | 智能开发入口 |
| vibe-verify | 验证循环 |
| vibe-learn | 模式学习 |
| vibe-checkpoint | 检查点 |
| vibe-exp | 经验操作 |
| vibe-kb | 知识库操作 |
| vibe-pause | 暂停 |
| vibe-archive | 归档 |

## 按需加载架构

```
CLAUDE.md (铁律) → P.A.C.E. 路由 → 对应 skill → 专项 skill
```

每次只加载需要的部分，不预加载，不堆积。

## 版本历史

### v8.0 (当前)
- Adaptive Thinking 替代 sequential-thinking
- Agent Teams 并行协作 (Path D)
- Model Router 智能路由
- .ai_state 五文件状态体系
- Smart Archive 替代 strategic-compact
- 所有自定义指令统一 vibe- 前缀
- 增强指令必须先调用官方版本
- P.A.C.E. v2.0 四路径路由

### v7.9.1
- Instinct-based Learning
- Cunzhi MCP Integration
- Context7 CLI Support
- Cross-platform Hooks

## License

MIT
