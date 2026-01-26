---
name: multi-ai-sync
description: 多 AI 协调同步协议 - 解决 Claude/Codex/Gemini 如何协同工作
---

# 🔄 多 AI 协调同步协议

> **核心问题**：当多个 AI（Claude Code、Codex、Gemini）同时或交替工作时，如何保证：
> 1. 状态一致性
> 2. 上下文连续性
> 3. 任务不冲突
> 4. 结果可追溯

---

## 1. 核心原则

### 1.1 文件系统是唯一真理

```
┌─────────────────────────────────────────────────────────┐
│                   唯一真理来源                           │
│         project_document/.ai_state/                     │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌─────────┐   ┌─────────┐   ┌─────────┐               │
│  │ Claude  │   │ Codex   │   │ Gemini  │               │
│  │  Code   │   │  CLI    │   │  CLI    │               │
│  └────┬────┘   └────┬────┘   └────┬────┘               │
│       │             │             │                     │
│       ▼             ▼             ▼                     │
│  ┌─────────────────────────────────────────┐           │
│  │         .ai_state/ (文件系统)            │           │
│  │  ├── active_context.md  # 当前状态       │           │
│  │  ├── kanban.md          # 进度看板       │           │
│  │  ├── handoff.md         # 交接记录       │           │
│  │  └── .ai_lock           # 并发锁         │           │
│  └─────────────────────────────────────────┘           │
│                                                         │
└─────────────────────────────────────────────────────────┘

规则：
- 每个 AI 开始工作前必须读取 .ai_state/
- 每个 AI 完成工作后必须更新 .ai_state/
- 不依赖会话记忆，只依赖文件
```

### 1.2 任务单一所有权

```
同一时刻，一个任务只能被一个 AI 执行：

T-001: Claude Code ✅ (正在执行)
T-002: Codex      ✅ (正在执行)  
T-003: 待分配    ⏳ (等待中)
T-001: Gemini    ❌ (冲突！已被 Claude 占用)
```

### 1.3 显式交接

```
AI 之间不能"隐式"传递信息，必须通过 handoff.md 显式交接：

Claude Code 完成 T-001 → 写入 handoff.md → Codex 读取后继续
```

---

## 2. 状态文件规范

### 2.1 active_context.md（当前状态）

```markdown
# Active Context

## 🔒 当前执行锁

| 任务 | 执行者 | 开始时间 | 状态 |
|:----|:------|:--------|:----|
| T-002 | codex | 2025-01-11T10:30:00 | 🔄 执行中 |
| T-003 | claude-code | 2025-01-11T10:35:00 | 🔄 执行中 |

## 📋 任务队列

### 执行中
- T-002: 数据库设计 (codex)
- T-003: API 接口 (claude-code)

### 待执行
- T-004: 前端页面 (待分配)
- T-005: 用户认证 (待分配)

### 已完成
- T-001: 项目初始化 ✅ (codex, 10:28)

## 📝 最近变更

| 时间 | AI | 动作 | 文件 |
|:----|:---|:----|:----|
| 10:35 | claude-code | 创建 | src/api/users.ts |
| 10:32 | codex | 创建 | src/db/schema.ts |
```

### 2.2 handoff.md（任务交接）

```markdown
# 任务交接记录

---

## Handoff #001

**时间**: 2025-01-11T10:30:00
**任务**: T-002 数据库设计
**交接方向**: claude-code → codex

### 已完成工作
- 数据模型设计完成
- 接口定义已写入 src/types/

### 待继续工作
- 实现 CRUD 函数
- 添加数据验证

### 上下文摘要
```
用户需求：博客系统
技术栈：Next.js + SQLite
数据模型：User, Article, Tag
关系：Article belongsTo User, Article hasMany Tags
```

### 关键文件
- `src/types/models.ts` - 数据模型定义
- `src/db/schema.sql` - 数据库 Schema

### 注意事项
- 用户要求使用 SQLite
- 文章需要支持 Markdown

---
```

### 2.3 .ai_lock（并发锁）

```json
{
  "locked_by": "codex",
  "locked_at": "2025-01-11T10:30:00Z",
  "task_id": "T-002",
  "expires_at": "2025-01-11T10:35:00Z"
}
```

---

## 3. 协调流程

### 3.1 任务领取流程

