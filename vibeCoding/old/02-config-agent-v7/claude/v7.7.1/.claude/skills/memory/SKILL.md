# 双轨记忆系统

## 架构
```
┌─────────────────────────────────────────┐
│            双轨记忆系统                   │
├──────────────────┬──────────────────────┤
│   Memory MCP     │    .ai_state/        │
│   (云端持久)      │    (本地文件)         │
├──────────────────┼──────────────────────┤
│ • 跨项目知识      │ • 项目状态            │
│ • 长期经验        │ • 会话上下文          │
│ • 技术决策        │ • TODO/kanban        │
│ • 用户偏好        │ • 错误记录            │
└──────────────────┴──────────────────────┘
```

## Memory MCP 使用

### 存储知识
```javascript
memory_store({
  category: "技术决策",
  title: "认证系统设计",
  content: `
    选择 JWT + Redis 方案
    原因: 支持分布式、可快速撤销
    注意: token 过期时间设置...
  `,
  tags: ["auth", "jwt", "architecture"]
})
```

### 查询知识
```javascript
memory_search({
  query: "认证相关的设计决策",
  category: "技术决策",  // 可选
  limit: 5
})
```

### 更新知识
```javascript
memory_update({
  id: "knowledge_id",
  content: "更新后的内容..."
})
```

## .ai_state/ 文件系统

### 目录结构
```
.ai_state/
├── session.lock        # 会话锁
├── active_context.md   # 当前上下文
├── TODO.md             # 任务列表
├── kanban.md           # 看板状态
├── errors.md           # 错误记录
├── knowledge.md        # 本地知识 (降级存储)
└── handoff.md          # AI 交接文档
```

### session.lock
```json
{
  "session_id": "uuid",
  "started_at": "2025-01-01T00:00:00Z",
  "ai_engine": "claude",
  "current_phase": "Execute",
  "current_task": "task_id"
}
```

### active_context.md
```markdown
# 当前上下文

## 任务
[当前任务描述]

## 进度
- 阶段: Execute
- 完成: 3/5

## 关键信息
- [重要上下文1]
- [重要上下文2]

## 最近决策
- [决策1]
- [决策2]
```

### errors.md
```markdown
# 错误记录

## 2025-01-01 10:30
**任务**: 修改 auth.ts
**错误**: TypeError: undefined is not a function
**根因**: 未检查返回值
**解决**: 添加空值检查
**教训**: 总是检查异步函数返回值
```

### knowledge.md (Memory MCP 降级)
```markdown
# 本地知识库

## 技术决策
### 认证系统
- 方案: JWT + Redis
- 原因: ...

## 经验教训
### 错误处理
- 总是检查异步返回值
- ...
```

## 同步策略

### 优先级
```yaml
读取:
  1. Memory MCP (优先，最新)
  2. .ai_state/ (降级，本地)

写入:
  1. 同时写入两处 (若可能)
  2. 仅 Memory MCP (跨项目知识)
  3. 仅 .ai_state/ (项目特定)
```

### 场景判断
```yaml
跨项目通用:
  存储: Memory MCP
  示例: 技术最佳实践、通用设计模式

项目特定:
  存储: .ai_state/
  示例: TODO、kanban、当前任务状态

两者都需要:
  存储: 都写
  示例: 重要决策（Memory持久化 + 本地快速访问）
```

## 会话恢复

### onSessionStart 流程
```yaml
1. 检查 session.lock
   - 存在 → 恢复会话
   - 不存在 → 新建会话

2. 读取 active_context.md
   - 获取上次状态
   - 识别待续任务

3. 查询 Memory MCP
   - 获取相关知识
   - 加载历史决策

4. 加载 kanban.md
   - 识别 DOING 任务
   - 继续执行
```

### 恢复示例
```javascript
async function restoreSession() {
  // 检查 session.lock
  const lock = await readFile('.ai_state/session.lock');
  if (lock) {
    console.log('恢复会话:', lock.session_id);
    
    // 读取上下文
    const context = await readFile('.ai_state/active_context.md');
    
    // 查询相关知识
    const knowledge = await memory_search({
      query: context.task,
      limit: 3
    });
    
    // 继续任务
    return { context, knowledge, resumeFrom: lock.current_task };
  }
  
  return null;
}
```

## 清理策略

### 任务完成后
```yaml
保留:
  - Memory MCP 中的知识
  - errors.md 中的教训
  
清理:
  - session.lock
  - 可选: 归档 TODO.md 和 kanban.md
```

### 会话中断
```yaml
保留所有文件，等待恢复:
  - session.lock 标记未完成
  - active_context.md 保留最新状态
  - kanban.md 保留 DOING 状态
```
