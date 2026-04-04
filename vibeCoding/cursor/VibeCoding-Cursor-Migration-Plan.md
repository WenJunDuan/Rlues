# VibeCoding Kernel → Cursor 3.0 移植架构计划

> 身份：跨平台 AI 编排架构师，VibeCoding 全版本作者
> 日期：2026-04-04
> 源版本：VibeCoding v9.3.7 (CC-only, 32 files, 1162 lines)
> 目标平台：Cursor 3.0 (2026.04.02 release)

---

## 0. 核心约束（动手前必须刻进脑子里）

| 约束 | 值 | 来源 |
|---|---|---|
| User Rules 字符上限 | **≤ 20,000 字符** | Cursor Forum 确认 |
| User Rules 格式 | **纯文本/Markdown，无 frontmatter** | Cursor 官方文档 |
| User Rules 作用域 | **全局，所有项目，所有会话** | Cursor Settings → Rules |
| Token 税 | 每个 rule 字占用上下文窗口 | 社区实测 |
| Rules 生效范围 | **仅 Agent + Inline Edit**（Tab 补全无效）| 官方文档 |
| Hooks 可全局 | `~/.cursor/hooks.json` | GitButler 博客 + 官方确认 |
| Commands/Skills | **仅项目级** (`.cursor/commands/`, `.cursor/skills/`) | 官方文档 |

### 这意味着什么？

v9.3.7 的 32 文件 1162 行 ≈ **~35,000 字符**。塞不进 20k 的 User Rules。
必须做**残酷的压缩和取舍**，不是"移植"，是"蒸馏"。

---

## 1. Cursor 4 层配置体系 vs CC 架构映射

```
┌─────────────────────────────────────────────────────────┐
│                    Cursor 配置体系                        │
│                                                         │
│  ┌─────────────┐  全局，≤20k chars                      │
│  │ User Rules  │  Settings → Rules (纯文本)             │
│  │  (系统级)    │  → 你的 VibeCoding 核心在这里           │
│  └──────┬──────┘                                        │
│         │ 叠加                                          │
│  ┌──────▼──────┐  项目级，.cursor/rules/*.mdc           │
│  │Project Rules│  YAML frontmatter + globs              │
│  │  (项目级)    │  → 技术栈特定规则（可选增强）            │
│  └──────┬──────┘                                        │
│         │ 叠加                                          │
│  ┌──────▼──────┐  项目级，.cursor/commands/*.md          │
│  │  Commands   │  /vibe-dev, /vibe-init 等              │
│  │  (项目级)    │  → 快捷指令（需要项目文件）              │
│  └──────┬──────┘                                        │
│         │ 并行                                          │
│  ┌──────▼──────┐  全局 ~/.cursor/hooks.json             │
│  │   Hooks     │  OR 项目级 .cursor/hooks.json          │
│  │ (可全局)     │  → 生命周期守卫                         │
│  └─────────────┘                                        │
└─────────────────────────────────────────────────────────┘
```

### 用户要求：不拷贝到项目根目录 → 可用的层

| 层 | 可用？ | 说明 |
|---|---|---|
| **User Rules** | ✅ 主力 | 系统级，20k 字符 |
| **Global Hooks** | ✅ 辅助 | `~/.cursor/hooks.json`，全局生效 |
| **Project Rules** | ❌ 不用 | 需要项目文件 |
| **Commands** | ❌ 不用 | 需要项目文件 |
| **Skills** | ❌ 不用 | 需要项目文件 |

**结论：所有 VibeCoding 逻辑必须压缩进 User Rules (20k) + Global Hooks (hooks.json)**

---

## 2. v9.3.7 组件蒸馏分析

### 2.1 必须保留（核心价值，无可替代）

| 组件 | CC 原始行数 | 蒸馏目标 | 理由 |
|---|---|---|---|
| PACE 复杂度路由 | ~50 行 | ~800 字符 | 核心决策引擎，Cursor 没有等价物 |
| RIPER-7 阶段定义 | ~200 行 | ~3000 字符 | 核心编排流程，Cursor Plan Mode 不够 |
| Sprint Contract | ~30 行 | ~500 字符 | 人机协作协议 |
| 质量门控 (Quality Gate) | ~40 行 | ~600 字符 | 交付标准 |
| 寸止 (Cunzhi) 协议 | ~20 行 | ~300 字符 | 关键决策暂停点 |
| Sisyphus 规则 | ~10 行 | ~200 字符 | 任务完成性保障 |
| **小计** | ~350 行 | **~5,400 字符** | |