```
┌─────────────────────────────────────────────────────────┐
│                    任务领取流程                          │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  1. 检查 .ai_lock                                       │
│     ├── 无锁 → 继续                                     │
│     └── 有锁 → 等待或选择其他任务                        │
│                                                         │
│  2. 创建锁文件                                          │
│     .ai_lock = { locked_by: "codex", task_id: "T-002" } │
│                                                         │
│  3. 读取 active_context.md                              │
│     获取任务详情和上下文                                 │
│                                                         │
│  4. 读取 handoff.md（如有前序交接）                      │
│     获取前一个 AI 的工作成果                             │
│                                                         │
│  5. 执行任务                                            │
│                                                         │
│  6. 更新状态文件                                        │
│     - active_context.md                                 │
│     - handoff.md（如需交接）                            │
│     - kanban.md                                         │
│                                                         │
│  7. 释放锁                                              │
│     删除 .ai_lock                                       │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### 3.2 任务交接流程

```
┌─────────────────────────────────────────────────────────┐
│            Claude Code → Codex 交接示例                  │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Claude Code (完成设计阶段):                             │
│                                                         │
│  1. 完成架构设计                                        │
│  2. 写入 handoff.md:                                    │
│     - 已完成: 数据模型设计                               │
│     - 待继续: 实现 CRUD                                 │
│     - 关键文件: src/types/models.ts                     │
│  3. 更新 active_context.md:                             │
│     - T-002: claude-code → handoff → codex             │
│  4. 释放锁                                              │
│                                                         │
│  ─────────────────────────────────────────────────────  │
│                                                         │
│  Codex (接收执行阶段):                                   │
│                                                         │
│  1. 获取锁                                              │
│  2. 读取 handoff.md                                     │
│  3. 读取关键文件 src/types/models.ts                    │
│  4. 继续实现 CRUD                                       │
│  5. 完成后更新状态                                       │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### 3.3 并行执行流程

```
┌─────────────────────────────────────────────────────────┐
│                    并行执行示例                          │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  前提：任务之间无依赖关系                                │
│                                                         │
│  ┌─────────────┐         ┌─────────────┐               │
│  │   Codex     │         │   Codex     │               │
│  │   T-004     │         │   T-005     │               │
│  │  前端组件   │         │  后端API    │               │
│  └──────┬──────┘         └──────┬──────┘               │
│         │                       │                       │
│         ▼                       ▼                       │
│  ┌─────────────────────────────────────────┐           │
│  │         active_context.md               │           │
│  │                                         │           │
│  │  执行中:                                │           │
│  │  - T-004: codex (instance-1)           │           │
│  │  - T-005: codex (instance-2)           │           │
│  └─────────────────────────────────────────┘           │
│                                                         │
│  规则：                                                 │
│  1. 每个任务有独立的锁                                  │
│  2. 并行任务不能修改同一文件                            │
│  3. 完成后需要集成验证                                  │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## 4. 冲突解决

### 4.1 文件冲突

```yaml
场景: Codex 和 Claude Code 同时修改了同一文件

解决方案:
  1. 检测冲突:
     - 比较文件修改时间戳
     - 使用 git diff 检测
     
  2. 冲突处理优先级:
     - 用户指定 > 后完成的 AI > 先完成的 AI
     
  3. 自动合并:
     - 如果修改不同区域，尝试自动合并
     - 如果修改同一区域，创建 .conflict 文件等待人工处理
```

### 4.2 任务冲突

```yaml
场景: 两个 AI 同时尝试领取同一任务

解决方案:
  1. 锁机制:
     - 先获取锁的 AI 执行
     - 后到的 AI 选择其他任务或等待
     
  2. 锁超时:
     - 锁有超时时间（默认 5 分钟）
     - 超时后其他 AI 可以接管
     
  3. 死锁检测:
     - 定期检查锁状态
     - 发现死锁自动释放
```

---

## 5. 实际调用示例

### 5.1 主 AI 调度其他 AI

```markdown
## 场景：Claude Code 作为主 AI，调度 Codex 执行子任务

### Claude Code 操作：

1. 分析任务，决定交给 Codex：
   "T-004 是并行的前端任务，交给 Codex 执行"

2. 写入交接信息到 handoff.md

