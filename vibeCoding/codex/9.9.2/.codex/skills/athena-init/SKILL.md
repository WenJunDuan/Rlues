---
name: athena-init
description: |
  Athena 项目初始化 skill (Codex). 在项目中说"初始化 Athena"/"athena init"时触发.
  职责: 探测平台 / 工具可用性, 创建 .ai_state/ 目录 (v9.9.2 schema) + 复制 _index.md 模板 + 填入探测结果.
  v9.7.0: 文件名修正 athena-init.md → SKILL.md (config.toml [[skills.config]] 指向 SKILL.md, 旧文件名导致加载失败).
---

# /athena-init — 项目初始化 (Codex, v9.9.2)

Memory contract: **Tier1 working memory** is non-authoritative; **Tier2 persistent memory** is the created `.ai_state`; **_index.md retrieval router** owns bounded recovery pointers/history.

## 触发

用户在新项目首次要求初始化 Athena. 已 init 的项目 → 跳过, 提示用 athena-status 查状态.

## 工作流 (按顺序)

### Step 1: 前置检查

```bash
if [ -d ".ai_state" ]; then
  echo "项目已初始化, 用 athena-status 查看状态"; exit 0
fi
git rev-parse --git-dir >/dev/null 2>&1 || { echo "Athena 需要 git 仓库, 先 git init"; exit 1; }
```

### Step 2: 探测平台 (cx / cc / ag)

```bash
# CX 始终可用 (我们就在 Codex 里跑)
CX_VERSION=$(codex --version 2>/dev/null || echo "codex-cli (unknown)")
CX_AVAILABLE=true

# CC 是否也在 (可选)
if command -v claude >/dev/null 2>&1; then
  CC_VERSION=$(claude --version 2>/dev/null)
else
  CC_VERSION=""
fi

# AG (Antigravity)
if command -v agy >/dev/null 2>&1; then
  AG_VERSION=$(agy --version 2>/dev/null || echo "agy (unknown)"); AG_CALLABLE=true
else
  AG_CALLABLE=false
fi
```

### Step 3: 探测工具

```bash
# context7 (skill 模式, npx ctx7)
if command -v npx >/dev/null 2>&1 && npx --no-install ctx7 --version >/dev/null 2>&1; then
  CTX7_AVAILABLE=true
else
  CTX7_AVAILABLE=false
fi

# rg / jq
RG_AVAILABLE=$(command -v rg >/dev/null && echo true || echo false)
JQ_AVAILABLE=$(command -v jq >/dev/null && echo true || echo false)
# 注: 不探测语义扫描索引工具 (已退场, 用 rg/grep 兜底)

# v9.9.0: VM 运行时 (~/.athena/vm.json 由 /athena-vm setup 创建)
if [ -f "$HOME/.athena/vm.json" ]; then
  VM_AVAILABLE=true   # 存在即标 true; 连通性由 /athena-vm doctor 验证
else
  VM_AVAILABLE=false
fi
```

### Step 4: 创建 .ai_state/ 目录 (v9.9.2 Tier2 schema)

```bash
mkdir -p .ai_state/sprints
mkdir -p .ai_state/roadmap
mkdir -p .ai_state/architecture
mkdir -p .ai_state/requirements   # v9.8.0 长效需求档 (WHY, 逃生通道)
mkdir -p .ai_state/compound
mkdir -p .ai_state/.snapshots
# compound/ 从空起步, 用 .gitkeep 占位; 内容由 polish/review 按 doc_type 落具体文件
touch .ai_state/compound/.gitkeep
```

### Step 5: 复制 \_index.md 模板 + 填入探测结果

```bash
cp ~/.agents/skills/pace/templates/_index.md .ai_state/_index.md
```

主 agent 把探测值写入 frontmatter:

- `cx_version`, `cc_version`, `ag_callable`
- `tools_available.{context7_cli, rg_available, jq_available, vm_available}`
- `platforms_enabled`
- `platform_features.{cx_spawn_agent, cx_plan_mode_reasoning_effort, ag_parallel_subagents, ag_headless_p}`

判定规则:

- `cx_spawn_agent = true` if `CX_VERSION` >= 0.128
- `cx_plan_mode_reasoning_effort = true` when the installed Codex supports that config field
- `ag_parallel_subagents = ag_callable`; `ag_headless_p = ag_callable`

### Step 6: 总结 + 给用户

主 agent 输出 markdown 总结: 探测到的平台 / 可用工具表 / 缺失但建议安装的工具 / 下一步 (说出第一个任务 → 路由 PACE).

## 输出示例

```markdown
✓ Athena v9.9.2 初始化完成

## 平台

- CX (codex): codex-cli 0.144.1 ✓
- CC (claude): 未安装 (可选)
- AG (antigravity): 未安装. 安装: curl -fsSL https://antigravity.google/cli/install.sh | bash

## 工具

- context7 (npx ctx7, skill 模式): ✓
- rg: ✓ jq: ✓

## 状态

.ai_state/ 已建立 (sprints/ roadmap/ architecture/ requirements/ compound/ .snapshots/), \_index.md 已生成；仅填充模板中真实存在的字段。

## 下一步

告诉我要做什么, 我路由 PACE: 修 bug→Bugfix / 加功能→Feature / 重构→Refactor / 搭系统→System
```

## 例外

- 非 git 项目: 拒绝, 提示先 `git init`
- 模板缺失: fallback 内置 minimum template (保留 Athena 核心 frontmatter 字段)
- 已 init 又跑: 不覆盖, 显式问"重新初始化?会清空 .ai_state/"

## 路径无关

athena-init 不进任何 PACE stage, stage="(none)" → 等用户首条任务再路由.
