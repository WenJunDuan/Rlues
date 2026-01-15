# /vibe-init

## 用途
初始化 VibeCoding 项目环境

## 语法
```bash
/vibe-init [项目名]
```

## 执行流程

### 1. 创建目录结构
```bash
mkdir -p .ai_state
```

### 2. 初始化状态文件
```yaml
创建文件:
  - session.lock: 会话锁
  - active_context.md: 当前上下文
  - TODO.md: 任务列表
  - kanban.md: 看板
  - errors.md: 错误记录
```

### 3. 连接 MCP
```yaml
检查:
  - memory MCP 可用性
  - 其他 MCP 工具

若可用:
  - 创建项目知识空间
  - 加载历史上下文
```

### 4. 输出确认
```markdown
## VibeCoding 初始化完成

### 项目
[项目名]

### 状态目录
.ai_state/ ✓

### MCP 状态
- memory: ✓ 已连接
- sequential-thinking: ✓ 可用
- sou: ⚠ 未配置

### 下一步
使用 `/vibe-code <描述>` 开始开发
```

## 文件模板

### session.lock
```json
{
  "session_id": "<uuid>",
  "project": "<项目名>",
  "started_at": "<timestamp>",
  "ai_engine": "claude",
  "status": "idle"
}
```

### active_context.md
```markdown
# 当前上下文

## 项目
[项目名]

## 状态
初始化完成，等待任务

## 最近操作
- [timestamp] 项目初始化
```

### TODO.md
```markdown
# TODO

> 使用 `/vibe-code` 或 `/vibe-plan` 生成任务
```

### kanban.md
```markdown
# Kanban

### TODO

### DOING

### DONE
```

### errors.md
```markdown
# 错误记录

> 自动记录开发过程中的错误和教训
```

## 重复初始化
```yaml
若 .ai_state/ 已存在:
  1. 提示已初始化
  2. 询问是否重置
  3. 用户确认后清理重建
```

## 示例
```bash
# 初始化新项目
/vibe-init my-app

# 输出
## VibeCoding 初始化完成

### 项目
my-app

### 状态目录
.ai_state/ ✓

### 下一步
使用 `/vibe-code <描述>` 开始开发
```
