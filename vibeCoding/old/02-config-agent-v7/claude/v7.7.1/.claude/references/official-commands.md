# 官方指令映射

## 设计原则
VibeCoding 的自定义指令是**对官方指令的增强**，而非替代。自定义指令应该：
1. 调用官方指令作为基础能力
2. 在官方能力之上叠加 MCP、Skills、Workflow 增强
3. 确保官方的统计、追踪等功能正常工作

## 官方指令清单

### 项目与会话
| 官方指令 | 用途 | VibeCoding 增强 |
|:---|:---|:---|
| `/init` | 初始化项目 CLAUDE.md | vibe-init 增强 |
| `/memory` | 编辑 CLAUDE.md | 直接使用官方 |
| `/clear` | 清除对话历史 | 直接使用官方 |
| `/compact` | 压缩对话 | 直接使用官方 |
| `/resume` | 恢复会话 | vibe-resume 增强 |
| `/rename` | 重命名会话 | 直接使用官方 |

### 开发流程
| 官方指令 | 用途 | VibeCoding 增强 |
|:---|:---|:---|
| `/plan` | 进入计划模式 | vibe-plan 增强 |
| `/todos` | 列出 TODO | vibe-todos 增强 |
| `/review` | 代码审查 | vibe-review 增强 |
| `/security-review` | 安全审查 | 直接使用官方 |

### 系统管理
| 官方指令 | 用途 | VibeCoding 增强 |
|:---|:---|:---|
| `/agents` | 管理子代理 | vibe-agents 增强 |
| `/hooks` | 管理钩子 | 直接使用官方 |
| `/mcp` | 管理 MCP 服务器 | 直接使用官方 |
| `/plugin` | 管理插件 | 直接使用官方 |
| `/permissions` | 查看权限 | 直接使用官方 |

### 信息查看
| 官方指令 | 用途 | VibeCoding 增强 |
|:---|:---|:---|
| `/status` | 显示状态 | vibe-status 增强 |
| `/cost` | 令牌统计 | 直接使用官方 |
| `/context` | 上下文使用 | 直接使用官方 |
| `/stats` | 使用统计 | 直接使用官方 |
| `/usage` | 计划限制 | 直接使用官方 |

### 其他
| 官方指令 | 用途 | VibeCoding 增强 |
|:---|:---|:---|
| `/help` | 获取帮助 | 直接使用官方 |
| `/doctor` | 健康检查 | 直接使用官方 |
| `/config` | 打开设置 | 直接使用官方 |
| `/model` | 选择模型 | 直接使用官方 |
| `/sandbox` | 沙箱模式 | 直接使用官方 |
| `/rewind` | 回退对话 | 直接使用官方 |

## VibeCoding 增强指令

### 增强官方指令
这些指令**必须先调用官方指令**，然后叠加增强：

| VibeCoding 指令 | 基于官方 | 增强内容 |
|:---|:---|:---|
| `vibe-init` | `/init` | + 创建 .ai_state/ + 知识库初始化 |
| `vibe-plan` | `/plan` | + 知识库检索 + 经验检索 + 九步流程 |
| `vibe-todos` | `/todos` | + Kanban 视图 + 进度追踪 |
| `vibe-review` | `/review` | + 知识库规范 + 经验匹配 + 质量检查 |
| `vibe-status` | `/status` | + 任务状态 + 流程进度 |
| `vibe-resume` | `/resume` | + .ai_state 恢复 + 上下文重建 |
| `vibe-agents` | `/agents` | + 功能导向代理 + 路由配置 |

### 纯自定义指令
这些是全新指令，无官方对应：

| VibeCoding 指令 | 用途 |
|:---|:---|
| `vibe-dev` | 需求研发入口（智能路由）|
| `vibe-service` | 服务上下文加载 |
| `vibe-exp` | 经验库操作 |
| `vibe-kb` | 知识库操作 |
| `vibe-pause` | 暂停工作流 |
| `vibe-abort` | 中止工作流 |

## 增强调用模式

### 模式说明
```
用户调用 vibe-xxx
       ↓
┌─────────────────┐
│ 1. 调用官方指令  │ ← 确保官方功能正常
└────────┬────────┘
         ↓
┌─────────────────┐
│ 2. VibeCoding   │ ← 叠加增强能力
│    增强处理      │
└────────┬────────┘
         ↓
┌─────────────────┐
│ - 知识库检索     │
│ - 经验库检索     │
│ - MCP 工具调用   │
│ - Workflow 执行  │
│ - Skills 加载    │
└─────────────────┘
```

### 示例: vibe-plan

```yaml
执行流程:
  1. 调用官方 /plan
     → 进入计划模式
     → 官方统计正常记录
  
  2. VibeCoding 增强
     → 检索知识库 (项目背景、规范)
     → 检索经验库 (类似任务经验)
     → 加载 riper/plan skill
     → 执行九步工作流的 Plan 阶段
     → 生成增强的 TODO.md
     → 更新 .ai_state/
```

### 示例: vibe-review

```yaml
执行流程:
  1. 调用官方 /review
     → 官方代码审查
     → 官方统计正常记录
  
  2. VibeCoding 增强
     → 检索知识库 (审查清单、规范)
     → 检索经验库 (常见问题)
     → 加载 riper/review skill
     → 加载 code-quality skill
     → 执行 Linus 品味检查
     → 沉淀审查经验
```

## 直接使用官方指令

以下场景直接使用官方指令，无需 vibe 增强：

```yaml
配置管理:
  - /config, /permissions, /model, /plugin

信息查看:
  - /cost, /context, /stats, /usage

系统操作:
  - /clear, /compact, /rewind, /doctor

MCP 管理:
  - /mcp (直接使用官方管理)

钩子管理:
  - /hooks (直接使用官方管理)
```

## 版本兼容

### 官方更新策略
当官方指令更新时：
1. 自动继承新功能（因为我们调用官方指令）
2. 评估是否需要调整增强逻辑
3. 保持 VibeCoding 增强的独立性

### 降级策略
若官方指令不可用：
1. 输出警告信息
2. 尝试使用 VibeCoding 内置能力
3. 记录到 errors.md
