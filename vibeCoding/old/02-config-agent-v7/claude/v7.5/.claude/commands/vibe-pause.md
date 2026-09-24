---
name: vibe-pause
description: 暂停当前工作流，保存断点
---

# /vibe-pause - 暂停工作流

暂停当前正在执行的工作流，保存断点以便后续恢复。

## 触发

```bash
/vibe-pause
```

## 执行动作

### 1. 保存断点

创建 `checkpoint.md`:

```markdown
# 断点信息

## 暂停时间
2025-01-12T10:30:00Z

## 工作流
- 名称: vibe-code
- 阶段: Execute (E)
- 步骤: 4.3

## 当前任务
- ID: T-003
- 描述: 实现登录API
- 进度: 60%

## 当前文件
- 路径: src/api/auth.ts
- 行号: 45
- 动作: 实现密码验证

## 待继续
1. 完成密码验证逻辑
2. 添加错误处理
3. 编写单元测试

## 恢复指令
/vibe-resume
```

### 2. 更新状态

```yaml
# session.yaml
mode:
  type: paused

workflow:
  status: paused
```

### 3. 释放锁

```yaml
# workflow.lock
locked: false
paused: true
paused_at: "..."
```

### 4. 输出确认

```markdown
## ⏸️ 工作流已暂停

### 断点位置
- **阶段**: Execute (E)
- **任务**: T-003 实现登录API
- **进度**: 60%

### 已保存
- 断点信息: checkpoint.md
- 会话状态: session.yaml

### 恢复方式
- `/vibe-resume` - 继续执行
- `/vibe-state` - 查看详情
- `/vibe-abort` - 终止工作流
```

## 注意

- 暂停后可以进行其他对话
- 下次启动时会提示有暂停的工作流
- 使用 `/vibe-resume` 恢复
