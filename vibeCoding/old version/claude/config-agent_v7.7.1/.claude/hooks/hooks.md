# 生命周期钩子

## 概述
钩子函数在工作流特定时机自动触发，用于状态管理、验证和学习。

## 钩子列表

| 钩子 | 触发时机 | 用途 |
|:---|:---|:---|
| onSessionStart | 会话开始 | 初始化/恢复状态 |
| beforeTask | 任务开始前 | 前置检查 |
| afterTask | 任务完成后 | 状态更新 |
| onError | 发生错误时 | 错误处理 |
| onUserCorrection | 用户纠正时 | 学习记录 |
| onComplete | 工作流完成 | 调用寸止 |
| afterComplete | 寸止确认后 | 清理归档 |

---

## onSessionStart

### 触发时机
每次会话开始时

### 执行逻辑
```yaml
1. 检查 session.lock
   存在且 status=running:
     - 提示有未完成任务
     - 建议 /vibe-resume
   存在且 status=paused:
     - 询问是否恢复
   不存在:
     - 正常开始新会话

2. 加载上下文
   - 读取 active_context.md
   - 读取 kanban.md
   - 查询 Memory MCP

3. 初始化环境
   - 检查 MCP 可用性
   - 加载必要技能
```

### 代码示例
```javascript
async function onSessionStart() {
  const lock = await readFile('.ai_state/session.lock');
  
  if (lock) {
    if (lock.status === 'running') {
      return { action: 'prompt_resume', context: lock };
    }
    if (lock.status === 'paused') {
      return { action: 'ask_resume', context: lock };
    }
  }
  
  // 新会话
  const context = await readFile('.ai_state/active_context.md');
  const memory = await memory_search({ query: 'recent project context' });
  
  return { action: 'start_new', context, memory };
}
```

---

## beforeTask

### 触发时机
每个任务开始执行前

### 执行逻辑
```yaml
1. 检查依赖
   - 前置任务是否完成
   - 依赖文件是否存在

2. 检查禁止行为
   - 读取 errors.md 中的 forbidden_action
   - 若匹配则警告

3. 更新状态
   - kanban: TODO → DOING
   - session.lock: current_task
```

### 代码示例
```javascript
async function beforeTask(task) {
  // 检查依赖
  if (task.depends) {
    const kanban = await readKanban();
    for (const dep of task.depends) {
      if (!kanban.done.includes(dep)) {
        throw new Error(`依赖未完成: ${dep}`);
      }
    }
  }
  
  // 检查禁止行为
  const errors = await readFile('.ai_state/errors.md');
  const forbidden = extractForbiddenActions(errors);
  if (forbidden.some(f => task.matches(f))) {
    console.warn('警告: 此操作曾导致错误');
  }
  
  // 更新 kanban
  await moveToTaking(task.id);
}
```

---

## afterTask

### 触发时机
每个任务完成后

### 执行逻辑
```yaml
1. 更新状态
   - kanban: DOING → DONE
   - TODO.md: 打勾
   - active_context.md: 更新进度

2. 验证结果
   - 检查文件是否修改
   - 运行相关测试

3. 经验沉淀
   - 记录有价值的发现到 Memory
```

### 代码示例
```javascript
async function afterTask(task, result) {
  // 更新状态
  await moveToDone(task.id);
  await updateTodo(task.id, 'done');
  await updateContext({ lastTask: task.id, progress: getProgress() });
  
  // 验证
  if (result.files) {
    for (const file of result.files) {
      const exists = await fileExists(file);
      if (!exists) throw new Error(`文件未创建: ${file}`);
    }
  }
  
  // 经验沉淀
  if (result.learning) {
    await memory_store({
      category: 'task_learning',
      content: result.learning
    });
  }
}
```

---

## onError

### 触发时机
执行过程中发生错误

### 执行逻辑
```yaml
1. 记录错误
   - 写入 errors.md
   - 包含时间、任务、错误、上下文

2. 分析根因
   - 尝试识别错误类型
   - 提取可泛化的教训

3. 决定处理方式
   - 可重试 → 自动重试
   - 需介入 → 触发 [VERIFICATION_FAILED]
```

### 代码示例
```javascript
async function onError(error, context) {
  // 记录错误
  await appendToErrors({
    timestamp: new Date().toISOString(),
    task: context.task,
    error: error.message,
    stack: error.stack,
    context: context
  });
  
  // 分析
  const analysis = analyzeError(error);
  
  // 决定处理
  if (analysis.retryable && context.retryCount < 3) {
    return { action: 'retry', delay: 1000 };
  }
  
  // 需要用户介入
  return { 
    action: 'pause',
    token: 'VERIFICATION_FAILED',
    summary: {
      error: error.message,
      analysis: analysis.cause,
      suggestions: analysis.suggestions
    }
  };
}
```

---

## onUserCorrection

### 触发时机
用户指出错误或纠正行为

### 执行逻辑
```yaml
1. 记录纠正
   - 写入 errors.md
   - 标记为 forbidden_action

2. 学习更新
   - 存入 Memory MCP
   - 标记为高优先级

3. 调整行为
   - 立即应用纠正
   - 避免重复错误
```

### 代码示例
```javascript
async function onUserCorrection(correction) {
  // 记录
  await appendToErrors({
    type: 'user_correction',
    timestamp: new Date().toISOString(),
    correction: correction.content,
    forbidden_action: correction.action,
    reason: correction.reason
  });
  
  // 学习
  await memory_store({
    category: 'forbidden_action',
    title: correction.action,
    content: correction.reason,
    tags: ['correction', 'high_priority']
  });
  
  // 确认
  return { acknowledged: true, willAvoid: correction.action };
}
```

---

## onComplete

### 触发时机
所有任务完成，准备结束

### 执行逻辑
```yaml
1. 最终验证
   - 检查所有 TODO 完成
   - 运行完整测试

2. 生成摘要
   - 完成情况统计
   - 关键成果

3. 触发寸止
   - [TASK_DONE] 或 [PHASE_DONE]
   - 等待用户确认
```

### 代码示例
```javascript
async function onComplete(workflow) {
  // 验证
  const kanban = await readKanban();
  if (kanban.todo.length > 0 || kanban.doing.length > 0) {
    throw new Error('还有未完成任务');
  }
  
  // 生成摘要
  const summary = {
    tasks: kanban.done.length,
    files: workflow.modifiedFiles,
    duration: workflow.duration
  };
  
  // 寸止
  return {
    action: 'cunzhi',
    token: 'TASK_DONE',
    summary: summary
  };
}
```

---

## afterComplete

### 触发时机
用户确认完成后

### 执行逻辑
```yaml
1. 归档状态
   - 可选: 移动 TODO.md 到 archive/
   - 清理 DOING 状态

2. 清理锁
   - 删除 session.lock

3. 经验沉淀
   - 项目经验存入 Memory
```

### 代码示例
```javascript
async function afterComplete(confirmation) {
  if (confirmation.archive) {
    await archiveTodo();
  }
  
  // 清理
  await deleteFile('.ai_state/session.lock');
  
  // 经验沉淀
  await memory_store({
    category: 'project_completion',
    title: confirmation.project,
    content: confirmation.summary,
    tags: ['completed', confirmation.project]
  });
  
  return { status: 'idle', message: '任务完成' };
}
```
