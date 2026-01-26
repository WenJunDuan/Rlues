# Hooks (钩子函数)

> 钩子在特定时机自动触发，无需手动调用

---

## 钩子列表

| 钩子 | 触发时机 | 作用 |
|:---|:---|:---|
| `onSessionStart` | 会话开始 | 检查 session.lock，加载 Memory |
| `beforeTask` | 任务执行前 | 检查依赖，检查 forbidden_action |
| `afterTask` | 任务执行后 | 更新状态，学习沉淀 |
| `onError` | 发生错误 | 错误学习，请求介入 |
| `onUserCorrection` | 用户纠正 | 记录 forbidden_action |
| `beforeComplete` | 完成前 | 核对 TODO |
| `onComplete` | 完成时 | 调用寸止 |
| `afterComplete` | 完成后 | 归档，删除 session.lock |

---

## onSessionStart

```javascript
// 每次会话开始自动执行

async function onSessionStart() {
  // 1. 检查 session.lock
  const lock = await readFile('.ai_state/session.lock')
  
  if (lock && lock.mode === 'workflow') {
    // 有未完成工作流
    await showRecoveryOptions(lock)
    return
  }
  
  // 2. 加载 Memory
  await memory.recall({ category: 'user_preference' })
  await memory.recall({ category: 'forbidden_action' })
  await memory.recall({ category: 'code_pattern' })
  
  // 3. 读取项目状态
  await readProjectState()
  
  // 4. 汇报状态
  await reportStatus()
}
```

---

## beforeTask

```javascript
// 每个任务执行前自动执行

async function beforeTask(task) {
  // 1. 检查依赖
  for (const dep of task.dependencies) {
    if (!isCompleted(dep)) {
      throw new Error(`依赖任务 ${dep} 未完成`)
    }
  }
  
  // 2. 检查 forbidden_action
  const forbidden = await memory.recall({ category: 'forbidden_action' })
  for (const rule of forbidden) {
    if (task.violates(rule)) {
      throw new Error(`任务违反禁止规则: ${rule}`)
    }
  }
  
  // 3. 更新 kanban (TODO → DOING)
  await updateKanban(task.id, 'DOING')
}
```

---

## afterTask

```javascript
// 每个任务执行后自动执行

async function afterTask(task, result) {
  // 1. 更新 kanban (DOING → DONE)
  await updateKanban(task.id, 'DONE', {
    duration: result.duration,
    completedAt: new Date()
  })
  
  // 2. 更新 active_context.md
  await markTaskComplete(task.id)
  
  // 3. 学习沉淀
  if (result.newPattern) {
    await memory.add({
      category: 'code_pattern',
      content: result.newPattern
    })
  }
  
  if (result.lessonLearned) {
    await memory.add({
      category: 'lesson_learned',
      content: result.lessonLearned
    })
  }
}
```

---

## onError

```javascript
// 发生错误时自动执行

async function onError(error, context) {
  // 1. 记录错误
  console.error('Error:', error)
  
  // 2. 尝试自动恢复
  if (error.recoverable) {
    await attemptRecovery(error)
    return
  }
  
  // 3. 学习错误
  await memory.add({
    category: 'lesson_learned',
    content: `错误: ${error.message}, 上下文: ${context}`
  })
  
  // 4. 请求人工介入
  await cunzhi.pause({
    token: '[ERROR]',
    summary: '发生错误',
    content: error.message,
    options: ['重试', '跳过', '中止']
  })
}
```

---

## onUserCorrection

```javascript
// 用户纠正时自动执行

async function onUserCorrection(correction) {
  // 检测纠正信号
  const signals = ['不要', '别', '禁止', '以后别', '不许']
  
  if (signals.some(s => correction.includes(s))) {
    // 提取禁止行为
    const forbidden = extractForbiddenAction(correction)
    
    // 立即记录
    await memory.add({
      category: 'forbidden_action',
      content: forbidden,
      tags: ['user_correction']
    })
    
    // 确认
    console.log(`好的，我已记录：${forbidden}。以后会避免。`)
  }
}
```

---

## onComplete

```javascript
// 工作流完成时自动执行

async function onComplete(workflow) {
  // 1. 生成核对报告
  const report = await generateReviewReport(workflow)
  
  // 2. 调用寸止
  await cunzhi.pause({
    token: '[TASK_DONE]',
    summary: '工作流完成',
    content: report,
    options: ['通过', '问题', '优化']
  })
}
```

---

## afterComplete

```javascript
// 用户验收后自动执行

async function afterComplete(workflow, userResponse) {
  if (userResponse === '通过') {
    // 1. 删除 session.lock
    await deleteFile('.ai_state/session.lock')
    
    // 2. 归档（可选）
    await archiveWorkflow(workflow)
    
    // 3. 沉淀学习成果
    await saveLearnings(workflow)
  }
}
```
