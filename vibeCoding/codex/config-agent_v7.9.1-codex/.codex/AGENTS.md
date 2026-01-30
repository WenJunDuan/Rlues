# VibeCoding Kernel v7.9.1

> **"Talk is cheap. Show me the code."** — Linus Torvalds
> **"AI 不是聊天机器人，而是可并行调度、可验证的工程资源。"** — Boris Cherny

## 七条铁律

1. **先读后写** - 修改前必须读取目标文件
2. **知识先行** - 开发前检索知识库和经验库
3. **寸止等待** - 关键节点调用 cunzhi MCP 等待确认
4. **状态同步** - 变更后更新 .ai_state/
5. **验证闭环** - 执行后必须验证结果
6. **经验沉淀** - 完成后沉淀经验到经验库
7. **能力增强** - 优先使用 Skills 和 MCP 工具

## 五层架构

```
┌─────────────────────────────────────────────────────────────────┐
│  用户层        用户输入 / vibe-dev "新功能"                      │
├─────────────────────────────────────────────────────────────────┤
│  Command层     vibe-* 增强官方 / 纯自定义指令                    │
│                vibe-plan→/plan / learn / verify / checkpoint    │
├─────────────────────────────────────────────────────────────────┤
│  Agent决策层   phase-router → 功能导向 Agents                    │
│                requirement-mgr / design-mgr / impl-executor     │
├─────────────────────────────────────────────────────────────────┤
│  Skill执行层   context7 / knowledge-base / experience / riper   │
│                continuous-learning-v2 / verification-loop       │
├─────────────────────────────────────────────────────────────────┤
│  数据存储层    .ai_state/ + .knowledge/ + instincts/            │
└─────────────────────────────────────────────────────────────────┘
```

## 意图路由 (phase-router)

```yaml
路由规则:
  无任务ID → 新建任务 (需求创建)
  任务ID + "变更/修改" → 变更管理
  任务ID + "设计/架构" → 方案设计
  任务ID + "开发/实现" → 开发实施
  任务ID + "完成/发布" → 流转归档
  仅任务ID → 智能推断当前状态并继续
```

## 复杂度评估 (P.A.C.E.)

| Path | 标准 | 工作流 | 时长 |
|:---|:---|:---|:---|
| A | 单文件, <30行 | R1→E→R2 | 30-60分 |
| B | 2-10文件 | R1→I→P→E→R2 | 2-8小时 |
| C | >10文件, 跨模块 | 完整九步 | 数天+ |

## 九步工作流

| 阶段 | 说明 | 寸止点 |
|:---|:---|:---|
| 需求创建 | 创建需求文档 | - |
| 需求审查 | 确认需求理解 | `[REQ_READY]` |
| 方案设计 | 技术方案设计 | - |
| 方案审查 | 确认设计方案 | `[DESIGN_READY]` |
| 环境搭建 | 准备开发环境 | - |
| 开发实施 | 编码实现 | `[PHASE_DONE]` |
| 代码提交 | 提交代码 | - |
| 版本发布 | 发布版本 | `[RELEASE_READY]` |
| 完成归档 | 归档沉淀 | `[TASK_DONE]` |

## 能力增强矩阵

| 场景 | 优先使用 | 备选 |
|:---|:---|:---|
| 库文档获取 | context7 CLI (`npx ctx7`) | 官方文档 |
| 知识检索 | knowledge-base skill | 项目文档 |
| 经验匹配 | experience skill | instincts |
| 深度推理 | sequential-thinking MCP | 内置推理 |
| 寸止确认 | cunzhi MCP | 文本确认 |
| 代码验证 | verification-loop skill | 手动测试 |
| 模式提取 | continuous-learning-v2 | /learn |

## 指令速查

### 增强官方指令
| 指令 | 说明 |
|:---|:---|
| `vibe-init` | 初始化 → 调用 `/init` 后创建 .ai_state/ |
| `vibe-plan <desc>` | 规划 → 调用 `/plan` 后整合知识库 |
| `vibe-todos` | 待办 → 调用 `/todos` 后同步 kanban |
| `vibe-review` | 审查 → 调用 `/review` 后运行质量检查 |

### 纯自定义指令
| 指令 | 说明 |
|:---|:---|
| `vibe-dev <desc>` | 智能开发入口（意图路由）|
| `learn` | 提取当前会话模式 |
| `checkpoint <name>` | 保存验证检查点 |
| `verify` | 运行验证循环 |
| `instinct-status` | 查看学习的 instincts |
| `instinct-export` | 导出 instincts |
| `evolve` | 将 instincts 聚类为 skills |

## 数据存储

```
.ai_state/
├── requirements/     # 需求文档
├── designs/          # 设计文档
├── experience/       # 经验库
│   └── learned/      # 自动提取的模式
├── instincts/        # Instinct-based 学习
│   └── instincts.json
├── checkpoints/      # 验证检查点
└── meta/             # 元信息

.knowledge/           # 外部知识库
├── project/          # 项目文档
├── standards/        # 开发规范
└── tech/             # 技术栈文档
```

## Context7 集成

使用 Context7 CLI 获取最新库文档：

```bash
# 搜索 skills
npx ctx7 skills search <keyword>

# 安装 skill
npx ctx7 skills install /org/project <skill>

# 生成自定义 skill
npx ctx7 skills generate
```

或在提示中使用 `use context7` 触发文档获取。

## Cunzhi MCP

寸止确认通过 cunzhi MCP 实现，在关键节点调用：

```
mcp__cunzhi__confirm({
  point: "PLAN_READY",
  content: "计划内容摘要",
  options: ["继续", "修改", "取消"]
})
```

---
**版本**: v7.9.1 | **架构**: VibeCoding Modular | **平台**: Codex CLI
