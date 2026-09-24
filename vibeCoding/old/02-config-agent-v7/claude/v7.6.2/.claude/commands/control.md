# 控制指令

## 概述
控制指令用于管理工作流状态：暂停、恢复、中止、查看状态。

---

## /vibe-status

### 用途
查看当前工作流状态

### 语法
```bash
/vibe-status
```

### 输出示例
```markdown
## 工作流状态

### 会话
- ID: abc-123
- 引擎: claude
- 开始: 2025-01-01 10:00

### 当前任务
添加用户设置页面

### 进度
- 路径: Path B
- 阶段: Execute
- 进度: 3/5 任务完成

### Kanban
- TODO: 2
- DOING: 0
- DONE: 3

### 下一步
继续执行剩余任务
```

### 无任务时
```markdown
## 工作流状态

### 状态
空闲，无进行中的任务

### 建议
使用 `/vibe-code <描述>` 开始新任务
```

---

## /vibe-pause

### 用途
暂停当前工作流

### 语法
```bash
/vibe-pause [原因]
```

### 执行流程
```yaml
1. 保存当前状态
   - 更新 session.lock
   - 更新 active_context.md
   - 保存 DOING 任务位置

2. 标记暂停
   - session.lock.status = "paused"
   - 记录暂停时间

3. 输出确认
```

### 输出示例
```markdown
## 工作流已暂停

### 暂停时间
2025-01-01 10:30

### 当前进度
- 阶段: Execute
- 任务: 3/5 完成
- DOING: [components/Settings.tsx]

### 恢复方式
使用 `/vibe-resume` 继续
```

---

## /vibe-resume

### 用途
恢复暂停的工作流

### 语法
```bash
/vibe-resume
```

### 执行流程
```yaml
1. 检查状态
   - session.lock 存在
   - status = "paused"

2. 恢复上下文
   - 读取 active_context.md
   - 加载 kanban.md
   - 识别 DOING 任务

3. 继续执行
   - 从暂停点继续
   - 更新 status = "running"
```

### 输出示例
```markdown
## 工作流已恢复

### 恢复时间
2025-01-01 11:00

### 继续任务
[components/Settings.tsx] 创建设置组件

### 剩余工作
- 当前任务: 1
- 待完成: 2

### 继续执行...
```

### 无暂停任务时
```markdown
## 无法恢复

### 原因
没有暂停的工作流

### 建议
使用 `/vibe-code <描述>` 开始新任务
```

---

## /vibe-abort

### 用途
中止当前工作流

### 语法
```bash
/vibe-abort [--force]
```

### 参数
| 参数 | 说明 |
|:---|:---|
| --force | 跳过确认直接中止 |

### 执行流程
```yaml
1. 确认中止 (除非 --force)
   - 显示当前进度
   - 警告数据可能丢失
   - 等待用户确认

2. 清理状态
   - 删除 session.lock
   - 保留 TODO.md 和 kanban.md (供参考)
   - 记录中止原因到 errors.md

3. 输出确认
```

### 确认提示
```markdown
## 确认中止？

### 当前进度
- 任务: 添加用户设置页面
- 完成: 3/5
- 未完成工作将丢失

### 选项
1. 确认中止
2. 取消
3. 先暂停 (/vibe-pause)
```

### 中止后输出
```markdown
## 工作流已中止

### 中止时间
2025-01-01 10:45

### 已完成工作
- [x] task1
- [x] task2
- [x] task3

### 未完成
- [ ] task4
- [ ] task5

### 状态文件
- TODO.md: 已保留
- kanban.md: 已保留
- session.lock: 已删除

### 下一步
使用 `/vibe-code` 开始新任务
```

---

## 状态流转图
```
         /vibe-code
              ↓
    ┌─────────────────┐
    │     running     │
    └────────┬────────┘
             │
    /vibe-pause│    /vibe-abort
             ↓         ↓
    ┌─────────────┐  ┌──────┐
    │   paused    │  │ idle │
    └──────┬──────┘  └──────┘
           │
    /vibe-resume
           ↓
    ┌─────────────────┐
    │     running     │
    └─────────────────┘
```