3. 调用 Codex：
   ```bash
   codex - <<'EOF'
   任务ID: T-004
   描述: 实现用户列表组件
   上下文: @project_document/.ai_state/handoff.md
   范围: @src/components/UserList/
   完成后更新: @project_document/.ai_state/active_context.md
   EOF
   ```

4. 等待 Codex 完成

5. 读取更新后的 active_context.md，继续下一步
```

### 5.2 用户指定 AI

```markdown
## 场景：用户要求用 Codex 完成开发

用户: "用 codex 来实现这个登录功能"

主 AI 操作：
1. 识别用户指定了 codex
2. 无论 orchestrator.yaml 如何配置，都使用 codex
3. 准备任务上下文
4. 调用 codex 执行
```

### 5.3 多 AI 协作完整流程

```markdown
## 场景：博客系统开发

Phase 1 - 需求分析 (Claude Code 主导)
├── Claude Code 分析需求
├── 生成任务列表
└── 写入 active_context.md

Phase 2 - 并行开发 (多 AI)
├── T-001 项目初始化: Codex (快)
├── T-002 数据库设计: Claude Code (需思考)
├── T-003 后端 API: 
│   ├── Claude Code 设计接口
│   └── Codex 实现代码 (交接)
└── T-004/T-005 前端页面: Codex 并行

Phase 3 - 集成测试 (Claude Code)
├── 读取所有 AI 的工作成果
├── 验证集成
└── 修复问题

每个阶段转换时：
1. 当前 AI 更新 active_context.md
2. 写入 handoff.md
3. 下一个 AI 读取后继续
```

---

## 6. 调度器实现要点

### 6.1 Orchestrator 职责

```python
class Orchestrator:
    def __init__(self, config_path="orchestrator.yaml"):
        self.config = load_yaml(config_path)
        self.state_dir = self.config["sync"]["state_dir"]
    
    def select_engine(self, task, user_override=None):
        """
        引擎选择优先级：
        1. 用户指定
        2. 角色映射
        3. 任务类型提示
        4. 默认引擎
        """
        if user_override:
            return user_override
        
        role = task.get("assigned_role")
        if role and role in self.config["role_engine_mapping"]:
            return self.config["role_engine_mapping"][role]
        
        task_type = task.get("type")
        if task_type and task_type in self.config["task_type_hints"]:
            return self.config["task_type_hints"][task_type]
        
        return self.config["default_engine"]["name"]
    
    def dispatch(self, task, engine):
        """分发任务到指定引擎"""
        # 1. 获取锁
        self.acquire_lock(task["id"], engine)
        
        # 2. 准备上下文
        context = self.prepare_context(task)
        
        # 3. 调用引擎
        if engine == "codex":
            result = self.call_codex(task, context)
        elif engine == "gemini":
            result = self.call_gemini(task, context)
        else:
            result = self.execute_directly(task, context)
        
        # 4. 更新状态
        self.update_state(task, result)
        
        # 5. 释放锁
        self.release_lock(task["id"])
        
        return result
```

### 6.2 状态同步实现

```python
class StateSync:
    def read_context(self):
        """读取当前上下文"""
        return read_file(f"{self.state_dir}/active_context.md")
    
    def write_context(self, content):
        """写入上下文（带锁）"""
        with file_lock(f"{self.state_dir}/.ai_lock"):
            write_file(f"{self.state_dir}/active_context.md", content)
    
    def create_handoff(self, from_ai, to_ai, task, summary):
        """创建交接记录"""
        handoff = f"""
## Handoff #{self.next_handoff_id()}

**时间**: {now()}
**任务**: {task['id']} {task['name']}
**交接**: {from_ai} → {to_ai}

### 已完成
{summary['completed']}

### 待继续
{summary['pending']}

### 关键文件
{summary['files']}
"""
        append_file(f"{self.state_dir}/handoff.md", handoff)
```

---

## 7. 检查清单

### 任务开始前
- [ ] 读取 active_context.md
- [ ] 检查是否有锁冲突
- [ ] 读取 handoff.md（如有交接）
- [ ] 获取任务锁

### 任务执行中
- [ ] 定期更新进度（长任务）
- [ ] 记录修改的文件列表

### 任务完成后
- [ ] 更新 active_context.md
- [ ] 更新 kanban.md
- [ ] 写入 handoff.md（如需交接）
- [ ] 释放锁

---

**版本**: v1.0 | **核心**: 文件系统同步 + 显式交接 + 锁机制
