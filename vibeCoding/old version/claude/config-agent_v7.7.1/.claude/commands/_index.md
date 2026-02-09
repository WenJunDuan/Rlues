# 指令索引 (v7.7.1)

## 设计原则
**VibeCoding 指令 = 官方指令 + 增强能力**

自定义指令不替代官方指令，而是在调用官方指令的基础上叠加：
- 知识库检索 (knowledge-base)
- 经验库检索 (experience)
- MCP 工具调用
- Workflow 执行
- Skills 加载

## 指令分类

### 🔷 增强官方指令
这些指令**先调用官方指令**，再叠加增强：

| VibeCoding | 官方基础 | 增强内容 |
|:---|:---|:---|
| `vibe-init` | `/init` | + .ai_state + 知识库 |
| `vibe-plan` | `/plan` | + KB + EXP + 九步流程 |
| `vibe-todos` | `/todos` | + Kanban + 进度追踪 |
| `vibe-review` | `/review` | + 规范检索 + 质量检查 |
| `vibe-status` | `/status` | + 任务状态 + 流程进度 |
| `vibe-resume` | `/resume` | + .ai_state 恢复 |
| `vibe-agents` | `/agents` | + 功能导向配置 |

### 🔶 纯自定义指令
全新指令，无官方对应：

| 指令 | 用途 |
|:---|:---|
| `vibe-dev` | 需求研发入口（智能路由）|
| `vibe-service` | 服务上下文加载 |
| `vibe-exp` | 经验库操作 |
| `vibe-kb` | 知识库操作 |
| `vibe-pause` | 暂停工作流 |
| `vibe-abort` | 中止工作流 |

### ⚪ 直接使用官方
无需增强，直接使用：

```
/config    /permissions   /model      /plugin
/cost      /context       /stats      /usage
/clear     /compact       /rewind     /doctor
/mcp       /hooks         /help       /sandbox
```

---

## 增强指令详情

### vibe-init
```yaml
基于: /init
增强:
  - 调用官方 /init 创建 CLAUDE.md
  - 创建 .ai_state/ 目录结构
  - 初始化 .knowledge/ 知识库 (可选)
  - 创建 session.lock

语法: vibe-init [项目名]
```

### vibe-plan
```yaml
基于: /plan
增强:
  - 调用官方 /plan 进入计划模式
  - 检索知识库 (项目背景、规范)
  - 检索经验库 (类似任务经验)
  - 加载 riper/plan skill
  - 生成增强 TODO.md
  - 更新 .ai_state/meta/kanban.md

语法: vibe-plan [任务描述]
寸止: [PLAN_READY]
```

### vibe-todos
```yaml
基于: /todos
增强:
  - 调用官方 /todos 显示列表
  - 显示 Kanban 视图
  - 显示任务进度百分比
  - 显示关联的需求/设计文档
  - 支持按阶段过滤

语法: vibe-todos [--phase=<阶段>]
```

### vibe-review
```yaml
基于: /review
增强:
  - 调用官方 /review 代码审查
  - 检索知识库 (审查清单、代码规范)
  - 检索经验库 (常见问题、陷阱)
  - 加载 riper/review skill
  - 加载 code-quality skill
  - 执行 Linus 品味检查
  - 沉淀审查经验

语法: vibe-review [文件路径]
```

### vibe-status
```yaml
基于: /status
增强:
  - 调用官方 /status 显示系统状态
  - 显示当前任务状态
  - 显示九步流程进度
  - 显示知识库/经验库状态
  - 显示 MCP 工具连接状态

语法: vibe-status
```

### vibe-resume
```yaml
基于: /resume
增强:
  - 调用官方 /resume 恢复会话
  - 恢复 .ai_state/ 上下文
  - 重建任务状态
  - 加载相关知识和经验
  - 继续未完成的流程

语法: vibe-resume [session-id]
```

### vibe-agents
```yaml
基于: /agents
增强:
  - 调用官方 /agents 管理子代理
  - 配置 VibeCoding 功能导向代理
  - 设置 phase-router 路由规则
  - 管理代理间协作

语法: vibe-agents [list|add|remove|config]
```

---

## 纯自定义指令详情

### vibe-dev
```yaml
用途: 需求研发主入口
特点: 智能路由，自动选择流程

语法: 
  vibe-dev <任务描述>      # 新建
  vibe-dev <任务ID>        # 继续
  vibe-dev --path=A|B|C    # 指定路径

流程:
  1. phase-router 意图识别
  2. 路由到对应 Agent
  3. 自动检索知识库/经验库
  4. 执行九步工作流
```

### vibe-service
```yaml
用途: 服务上下文加载

语法:
  vibe-service load <name>      # 加载服务
  vibe-service analyze <name>   # 分析服务
  vibe-service init <name>      # 初始化文档

触发: service-analysis skill
```

### vibe-exp
```yaml
用途: 经验库操作

语法:
  vibe-exp search <关键词>   # 搜索经验
  vibe-exp deposit           # 沉淀经验
  vibe-exp show <ID>         # 查看经验
  vibe-exp list              # 列出经验

触发: experience skill
```

### vibe-kb
```yaml
用途: 知识库操作

语法:
  vibe-kb load <path>        # 加载知识
  vibe-kb search <关键词>    # 搜索知识
  vibe-kb list               # 列出知识

触发: knowledge-base skill
```

### vibe-pause / vibe-abort
```yaml
用途: 流程控制

vibe-pause: 暂停当前工作流
vibe-abort: 中止当前工作流

状态保存到: .ai_state/meta/session.lock
```

---

## 调用示例

### 计划任务 (增强官方)
```bash
# 用户输入
vibe-plan "添加用户搜索功能"

# 实际执行
1. → /plan                    # 调用官方
2. → knowledge-base skill     # 检索知识
3. → experience skill         # 检索经验
4. → riper/plan skill         # 增强计划
5. → 更新 .ai_state/          # 状态同步
6. → [PLAN_READY]             # 寸止等待
```

### 代码审查 (增强官方)
```bash
# 用户输入
vibe-review

# 实际执行
1. → /review                  # 调用官方
2. → knowledge-base skill     # 审查规范
3. → experience skill         # 常见问题
4. → code-quality skill       # 质量检查
5. → riper/review skill       # 增强审查
6. → experience deposit       # 沉淀经验
```

### 需求开发 (纯自定义)
```bash
# 用户输入
vibe-dev "实现登录功能"

# 实际执行
1. → phase-router             # 意图识别
2. → requirement-mgr          # 需求管理
3. → knowledge-base + experience # 检索
4. → 九步工作流               # 流程执行
```
