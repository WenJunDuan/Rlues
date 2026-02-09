# Superpowers Bootstrap (Codex CLI)

Superpowers 通过文件系统加载，不走 plugin 命令。

## 安装

```bash
# 方式 1: 从 Superpowers marketplace 手动下载
# 放置到 ~/.codex/superpowers/skills/

# 方式 2: 如果已有 Claude Code 环境 (可选)
# cp -r ~/existing-claude-project/superpowers/skills/ ~/.codex/superpowers/skills/
```

## 目录结构

```
~/.codex/superpowers/skills/
├── brainstorming/SKILL.md
├── writing-plans/SKILL.md
├── tdd/SKILL.md
├── subagent-driven-dev/SKILL.md
├── verification-before-completion/SKILL.md
├── requesting-code-review/SKILL.md
└── debugging/SKILL.md
```

## 调用方式

Codex 不像 Claude Code 有 plugin runtime。
VibeCoding workflow 在对应阶段读取 SKILL.md 文件内容，按其方法论执行。

```
# workflow 内部逻辑 (对用户透明):
读取 ~/.codex/superpowers/skills/brainstorming/SKILL.md
→ 按文件中描述的方法论执行苏格拉底提问
```

## 降级

如果 Superpowers 未安装:
- 所有 SP skill 有内置降级方案 (见各 skill 的"降级"段)
- 核心功能不受影响，只是缺少结构化方法论增强
- VibeCoding 自身能力覆盖 80% 场景

## 验证

```bash
# 检查安装
ls ~/.codex/superpowers/skills/
# 应有 7 个子目录
```
