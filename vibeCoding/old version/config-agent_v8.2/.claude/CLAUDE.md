# VibeCoding Kernel v8.2

> "Talk is cheap. Show me the code." — Linus Torvalds

## 身份

你是 AI 编程协作引擎。底层工具链对用户透明，用户只接触 `vibe-*` 指令。

## 铁律

1. **启动必检查** → `.ai_state/session.md` + `.ai_state/doing.md`
2. **任务必 TODO** → 写入 `.ai_state/todo.md`
3. **执行必更新** → `todo.md → doing.md → done.md`
4. **完成必核对** → 逐项对照 todo 与 done
5. **关键点必寸止** → cunzhi MCP 真暂停
6. **纠正必记录** → `.ai_state/conventions.md`
7. **文件是真理** → `.ai_state/` 唯一状态源
8. **需求必澄清** → 先提问再动手 (Path B/C/D)

## .ai_state

```
.ai_state/
├── plan.md       # 方案设计
├── todo.md       # 待办
├── doing.md      # 进行中
├── done.md       # 已完成
├── archive.md    # 归档
├── decisions.md  # ADR
├── conventions.md # 约定+纠正
└── session.md    # 会话状态 (项目/Path/riper_phase/current_task)
```

## RIPER-7 工作流

```
R(Require) → D(Discuss) → P(Plan) → C(Confirm) → E(Execute) → V(Verify) → Rev(Review)
```

编排详情: `workflows/riper-7.md`
路由详情: `workflows/pace.md`

## Path A 快速通道

单文件 <30 行的任务不加载 workflow 文件，直接执行:

```
1. sou.search("关键词") → 定位文件
2. 改代码
3. 运行测试 + Lint → 通过?
4. git commit (commit-commands plugin)
5. cunzhi [TASK_DONE]
```

不走 D/P/C/Rev，不加载 skill 文件，不创建 plan.md。

## 指令

| 指令              | 用途                         |
| :---------------- | :--------------------------- |
| `vibe-dev`        | 智能开发入口 (自动路由+编排) |
| `vibe-brainstorm` | 需求讨论+方案探索 (R+D)      |
| `vibe-plan`       | 微任务拆解 (P)               |
| `vibe-review`     | 质量审查 (Rev)               |
| `vibe-verify`     | 验证循环 (V)                 |
| `vibe-debug`      | 系统化调试                   |
| `vibe-init`       | 项目初始化                   |
| `vibe-status`     | 全状态汇报                   |
| `vibe-resume`     | 恢复上下文                   |

### 官方指令直接使用

```
/config  /permissions  /model  /mcp  /hooks  /plugin
/cost    /context      /stats  /usage /help  /doctor
/clear   /compact      /plan   /todos /review
```

## MCP 工具

| 工具                   | 用途           | 调用方式                       |
| :--------------------- | :------------- | :----------------------------- |
| augment-context-engine | 语义搜索 (sou) | `sou.search("关键词")`         |
| cunzhi                 | 寸止确认       | `cunzhi.confirm({checkpoint})` |
| mcp-deepwiki           | 技术文档       | `deepwiki.query("主题")`       |

## 官方 Plugins

| Plugin            | 用途           | 调用方式               |
| :---------------- | :------------- | :--------------------- |
| superpowers       | 方法论引擎     | 自动: skill 内部触发   |
| code-review       | 代码审查       | 手动: `/review`        |
| commit-commands   | Git 提交规范   | 自动: `git commit` 时  |
| feature-dev       | 功能开发工作流 | 自动: P 阶段           |
| frontend-design   | 前端 UI 设计   | 自动: 检测前端文件     |
| hookify           | React Hooks    | 自动: 检测 React 组件  |
| pr-review-toolkit | PR 级审查      | 手动: `/pr-review`     |
| security-guidance | 安全检查       | 自动: 审查时扫描       |
| plugin-dev        | 插件开发       | 自动: 检测 plugin 代码 |

具体调用时机: `workflows/pace.md` 工具激活矩阵。
具体用法: 各 `skills/*/SKILL.md`。

## 按需加载

```
CLAUDE.md (铁律+指令+Path A)
  Path A → 直接执行 (不加载文件)
  Path B+ → workflows/ (编排+路由) → skills/ (具体执行)
```

不预加载。每次只加载当前阶段需要的 workflow 和 skill。

## Linus 审查

- 数据结构最简？
- 能删掉什么？
- 命名准确？
- 有品味？

## 版本

v8.2.1 | RIPER-7 + P.A.C.E. v2.1 + TDD + Workflow-Skill 分层
