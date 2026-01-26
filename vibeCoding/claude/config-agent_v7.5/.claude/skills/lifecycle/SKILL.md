---
name: lifecycle
description: 指令生命周期管理，钩子函数，中断恢复，持续学习
trigger: 所有工作流指令
priority: high
---

# Lifecycle Skill

> **核心问题**: 指令如何持续运行、中断、恢复？
> **解决方案**: 生命周期状态机 + 钩子函数 + 持续监控

---

## 🔄 指令生命周期状态机

```
                    ┌─────────────────────────────────────────┐
                    │           指令生命周期状态机             │
                    └─────────────────────────────────────────┘

    /vibe-xxx ──▶ [INIT] ──▶ [RUNNING] ──▶ [COMPLETED]
                    │            │              │
                    │            │              └──▶ onComplete()
                    │            │
                    │            ├──▶ [PAUSED] ◀── /vibe-pause
                    │            │       │
                    │            │       └──▶ [RUNNING] ◀── /vibe-resume
                    │            │
                    │            └──▶ [FAILED] ◀── 错误发生
                    │                    │
                    │                    └──▶ onError()
                    │
                    └──▶ onInit()

    状态: INIT → RUNNING → PAUSED → RUNNING → COMPLETED
                    ↓
                  FAILED
```

---

## 🎣 钩子函数定义

### 完整钩子列表

```typescript
interface LifecycleHooks {
  // ====== 初始化阶段 ======
  onInit(): Promise<void>;           // 指令开始时
  onContextLoad(): Promise<void>;    // 加载上下文后
  onMemoryLoad(): Promise<void>;     // 加载Memory后
  
  // ====== 执行阶段 ======
  onPhaseEnter(phase: string): Promise<void>;   // 进入新阶段
  onPhaseExit(phase: string): Promise<void>;    // 离开阶段
  onTaskStart(taskId: string): Promise<void>;   // 任务开始
  onTaskComplete(taskId: string): Promise<void>;// 任务完成
  onTodoUpdate(): Promise<void>;                // TODO状态更新
  
  // ====== 中断恢复 ======
  onPause(): Promise<void>;          // 暂停时
  onResume(): Promise<void>;         // 恢复时
  onCheckpoint(): Promise<void>;     // 保存断点时
  
  // ====== 结束阶段 ======
  onBeforeComplete(): Promise<void>; // 完成前（寸止确认）
  onComplete(): Promise<void>;       // 完成后
  onError(error: Error): Promise<void>; // 错误发生时
  
  // ====== 持续监控 ======
  onDocChange(file: string): Promise<void>;  // 文档变化时
  onLearn(lesson: string): Promise<void>;    // 学习新知识时
}
```

### 钩子执行时机

```
┌─────────────────────────────────────────────────────────────┐
│                    钩子执行流程                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  /vibe-code "实现登录"                                      │
│       │                                                     │
│       ▼                                                     │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ onInit()                                             │   │
│  │ - 创建 workflow.lock                                │   │
│  │ - 初始化 session.yaml                               │   │
│  │ - 记录开始时间                                       │   │
│  └─────────────────────────────────────────────────────┘   │
│       │                                                     │
│       ▼                                                     │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ onContextLoad()                                      │   │
│  │ - 读取 active_context.md                            │   │
│  │ - 读取 kanban.md                                    │   │
│  │ - 检查未完成任务                                     │   │
│  └─────────────────────────────────────────────────────┘   │
│       │                                                     │
│       ▼                                                     │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ onMemoryLoad()                                       │   │
│  │ - 加载 user_preference                              │   │
│  │ - 加载 forbidden_action                             │   │
│  │ - 加载 code_pattern                                 │   │
│  └─────────────────────────────────────────────────────┘   │
│       │                                                     │
│       ▼                                                     │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ onPhaseEnter("R1")                                   │   │
│  │ - 更新 session.yaml.phase                           │   │
│  │ - 加载阶段所需技能                                   │   │
│  └─────────────────────────────────────────────────────┘   │
│       │                                                     │
│       ▼                                                     │
│     ... (执行阶段) ...                                      │
│       │                                                     │
│       ▼                                                     │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ onTaskComplete("T-001")                              │   │
│  │ - 更新 active_context.md                            │   │
│  │ - 更新 kanban.md (移动到已完成)                     │   │
│  │ - 触发 onTodoUpdate()                               │   │
│  └─────────────────────────────────────────────────────┘   │
│       │                                                     │
│       ▼                                                     │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ onBeforeComplete()                                   │   │
│  │ - 生成完成报告                                       │   │
│  │ - 调用寸止确认                                       │   │
│  │ - 等待用户响应                                       │   │
│  └─────────────────────────────────────────────────────┘   │
│       │                                                     │
│       ▼                                                     │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ onComplete()                                         │   │
│  │ - 删除 workflow.lock                                │   │
│  │ - 更新 session.yaml (completed)                     │   │
│  │ - 沉淀学习到 Memory                                 │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## ⏸️ 中断和恢复机制

### 中断指令: /vibe-pause

```javascript
async function handlePause() {
  // 1. 触发 onPause 钩子
  await hooks.onPause();
  
  // 2. 保存当前状态
  await hooks.onCheckpoint();
  
  // 3. 更新状态文件
  await updateSession({
    mode: { type: 'paused' },
    workflow: { status: 'paused' }
  });
  
  // 4. 释放锁但标记暂停
  await updateLock({ locked: false, paused: true });
  
  // 5. 输出暂停确认
  output(`
## ⏸️ 工作流已暂停

### 断点位置
- 阶段: ${currentPhase}
- 任务: ${currentTask}
- 进度: ${completedTasks}/${totalTasks}

### 恢复方式
- 输入 \`/vibe-resume\` 继续
- 输入 \`/vibe-state\` 查看详情
- 输入 \`/vibe-abort\` 放弃当前工作流
  `);
}
```

### 恢复指令: /vibe-resume

```javascript
async function handleResume() {
  // 1. 读取断点信息
  const checkpoint = await readCheckpoint();
  const session = await readSession();
  
  // 2. 触发 onResume 钩子
  await hooks.onResume();
  
  // 3. 恢复锁定
  await enterWorkflow(session.mode.workflow_name);
  
  // 4. 恢复到断点
  await restoreToCheckpoint(checkpoint);
  
  // 5. 输出恢复信息并继续
  output(`
## ▶️ 工作流已恢复

### 恢复位置
- 阶段: ${checkpoint.phase}
- 任务: ${checkpoint.task}

### 继续执行
${checkpoint.next_action}
  `);
  
  // 6. 继续执行
  await continueExecution();
}
```

### 强制终止: /vibe-abort

```javascript
async function handleAbort() {
  // 1. 确认终止
  const confirmed = await cunzhi.ask({
    question: "确定要终止当前工作流吗？进度将被保留但工作流会结束。",
    options: ["确认终止", "继续执行"]
  });
  
  if (confirmed !== "确认终止") return;
  
  // 2. 保存当前进度
  await saveProgress();
  
  // 3. 清理锁
  await releaseLock();
  
  // 4. 更新状态
  await updateSession({
    mode: { type: 'conversation' },
    workflow: { status: 'aborted' }
  });
}
```

---

## 📚 持续学习机制

### 文档监控

```javascript
// 持续监控项目文档变化
async function watchDocs() {
  const docsToWatch = [
    'project_document/.ai_state/conventions.md',
    'project_document/.ai_state/decisions.md',
    'README.md',
    'CONTRIBUTING.md'
  ];
  
  for (const doc of docsToWatch) {
    if (await hasChanged(doc)) {
      await hooks.onDocChange(doc);
      await learnFromDoc(doc);
    }
  }
}

