# VibeCoding Kernel v1.0-cursor

> 从 VibeCoding v9.3.7 (Claude Code) 蒸馏的 Cursor 3.0 系统级配置
> 不需要在项目中放任何文件，全局生效

## 它是什么

VibeCoding 不让 AI 更聪明，它给 AI 一个工程化的工作流程：

- **P.A.C.E.** 自动评估任务复杂度，选择对应执行路径
- **RIPER-7** 把开发拆成 7 个阶段（需求→调研→定稿→排期→执行→测试→归档），每个阶段有明确的产出和门控
- **寸止协议** 在关键决策点暂停，等待人类确认
- **Quality Gate** 交付前 4 维度质量检查
- **Global Hooks** 自动拦截危险命令、检查代码质量、输出会话摘要

## 包含什么

```
vibecoding-v10-cursor/
├── user-rules.md              # 粘贴到 Cursor Settings → Rules
├── hooks.json                 # 复制到 ~/.cursor/hooks.json
└── hooks/
    ├── pre-bash-guard.js      # beforeShellExecution: 拦截 rm -rf 等危险命令
    ├── post-edit-check.js     # afterFileEdit: 检查 TODO/调试代码/硬编码密钥
    └── delivery-summary.js    # stop: 输出会话进度摘要
```

## 安装

### 第 1 步：配置 User Rules

1. 打开 Cursor
2. Settings（右上角齿轮）→ Rules
3. 在 "User Rules" 文本框中，粘贴 `user-rules.md` 的全部内容
4. 保存

### 第 2 步：安装 Global Hooks

**macOS / Linux：**

```bash
mkdir -p ~/.cursor/hooks
cp hooks.json ~/.cursor/hooks.json
cp hooks/*.js ~/.cursor/hooks/
chmod +x ~/.cursor/hooks/*.js
```

**Windows (PowerShell)：**

```powershell
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.cursor\hooks"
Copy-Item hooks.json "$env:USERPROFILE\.cursor\hooks.json"
Copy-Item hooks\*.js "$env:USERPROFILE\.cursor\hooks\"
```

### 第 3 步：重启 Cursor

关闭并重新打开 Cursor IDE。

## 验证

在 Agent 中输入 `你是按什么框架工作的？`，Agent 应回答遵循 VibeCoding / PACE / RIPER-7。

查看 Cursor Settings → Hooks 面板，确认 hooks 注册成功。

## Hooks 技术细节

| Hook                | 事件                 | 类型   | 能力                                       |
| ------------------- | -------------------- | ------ | ------------------------------------------ |
| pre-bash-guard.js   | beforeShellExecution | 拦截型 | stdout 返回 `{permission:"deny"}` 阻断命令 |
| post-edit-check.js  | afterFileEdit        | 观察型 | stderr 输出警告，不能阻断编辑              |
| delivery-summary.js | stop                 | 观察型 | stderr 输出进度摘要                        |

## 与 CC v9.3.7 的主要区别

| 维度       | CC v9.3.7             | Cursor v1.0                           |
| ---------- | --------------------- | ------------------------------------- |
| 文件数     | 32                    | 5                                     |
| 配置方式   | .claude/ 项目目录     | 系统级全局                            |
| 插件依赖   | 8 个 CC 插件          | 0（利用 Cursor 原生能力）             |
| 生成策略   | GSD→codex→superpowers | Cursor Agent + /worktree + /best-of-n |
| Hooks 事件 | 6 个                  | 3 个（Cursor hooks 集合不同）         |

## 已知限制

1. **User Rules 上限 20k 字符** — 当前约 6.5k，余量充足
2. **无 SessionStart hook** — 不能自动恢复上下文，需手动让 Agent 读 .ai_state/
3. **afterFileEdit 不能阻断** — 只能输出警告，不能回退编辑
4. **Token 税** — User Rules 占用每次请求的上下文窗口（约 2k tokens）
5. **Commands/Skills 不可用** — 系统级配置不支持，所有逻辑编码在 Rules 中

## 可选增强

如果你需要项目级增强，可以在具体项目中创建 `.cursor/rules/` 目录，添加技术栈特定的 `.mdc` 规则文件。这些规则会叠加在 User Rules 之上。

## 版本

- v1.0-cursor (2026-04-04)
- 源: VibeCoding v9.3.7 (Claude Code)
- 目标: Cursor 3.0+
