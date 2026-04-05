# VibeCoding Kernel v3.0-cursor

> CC v9.3.7 架构 → Cursor 3.0 全局配置
> 不需要在项目中放文件，全局生效

## 架构

以 PACE 为核心调度器，编排 Skills / MCP / Hooks 协同工作：

```
用户输入
  ↓
User Rules (PACE 路由) ──→ 选定 Path A/B/C/D
  ↓
vibecoding-workflow (核心引擎)
  ├─→ vibecoding-plan       R0→R→D 规划（调用 cunzhi MCP 寸止确认）
  ├─→ vibecoding-execute    P→E 排期+执行（Sprint Contract → Reflexion）
  ├─→ vibecoding-review     T+QG 审查（Quality Gate 4 维评估）
  └─→ V 归档               workflow 自身完成
  
并行:
  Hooks: 安全拦截 + 质量警告 + 状态保存
  .ai_state/: 每阶段转换自动写入 JSON 状态

辅助 Skills:
  vibecoding-init       初始化 .ai_state/
  vibecoding-recovery   断点恢复
```

### 对标 CC v9.3.7

| CC v9.3.7 | Cursor v3.0 | 说明 |
|---|---|---|
| CLAUDE.md | User Rules | 入口路由器：铁律 + 框架地图 + 调度表 |
| workflow/SKILL.md | vibecoding-workflow | 核心引擎：调度子 skill |
| plan skill | vibecoding-plan | R0→R→D + cunzhi MCP 门控 |
| execute skill + generator | vibecoding-execute | Sprint Contract + 编码 + Reflexion |
| review skill + evaluator | vibecoding-review | T 验证 + Quality Gate 4 维评估 |
| settings.json | Cursor Settings | MCP / Hooks / 权限 |
| 6 hooks (.cjs) | 3 hooks (.js) | Cursor hooks 事件集不同 |
| 8 CC 插件 | 0 | Cursor 原生能力替代 |

## 安装

### Step 1: User Rules
Cursor Settings → Rules → 粘贴 `user-rules.md` 全部内容

### Step 2: Skills
```bash
# macOS / Linux
cp -r skills/* ~/.cursor/skills/

# Windows (PowerShell)
Copy-Item -Recurse skills\* "$env:USERPROFILE\.cursor\skills\"
```

### Step 3: Hooks
```bash
# macOS / Linux
mkdir -p ~/.cursor/hooks
cp hooks.json ~/.cursor/hooks.json
cp hooks/*.js ~/.cursor/hooks/
chmod +x ~/.cursor/hooks/*.js

# Windows (PowerShell)
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.cursor\hooks"
Copy-Item hooks.json "$env:USERPROFILE\.cursor\hooks.json"
Copy-Item hooks\*.js "$env:USERPROFILE\.cursor\hooks\"
```

### Step 4: MCP（可选）
Cursor Settings → MCP → 配置 cunzhi。不配置则自动降级为文字确认。

### Step 5: 重启 Cursor

## 文件清单（12 个）

```
user-rules.md                          Settings → Rules 粘贴
skills/
  vibecoding-workflow/SKILL.md         核心引擎：PACE 路径编排
  vibecoding-plan/SKILL.md             R0→R→D 规划三阶段
  vibecoding-execute/SKILL.md          P→E 排期+执行+Reflexion
  vibecoding-review/SKILL.md           T+QG 审查+质量门控
  vibecoding-init/SKILL.md             初始化 .ai_state/
  vibecoding-recovery/SKILL.md         断点恢复
hooks.json                             Cursor hooks 配置
hooks/
  pre-bash-guard.js                    beforeShellExecution: 安全拦截
  post-edit-check.js                   afterFileEdit: 质量警告
  delivery-summary.js                  stop: 状态保存+摘要
README.md                             本文件
```

## Review 记录

5 轮 Review，共发现并修复 16 个 bug：

| 轮次 | 方法 | 发现 |
|------|------|------|
| R1 逐行审查 | 每个文件逐行读 | 11 个 |
| R2 流程走查 | 模拟 Path A + Path B 完整流程 | 1 个 |
| R3 平台兼容 | Cursor API/格式检查 | 0 个 |
| R4 交叉一致 | 字段名/模板/版本号对齐 | 3 个 |
| R5 环境模拟 | Skill 触发词冲突检测 | 1 个 |

关键修复：
- beforeShellExecution 用 stdout JSON `{permission:"deny"}`（exit code 在 Cursor 无效）
- afterFileEdit 路径拼接 workspace_roots（相对路径问题）
- 所有 .ai_state/ 写入添加存在性检查（共 9 处）
- Skill description 去除触发词冲突（execute/plan 加"不直接触发"语义）
- R0 统一用 ASCII（与 state.json phase 字段值一致）

最终回归测试：32/32 全通过。

## 版本

- v3.0-cursor (2026-04-05)
- 源: VibeCoding v9.3.7 (Claude Code, 32 files, 1162 lines)
- 目标: Cursor 3.0+
