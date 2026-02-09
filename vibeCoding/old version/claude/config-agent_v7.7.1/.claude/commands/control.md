# 控制指令

---

## 🔷 增强官方指令

### vibe-status
**基于**: `/status`

显示增强的系统状态，包含任务进度和流程状态。

```bash
vibe-status
```

**执行流程**:
```
1. 调用官方 /status
   → 显示系统状态、版本、账户、连接性
   
2. VibeCoding 增强
   → 显示当前任务状态
   → 显示九步流程进度
   → 显示知识库/经验库状态
   → 显示 MCP 工具连接
```

**增强输出**:
```markdown
## 系统状态 (官方 /status)
[官方状态信息]

---

## VibeCoding 状态

### 当前任务
- ID: REQ-001
- 标题: 用户认证
- 阶段: 开发实施 (步骤6)
- 进度: 80%

### 九步流程
1. ✅ 需求创建
2. ✅ 需求审查 [REQ_READY]
3. ✅ 方案设计
4. ✅ 方案审查 [DESIGN_READY]
5. ⏭️ 环境搭建 (跳过)
6. 🔄 开发实施 ← 当前
7. ⬜ 代码提交
8. ⬜ 版本发布
9. ⬜ 完成归档

### 知识库
- 路径: .knowledge/
- 已加载: 3 个文档

### 经验库
- 条目: 12 条
- 本次检索: 3 条相关
```

---

### vibe-resume
**基于**: `/resume`

恢复会话并重建 VibeCoding 上下文。

```bash
vibe-resume [session-id]
```

**执行流程**:
```
1. 调用官方 /resume
   → 恢复对话会话
   
2. VibeCoding 增强
   → 读取 .ai_state/meta/session.lock
   → 恢复任务上下文
   → 重建 Kanban 状态
   → 加载相关知识和经验
```

**增强输出**:
```markdown
## 会话恢复

### 官方会话
[官方 /resume 结果]

### VibeCoding 上下文
- 任务: REQ-001 (用户认证)
- 阶段: 开发实施
- 进度: 4/5 完成
- 上次操作: 实现注册 API

### 自动加载
- 知识库: standards/code-style.md
- 经验: EXP-012, EXP-023

### 继续
从上次暂停点继续...
```

---

## 🔶 纯自定义指令

### vibe-pause
暂停当前工作流，保存状态。

```bash
vibe-pause [原因]
```

**执行**:
```yaml
动作:
  - 保存当前状态到 session.lock
  - 更新 kanban.md (DOING → 暂停)
  - 记录暂停时间和原因
  - 保存上下文到 active_context.md

输出:
  - 暂停确认
  - 当前进度摘要
  - 恢复方式提示
```

**示例输出**:
```markdown
## 工作流已暂停

### 暂停时间
2025-01-01 10:30

### 当前进度
- 任务: REQ-001
- 阶段: 开发实施
- 完成: 4/5

### 恢复方式
使用 `vibe-resume` 继续
```

---

### vibe-abort
中止当前工作流。

```bash
vibe-abort [--force]
```

**执行**:
```yaml
默认:
  - 显示当前进度
  - 警告数据影响
  - 等待确认

--force:
  - 跳过确认直接中止

动作:
  - 清理 session.lock
  - 保留任务文档 (供参考)
  - 沉淀中止原因 (可选)
```

**确认提示**:
```markdown
## 确认中止？

### 当前进度
- 任务: REQ-001
- 完成: 4/5
- 未完成工作将保留但标记为中止

### 选项
1. 确认中止
2. 取消
3. 先暂停 (vibe-pause)
```

---

### vibe-service
加载服务上下文。

```bash
vibe-service load <服务名>
vibe-service analyze <服务名>
vibe-service init <服务名>
```

**触发**: service-analysis skill

**详见**: commands/vibe-service.md

---

### vibe-exp
经验库操作。

```bash
vibe-exp search <关键词>
vibe-exp deposit [--title=<标题>]
vibe-exp show <EXP-ID>
vibe-exp list [--type=<类型>]
```

**触发**: experience skill

---

### vibe-kb
知识库操作。

```bash
vibe-kb load <path>
vibe-kb search <关键词>
vibe-kb list [--category=<类别>]
```

**触发**: knowledge-base skill

---

## ⚪ 直接使用官方

以下指令直接使用官方，无需 vibe 增强：

### 配置管理
```bash
/config          # 打开设置
/permissions     # 查看权限
/model           # 选择模型
/plugin          # 管理插件
/mcp             # 管理 MCP
/hooks           # 管理钩子
```

### 信息查看
```bash
/cost            # 令牌统计
/context         # 上下文使用
/stats           # 使用统计
/usage           # 计划限制
/help            # 获取帮助
```

### 系统操作
```bash
/clear           # 清除历史
/compact         # 压缩对话
/rewind          # 回退对话
/doctor          # 健康检查
/sandbox         # 沙箱模式
```

### 安全
```bash
/security-review # 安全审查 (单独使用或被 vibe-review --security 调用)
```
