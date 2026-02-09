---
name: vibe-resume
description: 恢复暂停的工作流
---

# /vibe-resume - 恢复工作流

恢复之前暂停的工作流，从断点继续执行。

## 触发

```bash
/vibe-resume
```

## 前置条件

- 存在 `checkpoint.md`
- `session.yaml.mode.type == 'paused'`

## 执行动作

### 1. 读取断点

```javascript
const checkpoint = await readFile('checkpoint.md');
const session = await readYaml('session.yaml');
```

### 2. 恢复锁定

```yaml
# workflow.lock
locked: true
workflow: "vibe-code"
resumed_at: "..."
```

### 3. 更新状态

```yaml
# session.yaml
mode:
  type: workflow
  workflow_name: "vibe-code"

workflow:
  status: running
```

### 4. 汇报并继续

```markdown
## ▶️ 工作流已恢复

### 恢复位置
- **工作流**: vibe-code
- **阶段**: Execute (E)
- **任务**: T-003 实现登录API

### 断点详情
- **文件**: src/api/auth.ts:45
- **进度**: 60%

### TODO 状态
- ✅ T-001: 数据模型
- ✅ T-002: 接口定义
- 🔄 T-003: 登录API (当前)
- ⏳ T-004: 前端页面
- ⏳ T-005: 测试

### 下一步
继续实现密码验证逻辑

---
正在继续执行...
```

### 5. 继续执行

自动继续执行未完成的任务。

## 无断点时

```markdown
## ⚠️ 无法恢复

未找到暂停的工作流。

### 可选操作
- `/vibe-state` - 查看当前状态
- `/vibe-plan` - 开始新的规划
```
