# VibeCoding Kernel v9.4.3-cx — Codex CLI

## 安装

### 1. 复制系统目录文件

```bash
cp -r .codex/ <你的系统目录>/.codex/
cp AGENTS.md <你的系统目录>/AGENTS.md
```

### 2. Superpowers 安装

```bash
git clone https://github.com/obra/superpowers.git ~/.codex/superpowers
mkdir -p ~/.agents/skills
ln -sf ~/.codex/superpowers ~/.agents/skills/superpowers
```

验证: 启动 Codex，说 "help me plan a feature" → brainstorming 应自动激活。

### 3. Context7 安装

**方式 A: ctx7 CLI (推荐)**

```bash
npm install -g @upstash/context7-cli
# 验证
ctx7 library express
```

**方式 B: MCP (CLI 不可用时)**

```bash
codex mcp add context7 -- npx -y @upstash/context7-mcp
```

### 4. 启用 Hooks

```bash
codex features enable codex_hooks
```

注意: Hooks 在 Windows 原生环境默认关闭，建议使用 WSL2。

### 5. 验证

```bash
ls ~/.agents/skills/superpowers/SKILL.md   # superpowers
codex mcp list                              # augment MCP
codex features list | grep codex_hooks      # hooks
```

## 使用

启动 Codex，说需求即可。PACE 自动路由:

- 小修小补 → Hotfix/Bugfix，直接做
- 新功能 → Feature，brainstorming → 设计 → 实现 → 审查
- 大系统目录 → System，全增强

## CC ↔ CX 协作

CC 通过 codex-plugin-cc 委托任务给 CX。CX 端有 AGENTS.md 引导工程纪律。
