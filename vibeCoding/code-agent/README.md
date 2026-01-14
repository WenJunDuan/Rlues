# VibeCoding Kernel v7.6

> **核心改进**: 精简文档 + 按需加载 + 真寸止

---

## 🎯 v7.6 核心变化

| 变化      | v7.5           | v7.6                         |
| :-------- | :------------- | :--------------------------- |
| CLAUDE.md | 417 行         | ~90 行                       |
| 总文件数  | 48 个          | ~25 个                       |
| 总行数    | ~6000 行       | ~2000 行                     |
| Workflow  | 单文件 1500 行 | 按阶段拆分                   |
| Skills    | 17 个独立      | 10 个合并                    |
| 寸止      | 文字输出       | cunzhi/mcp-feedback-enhanced |

---

## 📁 目录结构

```
.claude/
├── CLAUDE.md           # 核心铁律（<100行）
├── orchestrator.yaml   # 调度配置
│
├── skills/             # 按需加载
│   ├── research.md     # R1 阶段
│   ├── innovate.md     # I 阶段
│   ├── plan.md         # P 阶段
│   ├── execute.md      # E 阶段
│   ├── review.md       # R2 阶段
│   ├── cunzhi.md       # 寸止协议
│   ├── memory.md       # 记忆系统
│   ├── multi-ai.md     # 多AI协调
│   └── code-quality.md # 代码质量
│
├── workflows/          # 路径流程
│   ├── path-a.md       # 快速修复
│   ├── path-b.md       # 计划开发
│   └── path-c.md       # 系统开发
│
├── commands/           # 指令定义
│   ├── _index.md
│   ├── vibe-init.md
│   ├── vibe-code.md
│   └── control.md
│
├── hooks/              # 钩子函数
│   └── hooks.md
│
└── templates/          # 模板
    ├── kanban.md
    └── active_context.md
```

---

## 🚀 快速开始

### 1. 复制到项目

```bash
cp -r .claude your-project/
```

### 2. 初始化

```bash
/vibe-init
```

### 3. 开始工作

```bash
/vibe-code 实现用户登录功能
```

---

## 🔴 核心铁律

1. **启动必检查** → session.lock
2. **任务必 TODO** → 无论大小
3. **执行必更新** → kanban 三态
4. **完成必核对** → 逐项对照
5. **结束必寸止** → 调用 cunzhi
6. **纠正必记录** → forbidden_action
7. **文件是真理** → .ai_state/

---

## 📋 指令

| 指令           | 作用       |
| :------------- | :--------- |
| `/vibe-init`   | 初始化项目 |
| `/vibe-plan`   | 生成 TODO  |
| `/vibe-code`   | 执行编码   |
| `/vibe-status` | 查看状态   |
| `/vibe-pause`  | 暂停工作流 |
| `/vibe-resume` | 恢复工作流 |

---

## 🔧 按需加载

核心理念：**AI 不需要一次读完所有文档**

```
CLAUDE.md (铁律) → 加载
         ↓
选择路径 → 加载 workflows/path-x.md
         ↓
执行阶段 → 加载 skills/xxx.md
```

这样每次只加载需要的部分，避免注意力衰减。

---

## 📞 寸止机制

```
优先: cunzhi MCP
降级: mcp-feedback-enhanced

每个寸止点都必须调用工具，
真正暂停等待用户确认，
不是只输出文字！
```

---

**版本**: v7.6 | **架构**: 按需加载 + 真寸止
