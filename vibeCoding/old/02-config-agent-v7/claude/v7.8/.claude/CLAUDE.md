# VibeCoding Kernel v7.8

> **"Talk is cheap. Show me the code."** — Linus Torvalds
> **"Claude不是聊天机器人，而是可并行调度、可验证的工程资源。"** — Boris Cherny

## 七条铁律

1. **先读后写** - 修改前必须读取目标文件
2. **知识先行** - 开发前检索知识库和经验库
3. **寸止等待** - 关键节点调用寸止工具暂停
4. **状态同步** - 变更后更新 .ai_state/
5. **验证闭环** - 执行后必须验证结果
6. **经验沉淀** - 完成后沉淀经验到经验库
7. **能力增强** - 优先使用 MCP 工具和官方 Skills

## 五层架构

```
┌─────────────────────────────────────────────────────────────────┐
│  用户层        用户输入 / vibe-dev "新功能"                      │
├─────────────────────────────────────────────────────────────────┤
│  Command层     增强官方 + 纯自定义                               │
│                vibe-plan → /plan + KB + EXP                     │
├─────────────────────────────────────────────────────────────────┤
│  Agent决策层   phase-router → 功能导向 Agents                    │
│                requirement-mgr / design-mgr / impl-executor     │
├─────────────────────────────────────────────────────────────────┤
│  Skill执行层   context7 / knowledge-base / experience / riper   │
│                continuous-learning / verification-loop          │
├─────────────────────────────────────────────────────────────────┤
│  数据存储层    .ai_state/ + .knowledge/                         │
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
| 库文档获取 | context7 skill | context7 MCP |
| 知识检索 | knowledge-base skill | memory MCP |
| 经验匹配 | experience skill | memory MCP |
| 深度推理 | sequential-thinking | thinking skill |
| 代码验证 | verification-loop skill | 手动测试 |
| 模式提取 | continuous-learning skill | 手动记录 |

## 指令速查

### 增强官方指令
| 指令 | 官方基础 | 增强内容 |
|:---|:---|:---|
| `vibe-init` | /init | + .ai_state + 知识库 |
| `vibe-plan` | /plan | + KB + EXP + 九步 |
| `vibe-todos` | /todos | + Kanban + 进度 |
| `vibe-review` | /review | + 规范 + 质量检查 |

### 纯自定义指令
| 指令 | 说明 |
|:---|:---|
| `vibe-dev` | 智能开发入口 |
| `/learn` | 提取当前会话模式 |
| `/checkpoint` | 保存验证检查点 |
| `/verify` | 运行验证循环 |

## 数据存储

```
.ai_state/
├── requirements/     # 需求文档
├── designs/          # 设计文档
├── experience/       # 经验库
│   └── learned/      # 自动提取的模式
├── checkpoints/      # 验证检查点
└── meta/             # 元信息

.knowledge/           # 外部知识库
├── project/          # 项目文档
├── standards/        # 开发规范
└── tech/             # 技术栈文档
```

---
**版本**: v7.8.0 | **架构**: VibeCoding Modular
