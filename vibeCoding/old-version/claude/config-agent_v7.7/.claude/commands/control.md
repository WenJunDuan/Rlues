# 控制指令

## /vibe-status
查看当前工作流状态。

```bash
/vibe-status
```

输出示例:
```markdown
## 工作流状态

### 会话
- ID: abc-123
- 开始: 2025-01-01 10:00

### 当前任务
- ID: REQ-001
- 标题: 添加用户登录功能
- 阶段: 开发实施 (步骤6)
- 进度: 3/5 任务完成

### 知识库
- 已加载: standards/code-style.md

### 经验
- 已检索: 3 条相关经验
```

---

## /vibe-pause
暂停当前工作流。

```bash
/vibe-pause [原因]
```

动作:
- 保存当前状态到 session.lock
- 更新 kanban.md
- 记录暂停原因

---

## /vibe-resume
恢复暂停的工作流。

```bash
/vibe-resume
```

动作:
- 读取 session.lock
- 恢复上下文
- 继续执行

---

## /vibe-abort
中止当前工作流。

```bash
/vibe-abort [--force]
```

动作:
- 确认中止 (除非 --force)
- 清理 session.lock
- 保留任务文档 (供参考)
- 可选: 沉淀中止原因到经验

---

## /vibe-service
加载服务上下文。

```bash
# 加载服务
/vibe-service load <service-name>

# 加载多个服务
/vibe-service load service-a service-b

# 分析服务
/vibe-service analyze <service-name>

# 初始化服务文档
/vibe-service init <service-name>
```

触发: service-analysis skill

---

## /vibe-exp
经验库操作。

```bash
# 搜索经验
/vibe-exp search <关键词>

# 沉淀经验
/vibe-exp deposit [--title=<标题>]

# 查看经验
/vibe-exp show <EXP-ID>

# 列出经验
/vibe-exp list [--type=<类型>]
```

触发: experience skill

---

## /vibe-kb
知识库操作。

```bash
# 加载知识
/vibe-kb load <path>

# 搜索知识
/vibe-kb search <关键词>

# 列出知识
/vibe-kb list [--category=<类别>]
```

触发: knowledge-base skill
