---
name: athena-setup
description: |
  Athena 全局首次配置 (跨项目, 一次性). 部署 rules / hooks / agents / skills 到 ~/.claude/ (CC) 或 ~/.codex/ (CX) 或 ~/.agents/skills/_athena/ (CX 端 skills).
  和 athena-init 区别: setup 是全局一次性, init 是每项目一次.
effort: low
---

# /athena-setup — Athena 全局首次配置 (v9.6.2)

## 触发

第一次安装 Athena 时跑一次. 之后跨项目复用, 不需要再跑.

## CC 端步骤

### Step 1: 复制 settings.json

```bash
# 从 v9.6.2 包复制
mkdir -p ~/.claude
cp settings.json ~/.claude/settings.json
```

### Step 2: 复制 rules/ (5 个文件)

```bash
mkdir -p ~/.claude/rules
cp rules/* ~/.claude/rules/
```

### Step 3: 复制 hooks/ (9 个 .cjs)

```bash
mkdir -p ~/.claude/hooks
cp hooks/*.cjs ~/.claude/hooks/
chmod +x ~/.claude/hooks/*.cjs
```

### Step 4: 复制 agents/ (3 个 .md)

```bash
mkdir -p ~/.claude/agents
cp agents/* ~/.claude/agents/
```

### Step 5: 复制 skills/

```bash
mkdir -p ~/.claude/skills
cp -r skills/* ~/.claude/skills/
```

### Step 6: 安装 / 启用插件 (CC 原生 plugin marketplace)

```bash
# 添加 marketplace (若尚未添加)
# claude /plugin marketplace add anthropic-official
# claude /plugin marketplace add github:vibecoding/claude-plugins

# 启用插件 (在 settings.json 中已声明, 但首次需要 explicit 启用)
# /plugin install superpowers@anthropic-official
# /plugin install code-review@anthropic-official
# /plugin install feature-dev@anthropic-official
# /plugin install commit@anthropic-official
# /plugin install playwright-skill@anthropic-official
# /plugin install context7@anthropic-official
# /plugin install codex-plugin-cc@third-party-marketplace
# /plugin install ECC-AgentShield@third-party-marketplace
```

### Step 7: 验证

```bash
# 检查 rules 部署
ls ~/.claude/rules/*.md

# 检查 hooks 可执行
node -e "require('~/.claude/hooks/session-start.cjs')" 2>&1 | head -3

# 启动 CC 验证 SessionStart hook 加载 rules 摘要
claude --version
```

## CX 端步骤 (若用户也用 Codex)

### Step 1: 复制 config.toml

```bash
# 备份现有
[ -f ~/.codex/config.toml ] && cp ~/.codex/config.toml ~/.codex/config.toml.pre-athena

# 复制模板 (用户需要手工填 model_provider / API key / token 等)
mkdir -p ~/.codex
cp cx/.codex/config.toml ~/.codex/config.toml

# ⚠️ 把模板中的 <USER_HOME> 替换为实际 $HOME
sed -i "s|<USER_HOME>|$HOME|g" ~/.codex/config.toml
```

### Step 2: 复制 hooks.json

```bash
# 备份现有 hooks.json
[ -f ~/.codex/hooks.json ] && cp ~/.codex/hooks.json ~/.codex/hooks.json.pre-athena

cp cx/.codex/hooks.json ~/.codex/hooks.json
```

### Step 3: 复制 hooks/ Python 脚本

```bash
mkdir -p ~/.codex/hooks
cp cx/.codex/hooks/*.py ~/.codex/hooks/
chmod +x ~/.codex/hooks/*.py

# 验证 python3 可达
/usr/bin/env python3 -c "print('ok')" || echo "ERROR: python3 不可达, 修复 PATH 后再跑"
```

### Step 4: 复制 agents/ (6 个 .toml)

```bash
mkdir -p ~/.codex/agents
cp cx/.codex/agents/*.toml ~/.codex/agents/
```

### Step 5: 复制 standards/ (5 个 md)

```bash
mkdir -p ~/.agents/standards    # 注意: ~/.agents/, 不是 ~/.codex/!
                                # 这是 agentskills.io 跨工具标准
cp cx/.codex/standards/*.md ~/.agents/standards/
```

### Step 6: 复制 skills/ (到 ~/.agents/skills/_athena/, 用前缀隔离)

```bash
# v9.6.2 关键: 用 _athena 前缀, 避免与其他工具自动加载 Athena skill 冲突
# (Codex / Antigravity 都扫 ~/.agents/skills/ 但只有 Athena 主 agent 显式调用 _athena/*)
mkdir -p ~/.agents/skills/_athena
cp -r cx/.codex/skills/* ~/.agents/skills/_athena/

# 验证: codex /skills 应该列出 pace, polish, context7, augment, antigravity, compound (在 _athena/ 下)
codex /skills 2>&1 | grep -i athena || echo "WARN: codex 未识别 _athena/ 下的 skills"
```

### Step 7: 验证

```bash
# 检查 hooks.json 不再与 config.toml 冲突
grep -c "\[\[hooks\." ~/.codex/config.toml  # 应为 0
ls ~/.codex/hooks.json                       # 应存在

# 检查 codex 启动无 hook fail
codex --version  # 应不报错; 启动 codex 看 hook 加载日志
```

## AG (Antigravity) 端

**不部署**. Antigravity 由用户通过 `agy` 命令自己使用, Athena 只调度.

可选: 如果用户希望让 agy 用 Athena 的 standards/, 把 standards/ 也部署到 ~/.agents/skills/_athena/standards/ (但这是 enhancement, 不是必需).

## 跨平台兼容性表

| Athena 资产 | CC 部署位置 | CX 部署位置 | AG 是否看到 |
|---|---|---|---|
| Settings | `~/.claude/settings.json` | `~/.codex/config.toml` + `~/.codex/hooks.json` | (n/a) |
| Rules | `~/.claude/rules/` | `~/.agents/standards/` | (CC/CX 独立) |
| Hooks | `~/.claude/hooks/*.cjs` | `~/.codex/hooks/*.py` | (n/a) |
| Subagents | `~/.claude/agents/*.md` | `~/.codex/agents/*.toml` | (n/a) |
| Skills | `~/.claude/skills/` | `~/.agents/skills/_athena/` | 也能看到 (但默认不加载) |
| Prompts | (cc 用 skills 替代) | `~/.codex/prompts/*.md` | (n/a) |

## 卸载

```bash
# CC
rm -rf ~/.claude/{rules,hooks,agents,skills}/athena-*
rm ~/.claude/settings.json.pre-athena 2>/dev/null

# CX
rm ~/.codex/hooks.json
mv ~/.codex/config.toml.pre-athena ~/.codex/config.toml 2>/dev/null
rm -rf ~/.codex/{hooks,agents}/athena-*
rm -rf ~/.agents/standards
rm -rf ~/.agents/skills/_athena
```

## 升级 (v9.6.1 → v9.6.2)

```bash
# 跑 athena-migrate skill, 它会:
# 1. 备份现有 .claude / .codex 配置
# 2. 应用 v9.6.2 hotfixes (B1/B2/B3)
# 3. 新增 rules/ + standards/ + polish skill
# 4. 验证迁移
```

详见 athena-migrate skill.