async function learnFromDoc(docPath) {
  const content = await readFile(docPath);
  const learnings = extractLearnings(content);
  
  for (const lesson of learnings) {
    await memory.add({
      category: 'project_knowledge',
      content: lesson,
      source: docPath
    });
    await hooks.onLearn(lesson);
  }
}
```

### 周期性检查

```javascript
// 每个阶段结束时检查
async function onPhaseExit(phase) {
  // 1. 检查项目文档更新
  await watchDocs();
  
  // 2. 检查是否有新的约定
  await checkConventions();
  
  // 3. 检查是否有未处理的决策
  await checkDecisions();
  
  // 4. 更新状态
  await updatePhaseStatus(phase, 'completed');
}
```

---

## 📋 状态同步规则

### 必须同步的时机

| 事件 | 同步内容 |
|:---|:---|
| 指令开始 | session.yaml, workflow.lock |
| 阶段切换 | session.yaml.phase |
| 任务开始 | kanban.md (移到进行中) |
| 任务完成 | kanban.md (移到已完成), active_context.md |
| 暂停 | checkpoint.md |
| 错误 | session.yaml.workflow.status |
| 完成 | 删除 workflow.lock |

### 同步代码模板

```javascript
async function syncState(event, data) {
  const timestamp = new Date().toISOString();
  
  switch (event) {
    case 'task_start':
      await updateKanban(data.taskId, 'doing');
      await updateSession({ workflow: { current_task: data.taskId } });
      break;
      
    case 'task_complete':
      await updateKanban(data.taskId, 'done');
      await updateActiveContext(data.taskId, 'completed');
      await updateSession({ 
        workflow: { completed_tasks: data.completed }
      });
      break;
      
    case 'phase_change':
      await updateSession({ mode: { phase: data.phase } });
      break;
  }
  
  // 始终更新时间戳
  await updateSession({ session: { updated_at: timestamp } });
}
```

---

## 🔗 钩子实现示例

```javascript
const lifecycleHooks = {
  async onInit() {
    console.log('[Lifecycle] 工作流初始化');
    await createLock();
    await initSession();
  },
  
  async onPhaseEnter(phase) {
    console.log(`[Lifecycle] 进入阶段: ${phase}`);
    await loadPhaseSkills(phase);
    await updateSession({ mode: { phase } });
  },
  
  async onTaskComplete(taskId) {
    console.log(`[Lifecycle] 任务完成: ${taskId}`);
    await syncState('task_complete', { taskId });
    await triggerTodoUpdate();
  },
  
  async onPause() {
    console.log('[Lifecycle] 工作流暂停');
    await saveCheckpoint();
  },
  
  async onResume() {
    console.log('[Lifecycle] 工作流恢复');
    await loadCheckpoint();
  },
  
  async onBeforeComplete() {
    console.log('[Lifecycle] 准备完成，调用寸止');
    await generateReport();
    await cunzhi.confirm();
  },
  
  async onComplete() {
    console.log('[Lifecycle] 工作流完成');
    await releaseLock();
    await archiveSession();
  },
  
  async onError(error) {
    console.log(`[Lifecycle] 错误: ${error.message}`);
    await saveErrorState(error);
    await notifyError(error);
  }
};
```

---

## ⚠️ 强制规则

1. **每个钩子都必须执行** — 不能跳过
2. **状态必须同步到文件** — 不依赖内存
3. **暂停必须保存断点** — 确保可恢复
4. **完成必须调用寸止** — 用户确认

---

**核心价值**: 指令可中断、可恢复、可追踪 | **触发**: 所有工作流 | **输出**: 状态文件
