---
name: vibe-abort
description: 终止当前工作流
---

# /vibe-abort - 终止工作流

终止当前正在执行或暂停的工作流，保留已完成的进度。

## 触发

```bash
/vibe-abort
```

## 执行动作

### 1. 确认终止

调用寸止确认：

```markdown
## ⚠️ 确认终止

即将终止工作流: vibe-code

### 当前进度
- 已完成: 2/5 任务
- 进行中: T-003

### 后果
- 工作流将结束
- 已完成的任务会保留
- 进行中的任务会标记为中止

---
确认终止？`确认` | `取消`
```

### 2. 用户确认后

#### 保存进度

```markdown
# active_context.md

## 状态
工作流已中止于 2025-01-12T10:30:00Z

## 已完成
- [x] T-001: 数据模型
- [x] T-002: 接口定义

## 已中止
- [~] T-003: 登录API (进度60%)

## 未开始
- [ ] T-004: 前端页面
- [ ] T-005: 测试
```

#### 清理锁

```bash
rm workflow.lock
rm checkpoint.md
```

#### 更新状态

```yaml
# session.yaml
mode:
  type: conversation

workflow:
  status: aborted
  aborted_at: "..."
```

### 3. 输出确认

```markdown
## ⛔ 工作流已终止

### 进度保留
- ✅ T-001: 数据模型
- ✅ T-002: 接口定义
- ⛔ T-003: 登录API (已中止)

### 状态
已保存到 active_context.md

### 后续操作
- `/vibe-plan` - 开始新规划
- `/vibe-state` - 查看状态
```

## 取消终止

如果用户选择 `取消`，返回继续执行。