### 2.2 需重建（CC 专属逻辑 → Cursor 原生替代）

| 组件 | CC 实现 | Cursor 替代 | 蒸馏目标 |
|---|---|---|---|
| generator.md | GSD→codex→superpowers 降级链 | Cursor Agent Mode + /best-of-n + /worktree | ~800 字符 |
| evaluator.md | /review + codex adversarial + ECC | Cursor Agent 自审 + Bugbot + MCP 工具 | ~1000 字符 |
| context-loader | SessionStart hook 恢复 .ai_state/ | Global hooks + Agent 指令 | ~300 字符 (rules 部分) |
| delivery-gate | Stop hook 检查 quality.json | Global hooks stop event | ~200 字符 (rules 部分) |
| pre-bash-guard | PreToolUse 拦截危险命令 | Global hooks beforeShellExecution | ~0 (纯 hooks 实现) |
| **小计** | ~400 行 | | **~2,300 字符** |

### 2.3 应砍掉（Cursor 原生已覆盖 或 不适用）

| 组件 | 原因 |
|---|---|
| settings.json | CC 私有格式，Cursor 无对应 |
| enabledPlugins / extraKnownMarketplaces | CC 插件生态，不适用 |
| 所有 .cjs hook 脚本 | 需重写为 Cursor hooks.json 格式 |
| GSD/superpowers/codex/ECC 插件命令 | CC 专属插件 |
| hookSpecificOutput 格式 | CC 专属 |
| post-edit-check.cjs | Cursor afterFileEdit hook 替代 |
| permission-denied.cjs / stop-failure.cjs | Cursor 无对应事件 |

### 2.4 字符预算

```
总预算：              20,000 字符
─────────────────────────────
角色身份 + 行为准则：   ~2,000 字符
PACE 路由：            ~  800 字符
RIPER-7 编排：         ~3,000 字符
Sprint Contract：      ~  500 字符
质量门控：             ~  600 字符
行为规则（寸止/Sisyphus）：~ 500 字符
生成策略（Cursor 原生）：~  800 字符
评估策略（Cursor 原生）：~1,000 字符
.ai_state 状态管理：   ~  600 字符
Cursor 特有指令：      ~  800 字符
─────────────────────────────
预计使用：            ~10,600 字符
安全余量：            ~ 9,400 字符 (47%)
```

**47% 余量 → 有空间但不能浪费。每个字必须有信息增量。**

---

## 3. Cursor 原生能力利用策略

> 原则："VibeCoding 不让 AI 更聪明。VibeCoding 给 AI 车间。"
> Cursor 3.0 自带了半个车间，我们只补 Cursor 没有的。

| VibeCoding 需要的能力 | Cursor 原生实现 | User Rules 里怎么写 |
|---|---|---|
| 需求分析 / brainstorm | Plan Mode (选 "plan" 而非 "agent") | "R₀ 阶段：使用 Plan Mode 分析需求" |
| 技术调研 | @codebase + @docs + @web | "R 阶段：用 @codebase 搜索相关代码，@web 查最新文档" |
| 方案设计 | Plan Mode 输出 | "D 阶段：在 Plan Mode 中定稿方案" |
| 并行开发 | Agent 并行 + /worktree | "E 阶段复杂任务：建议用 /worktree 隔离" |
| 跨模型验证 | /best-of-n | "T 阶段可用 /best-of-n 多模型交叉验证" |
| 代码审查 | Bugbot + Agent 自审 | "T 阶段：提交前进行自我审查" |
| 上下文恢复 | Cursor 全仓库索引 + /summarize | "恢复上下文：读 .ai_state/ 状态文件" |
| 安全扫描 | MCP 工具 (如果配置了) | "安全检查：如有 MCP 安全工具则调用" |

---

## 4. Global Hooks 设计

文件位置：`~/.cursor/hooks.json`

### 4.1 事件映射

| CC Hook | CC 事件 | Cursor 事件 | 可行性 |
|---|---|---|---|
| context-loader.cjs | SessionStart | **无直接对应** | ❌ 改为 rules 指令 |
| pre-bash-guard.cjs | PreToolUse(Bash) | beforeShellExecution | ✅ 可移植 |
| post-edit-check.cjs | PostToolUse(Write) | afterFileEdit | ✅ 可移植 |
| delivery-gate.cjs | Stop | stop | ✅ 可移植（但不能阻断）|
| permission-denied.cjs | PermissionDenied | **无对应** | ❌ 砍掉 |
| stop-failure.cjs | StopFailure | **无对应** | ❌ 砍掉 |

