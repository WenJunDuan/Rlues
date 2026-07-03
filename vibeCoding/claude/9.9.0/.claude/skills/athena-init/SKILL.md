---
name: athena-init
description: |
  Athena 项目初始化 skill. 在项目中执行 /athena-init 时调用.
  职责: 探测平台 / 工具可用性, 创建 .ai_state/ 目录 + 复制 _index.md 模板 + 填入探测结果.
effort: medium
---

# /athena-init — 项目初始化 (v9.6.4)

## 触发

用户在新项目首次运行 `/athena-init`. 已 init 的项目 → 跳过, 提示用户用 `/athena-status` 查状态.

## 工作流 (按顺序)

### Step 1: 前置检查

```bash
# 项目是否已 init?
if [ -d ".ai_state" ]; then
  echo "项目已初始化, 使用 /athena-status 查看状态"
  exit 0
fi

# 是否在 git 仓库?
git rev-parse --git-dir >/dev/null 2>&1 || { echo "Athena 需要 git 仓库"; exit 1; }
```

### Step 2: 探测平台 (cc / cx / ag 可用性)

```bash
# CC 始终可用 (因为我们就在 CC 里跑)
CC_VERSION=$(claude --version 2>/dev/null || echo "claude-code (unknown)")

# CX
if command -v codex >/dev/null 2>&1; then
  CX_VERSION=$(codex --version 2>/dev/null)
  CX_AVAILABLE=true
else
  CX_VERSION=""
  CX_AVAILABLE=false
fi

# AG (Antigravity)
if command -v agy >/dev/null 2>&1; then
  AG_VERSION=$(agy --version 2>/dev/null || echo "agy (unknown)")
  AG_CALLABLE=true
else
  AG_CALLABLE=false
fi
```

### Step 3: 探测工具

```bash
# context7
if command -v npx >/dev/null 2>&1 && npx --no-install ctx7 --version >/dev/null 2>&1; then
  CTX7_AVAILABLE=true
else
  CTX7_AVAILABLE=false
fi

# augment MCP (CC 端在 ~/.claude/mcp.json 中)
if [ -f "$HOME/.claude/mcp.json" ] && grep -q "augment-context-engine" "$HOME/.claude/mcp.json" 2>/dev/null; then
  AUGMENT_CC=true
else
  AUGMENT_CC=false
fi

# rg / jq
RG_AVAILABLE=$(command -v rg >/dev/null && echo true || echo false)
JQ_AVAILABLE=$(command -v jq >/dev/null && echo true || echo false)

# v9.9.0: VM 运行时 (~/.athena/vm.json 由 /athena-vm setup 创建)
if [ -f "$HOME/.athena/vm.json" ]; then
  VM_AVAILABLE=true   # 存在即标 true; 连通性由 /athena-vm doctor 验证
else
  VM_AVAILABLE=false
fi
```

### Step 4: 创建 .ai_state/ 目录

```bash
mkdir -p .ai_state/sprints/reviews
mkdir -p .ai_state/sprints/lessons
mkdir -p .ai_state/requirements   # v9.8.0 长效需求档 (WHY, 逃生通道)
```

### Step 5: 复制 _index.md 模板 + 填入探测结果

```bash
cp ~/.claude/skills/pace/templates/_index.md .ai_state/_index.md
# 用 sed / python 把探测结果替换进 frontmatter
```

主 agent 编辑 `.ai_state/_index.md` 把上面探测到的真实值填入对应字段:
- `cc_version`, `cx_version`, `ag_callable`
- `tools_available.{context7_cli, augment_mcp_cc, rg_available, jq_available, vm_available}`
- `platform_features.{cc_subagent_task: true, cx_spawn_agent, cx_spawn_agents_on_csv, cx_goal_default_on, ag_parallel_subagents, ag_headless_p}`

判定规则 (主 agent 在 init 时执行):
- `cx_spawn_agent = true` if `CX_VERSION` >= 0.128
- `cx_spawn_agents_on_csv = true` if `CX_VERSION` >= 0.128 且 `~/.codex/config.toml [features].multi_agent = true`
- `cx_goal_default_on = true` if `CX_VERSION` >= 0.133.0
- `ag_parallel_subagents = ag_callable` (Antigravity 默认支持)
- `ag_headless_p = ag_callable` (`agy -p` 默认支持)

### Step 6: 初始 compound/

```bash
cat > .ai_state/compound/ << 'EOF'
# Project Lessons (Athena v9.6.4)

> 本项目积累的经验. 每次 polish / review 后由主 agent 追加.
> 格式: `## [date] 简述`
> 内容: pattern (做对的) / pitfall (踩的坑) / constraint (硬约束)

EOF
```

### Step 7: 总结 + 给用户

主 agent 输出 markdown 总结:
- 探测到的平台 (cc / cx / ag)
- 可用工具表
- **缺失但建议安装的工具** (例如 ctx7 / agy 没装就提示一行命令)
- 下一步: 用户说出第一个任务 → 主 agent 路由 PACE 路径

## 输出示例

```markdown
✓ Athena v9.6.4 初始化完成

## 平台
- CC: claude-code 2.4.1 ✓
- CX (codex): codex-cli 0.133.0 ✓
- AG (antigravity): 未安装. 安装: `curl -fsSL https://antigravity.google/cli/install.sh | bash`

## 工具
- context7 (npx ctx7): ✓
- augment MCP (CC): 未配置. 配置: 在 ~/.claude/mcp.json 加 augment-context-engine
- rg: ✓
- jq: ✓

## 状态
.ai_state/ 已建立, _index.md 已生成

## 下一步
告诉我你要做什么, 我会路由 PACE 路径:
- "修这个 bug" → Bugfix 路径
- "加个新功能" → Feature 路径
- "重构这个模块" → Refactor 路径 (含 polish 强制)
- "搭一个 X 系统" → System 路径 (含 design + polish 强制)
```

## 例外

- 若用户在非 git 项目跑: 主 agent 拒绝, 提示先 `git init`
- 若 ~/.claude/skills/pace/templates/_index.md 不存在: 主 agent fallback 用内置 minimum template (不要去掉 Athena 核心 frontmatter 字段)
- 若用户已 init 又跑 /athena-init: 不覆盖, 显式问 "重新初始化吗?会清空 .ai_state/"

## 路径无关

athena-init 不进入任何 PACE stage, 它是 stage="(none)" → 等待用户首条任务输入后才路由.
