# Claude Code Plugins 配置指南

> **核心问题**：Plugins 是什么？怎么用？放在哪里？

---

## 🎯 快速回答

| 问题 | 答案 |
|:----|:----|
| 是什么？ | Markdown 格式的提示词/规则文件 |
| 需要安装吗？ | ❌ **不需要安装**，直接复制 |
| 放在哪里？ | **`.claude/commands/`** 目录 |
| 怎么触发？ | 用文件名作为指令，如 `/code-review` |

---

## 📁 目录结构规范

```
your-project/
├── .claude/
│   ├── CLAUDE.md                    # AI 入口文件
│   ├── orchestrator.yaml            # AI 调度配置
│   │
│   ├── commands/                    # ⭐ 官方 Plugins 放这里
│   │   ├── code-review.md          # 官方: 代码审查
│   │   ├── commit.md               # 官方: Git 提交
│   │   ├── pr-review.md            # 官方: PR 审查
│   │   ├── security.md             # 官方: 安全扫描
│   │   ├── vibe-plan.md            # 自定义: 规划
│   │   └── vibe-code.md            # 自定义: 编码
│   │
│   ├── agents/                      # 角色定义
│   ├── skills/                      # 技能定义
│   └── workflows/                   # 工作流定义
│
└── src/                             # 你的代码
```

### ⭐ 重点：官方 Plugins 放在 `.claude/commands/` 目录

---

## 🔧 获取和安装步骤

### Step 1: 获取官方 Plugins

```bash
# 方法 A: 克隆完整仓库
git clone https://github.com/anthropics/claude-code.git temp-claude-code

# 方法 B: 只下载需要的文件
# 直接在 GitHub 网页上复制内容
```

### Step 2: 复制到项目

```bash
# 创建 commands 目录（如果不存在）
mkdir -p your-project/.claude/commands

# 复制需要的 plugins
cp temp-claude-code/.claude/commands/code-review.md your-project/.claude/commands/
cp temp-claude-code/.claude/commands/commit.md your-project/.claude/commands/
# ... 复制其他需要的

# 清理临时文件
rm -rf temp-claude-code
```

### Step 3: 使用

```bash
# 在 Claude Code 中直接用文件名作为指令
/code-review              # 触发代码审查
/commit                   # 触发提交辅助
```

---

## 📦 官方 Plugins 列表

**来源**: https://github.com/anthropics/claude-code/tree/main/.claude/commands

| 文件名 | 功能 | 触发指令 |
|:------|:----|:--------|
| `code-review.md` | 代码审查 | `/code-review` |
| `commit.md` | Git 提交辅助 | `/commit` |
| `pr-review.md` | PR 审查 | `/pr-review` |
| `feature.md` | 功能开发流程 | `/feature` |
| `design.md` | 前端设计 | `/design` |
| `security.md` | 安全扫描 | `/security` |

> 注：具体可用 plugins 以官方仓库为准，可能会更新

---

## ⚠️ 重要说明

### 1. 不是 npm 包

```bash
# ❌ 错误
npm install @claude/code-review

# ✅ 正确
# 直接复制 .md 文件到 .claude/commands/ 目录
```

### 2. 不需要特殊配置

复制后直接可用，Claude Code 会自动识别 `.claude/commands/` 下的所有 `.md` 文件。

### 3. 自定义 vs 官方

| 类型 | 放置位置 | 说明 |
|:----|:--------|:----|
| 官方 Plugins | `.claude/commands/` | 从 GitHub 复制 |
| 自定义指令 | `.claude/commands/` | 你自己写的 |
| 角色定义 | `.claude/agents/` | PM, LD 等角色 |
| 技能定义 | `.claude/skills/` | codex, thinking 等 |

---

## 🔄 保持更新

```bash
# 定期检查官方更新
cd temp-claude-code
git pull

# 对比并更新
diff your-project/.claude/commands/code-review.md temp-claude-code/.claude/commands/code-review.md
```

---

## 📝 创建自定义指令

如果你想创建自己的指令（和官方 Plugins 并列）：

```markdown
---
name: my-command
description: 我的自定义指令
---

# /my-command

## 用法
\`\`\`
/my-command              # 基础用法
/my-command --strict     # 带参数
\`\`\`

## 执行步骤
1. ...
2. ...
```

保存为 `.claude/commands/my-command.md`，即可用 `/my-command` 触发。

---

## ✅ 总结

| 步骤 | 操作 |
|:----|:----|
| 1 | 从 GitHub 复制 `.md` 文件 |
| 2 | 放到 `.claude/commands/` 目录 |
| 3 | 用 `/文件名` 触发 |

**就这么简单，不需要安装任何东西。**

---

**官方仓库**: https://github.com/anthropics/claude-code
