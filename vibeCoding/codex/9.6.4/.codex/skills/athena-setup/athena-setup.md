---
name: athena-setup
description: |
  Athena 全局首次配置 (Codex 端, 跨项目一次性). 部署 config.toml / hooks / agents / standards / skills 到 ~/.codex/ 与 ~/.agents/skills/_athena/.
  和 athena-init 区别: setup 全局一次性, init 每项目一次.
  v9.6.4-hotfix3: 由 prompts/ 迁为 skill; 补 entry-skills 部署步骤; 修 agents 计数; context7 skill 模式; 移除语义扫描 MCP.
effort: low
---

# /athena-setup — Athena 全局首次配置 (Codex, v9.6.4-hotfix3)

## 触发

第一次安装 Athena 时跑一次. 之后跨项目复用.

## CX 端步骤

### Step 1: 复制 config.toml

```bash
[ -f ~/.codex/config.toml ] && cp ~/.codex/config.toml ~/.codex/config.toml.pre-athena
mkdir -p ~/.codex
cp cx/.codex/config.toml ~/.codex/config.toml
# 把模板中的 <USER_HOME> 替换为实际 $HOME (config.toml 里 skills 路径用到)
sed -i "s|<USER_HOME>|$HOME|g" ~/.codex/config.toml
```

### Step 2: 复制 hooks.json

```bash
[ -f ~/.codex/hooks.json ] && cp ~/.codex/hooks.json ~/.codex/hooks.json.pre-athena
cp cx/.codex/hooks.json ~/.codex/hooks.json
# 注: Codex 同时支持 hooks.json 与 config.toml inline [hooks]; 本项目用 hooks.json,
#     config.toml 不放 [hooks] 表 (同层两者并存会 warn). hooks 默认启用.
```

### Step 3: 复制 hooks/ Python 脚本

```bash
mkdir -p ~/.codex/hooks
cp cx/.codex/hooks/*.py ~/.codex/hooks/
chmod +x ~/.codex/hooks/*.py
/usr/bin/env python3 -c "print('ok')" || echo "ERROR: python3 不可达, 修复 PATH 后再跑"
```

### Step 4: 复制 agents/ (9 个 .toml)

```bash
mkdir -p ~/.codex/agents
cp cx/.codex/agents/*.toml ~/.codex/agents/
# 9 个: architect / critic / docs_researcher / evaluator / generator / polish_worker / pr_explorer / reviewer / spec-compliance
ls ~/.codex/agents/*.toml | wc -l   # 应为 9
```

### Step 5: 复制 standards/ (5 个 md)

```bash
mkdir -p ~/.agents/standards   # 注意 ~/.agents/, 不是 ~/.codex/ (agentskills.io 跨工具标准)
cp cx/.codex/standards/*.md ~/.agents/standards/
```

### Step 6: 复制 skills/ (到 ~/.agents/skills/\_athena/, 前缀隔离)

```bash
mkdir -p ~/.agents/skills/_athena
cp -r cx/.codex/skills/* ~/.agents/skills/_athena/
```

### Step 7: 验证 entry + workflow + tool skills 全部被发现

```bash
# v9.6.4-hotfix3 关键: 7 个 athena-* entry skill 现以 skill 形态部署 (不再用 deprecated prompts/).
# config.toml 的 [[skills.config]] 已逐条显式列出 (兜底 _athena/ 嵌套发现).
# 自检: 应列出全部 16 个 (7 entry + pace/polish/compound/brainstorm/roadmap/architect-doc + context7/antigravity/deps-check)
codex /skills 2>&1 | grep -ic athena    # 期望 ≥ 13 (含 athena 字样的)
grep -c '\[\[skills.config\]\]' ~/.codex/config.toml   # 期望 16

# hooks.json 不与 config.toml inline [hooks] 冲突 (后者应为空)
grep -c '^\[\[hooks\.' ~/.codex/config.toml            # 期望 0
ls ~/.codex/hooks.json                                  # 应存在

# 启动验证
codex --version
```

> **不再部署 prompts/**: Codex 自定义 prompt 已 deprecated 且只能人工 `/` 触发、不能被 agent 隐式调用. 所有 athena-\* 入口统一为 skill (自动发现 + 可隐式调用), 与 CC 端 skill 形态对齐.

## AG (Antigravity) 端

**不部署**. Antigravity 由用户通过 `agy` 自己使用, Athena 只调度.

## 跨平台部署位置表

| Athena 资产       | CC 部署位置                 | CX 部署位置                                    |
| ----------------- | --------------------------- | ---------------------------------------------- |
| Settings          | `~/.claude/settings.json`   | `~/.codex/config.toml` + `~/.codex/hooks.json` |
| Rules / Standards | `~/.claude/rules/`          | `~/.agents/standards/`                         |
| Hooks             | `~/.claude/hooks/*.cjs`     | `~/.codex/hooks/*.py`                          |
| Subagents         | `~/.claude/agents/*.md` (5) | `~/.codex/agents/*.toml` (9)                   |
| Skills (含 entry) | `~/.claude/skills/`         | `~/.agents/skills/_athena/`                    |

## 卸载

```bash
# CX
rm ~/.codex/hooks.json
mv ~/.codex/config.toml.pre-athena ~/.codex/config.toml 2>/dev/null
rm -rf ~/.codex/{hooks,agents}
rm -rf ~/.agents/standards
rm -rf ~/.agents/skills/_athena
```

## 升级

跑 athena-migrate skill (备份现有配置 → 应用迁移 → 验证). 详见 athena-migrate.