### 4.2 Cursor Hooks 关键限制

| CC Hooks 能力 | Cursor Hooks 能力 |
|---|---|
| exit 2 可**阻断**工具调用 | ⚠️ beforeShellExecution 可阻断，其他事件只能观察 |
| hookSpecificOutput 可注入上下文 | ❌ 目前不支持注入上下文（beta 限制）|
| 6 种事件 | 6 种事件（不同集合）|

### 4.3 hooks.json 结构

```json
{
  "version": 1,
  "hooks": {
    "beforeShellExecution": [
      {
        "command": "node ~/.cursor/hooks/pre-bash-guard.js"
      }
    ],
    "afterFileEdit": [
      {
        "command": "node ~/.cursor/hooks/post-edit-check.js"
      }
    ],
    "stop": [
      {
        "command": "node ~/.cursor/hooks/delivery-summary.js"
      }
    ]
  }
}
```

---

## 5. 执行计划（4 个阶段）

### Phase 1: 蒸馏 User Rules（核心）
1. 写角色身份 + 行为准则
2. 写 PACE 路由表（压缩版）
3. 写 RIPER-7 阶段定义（每阶段：目标→Cursor 操作→产出→门控）
4. 写 Sprint Contract 协议
5. 写 Quality Gate 标准
6. 写行为规则（寸止、Sisyphus、不造轮子）
7. 写 Cursor 特有操作指令（Plan Mode / Agent / @context / /worktree）
8. 写 .ai_state/ 状态文件管理指令
9. **字符计数验证** ≤ 20,000

### Phase 2: 实现 Global Hooks
1. 写 `~/.cursor/hooks.json`
2. 写 `pre-bash-guard.js`（从 CC .cjs 移植，适配 Cursor stdin 格式）
3. 写 `post-edit-check.js`
4. 写 `delivery-summary.js`
5. 测试 hooks 事件触发

### Phase 3: Review（三轮）
1. **逐行审查 User Rules**：每句话是否有信息增量？能否更短？
2. **Agent 视角走查**：如果我是 Cursor Agent 读到这段 rules，我知道该做什么吗？
3. **Cursor 原生冲突检查**：rules 是否与 Cursor 内置行为矛盾？
4. **字符计数终审**

### Phase 4: 输出打包
1. User Rules 文本（直接粘贴到 Settings → Rules）
2. `~/.cursor/hooks.json`
3. `~/.cursor/hooks/` 目录下的 .js 脚本
4. 安装说明 README
5. CHANGELOG

---

## 6. 设计决策记录

### D1: 为什么不用 Project Rules？
用户技术栈五花八门，不能每个项目拷贝文件。User Rules 是唯一的全局注入点。

### D2: 为什么不用 .cursorrules？
已废弃（deprecated），且是项目级文件。

### D3: 为什么 RIPER-7 不直接用 Cursor Plan Mode 替代？
Plan Mode 只是"分析不写代码"的开关。RIPER-7 是 7 个阶段的完整生命周期编排，
Plan Mode 只覆盖了 R₀/R/D 三个阶段的部分功能。P/E/T/V 阶段没有 Cursor 原生对应。

### D4: CC 插件功能怎么处理？
不移植。Cursor 的 MCP + Marketplace 是不同生态。
在 rules 里写"如有可用 MCP 工具则调用"，不硬编码具体插件名。

### D5: .ai_state/ 状态文件怎么处理？
保留概念，在 rules 里指令 Agent 创建和维护这些文件。
但不能强制（没有 hooks 的 SessionStart 来自动检查）。
改为"每次开始新 Sprint 时，检查并创建 .ai_state/ 目录"。

### D6: 6 个 CC Hooks 只能移植 3 个？
是的。Cursor hooks 事件集不同。
context-loader (SessionStart) → 降级为 rules 里的文字指令
permission-denied / stop-failure → Cursor 无对应，砍掉

### D7: 语言选择？
用户偏好中文，User Rules 用中文写。
技术术语保留英文（PACE、RIPER-7、Sprint Contract、Quality Gate）。
