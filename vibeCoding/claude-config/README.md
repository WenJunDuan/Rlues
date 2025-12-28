# Claude Code 标准配置 v7.1

> **"Talk is cheap. Show me the code."** — Linus Torvalds

AI编程协作专家系统，融合 RIPER-10 工作流、寸止协议和 Linus 思维。

---

## 🧠 核心理念

### 简洁至上 (Simplicity First)
恪守 **KISS** 原则。避免过度工程化，崇尚简洁与可维护性。

### 深度分析 (Deep Analysis)
立足于 **第一性原理** 剖析问题。不接受"因为别人这么做"的答案。

### 事实为本 (Fact-Based)
以事实为最高准则。数据说话，代码验证。

### 渐进式开发 (Iterative)
通过多轮对话迭代。**在着手设计或编码前，必须厘清所有疑点。**

---

## 📁 目录结构

```
.claude/
├── CLAUDE.md              # 🔑 主入口（铁律+核心理念）
├── commands/              # 命令定义
│   ├── dev.md            # 完整开发
│   ├── quick.md          # 快速修复
│   ├── architect.md      # 架构设计
│   ├── review.md         # 代码审查
│   └── debug.md          # 问题调试
├── agents/                # 角色定义(via promptx)
│   ├── pm.md             # 项目经理
│   ├── pdm.md            # 产品经理
│   ├── ar.md             # 架构师
│   ├── ld.md             # 开发工程师
│   ├── qe.md             # 测试工程师
│   ├── sa.md             # 安全审计
│   └── dw.md             # 技术文档
├── skills/                # 技能定义
│   ├── codex/            # ⭐ 代码执行
│   ├── memory/           # 记忆管理
│   ├── sou/              # 语义搜索(augment)
│   ├── thinking/         # 深度推理
│   ├── meeting/          # 🆕 本地模拟会议
│   ├── deepwiki/         # 技术文档
│   └── devtools/         # 浏览器测试
├── workflows/
│   ├── pace.md           # P.A.C.E.路由
│   ├── riper.md          # RIPER-10流程
│   └── cunji.md          # 寸止协议
└── references/
    ├── frontend-standards.md  # 前端规范
    ├── backend-standards.md   # 后端规范
    └── mcp-tools.md           # MCP工具参考
```

---

## 🚀 快速开始

```bash
# 复制到项目
cp -r .claude /your/project/

# 或全局配置
cp -r .claude ~/
```

---

## 🔐 四大铁律

1. **禁止直接询问** - 只能通过`寸止`交互
2. **默认静默执行** - 不创建文档/不测试/不编译
3. **未批准禁止结束** - 必须获得`寸止`确认
4. **工具优先于输出** - 能用工具解决的优先调用

---

## ⚡ P.A.C.E. 智能路由

| 路径 | 条件 | 流程 |
|:---|:---|:---|
| **Path A** | 单文件/<30行 | R1→E→R2 |
| **Path B** | 2-10文件 | R1→I→P→E→R2 |
| **Path C** | >10文件 | 分阶段迭代 |

---

## 🎭 多角色协作

通过 **meeting skill** 模拟多角色会议：

```
需求澄清会议: PM + PDM
技术方案会议: AR + LD + SA
任务分解会议: PM + AR + LD
代码评审会议: AR + LD + QE + SA
```

---

## ✅ Linus 审查清单

- [ ] **Data First**: 数据结构是最简的吗？
- [ ] **Naming**: 命名准确反映本质？
- [ ] **Simplicity**: 是否过度设计？能删掉什么？
- [ ] **Taste**: 代码有"品味"吗？

---

## 🛠️ MCP 工具依赖

**必需**:
- 寸止 (用户交互)
- memory (记忆管理)
- codex (代码执行)

**推荐**:
- augment-context-engine (sou搜索)
- sequential-thinking (深度推理)
- promptx (角色切换)

**可选**:
- mcp-deepwiki, chrome-devtools, fetch, everything, context7

---

## 🆕 v7.1 更新

- **移除** shrimp-task-manager，改用本地 **meeting skill** 模拟会议
- **拆分** 代码规范为前端/后端两份
- **强化** Linus思维（简洁至上、第一性原理、事实为本）
- **补全** 多角色协作流程细节

---

**版本**: v7.1 | **协议**: RIPER-10 + 寸止 | **哲学**: Linus Torvalds
