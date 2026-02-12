#!/bin/bash
# VibeCoding v8.3.5 — 跨平台同步脚本
# 用途: 从 .claude/ 生成 Codex CLI 配置

set -euo pipefail

echo "=== VibeCoding v8.3.5 Platform Sync ==="

# 1. 确保 .codex 目录存在
mkdir -p .codex

# 2. 链接 skills 目录 (共享)
if [ -d ".claude/skills" ]; then
  if [ ! -L ".codex/skills" ]; then
    ln -sf ../.claude/skills .codex/skills
    echo "✓ Skills 已链接: .codex/skills → .claude/skills"
  else
    echo "✓ Skills 链接已存在"
  fi
fi

# 3. 链接 workflows 目录 (共享)
if [ -d ".claude/workflows" ]; then
  if [ ! -L ".codex/workflows" ]; then
    ln -sf ../.claude/workflows .codex/workflows
    echo "✓ Workflows 已链接: .codex/workflows → .claude/workflows"
  fi
fi

# 4. 复制 hooks (Node.js, 跨平台)
if [ -d ".claude/hooks" ]; then
  mkdir -p .codex/hooks
  cp .claude/hooks/*.js .codex/hooks/ 2>/dev/null
  echo "✓ Hooks 已复制: .codex/hooks/"
fi

# 5. 生成 AGENTS.md (如果 CLAUDE.md 更新了)
if [ ".claude/CLAUDE.md" -nt "AGENTS.md" ] 2>/dev/null || [ ! -f "AGENTS.md" ]; then
  # 从 CLAUDE.md 生成, 删除 CC-specific 段落
  sed \
    -e '/## Superpowers 协作/,/^## /{/^## [^S]/!d}' \
    -e '/### 官方 Plugins/,/^### /{/^### [^官]/!d}' \
    -e 's/augment-context-engine/augment-context-engine/g' \
    .claude/CLAUDE.md > AGENTS.md.tmp

  # 追加 Codex 特有段落 (质量门控替代 Hook)
  cat >> AGENTS.md.tmp << 'CODEX_APPEND'

## 质量门控 (替代 Claude Code Stop Hook)

完成任务前必须执行:
1. `npm test` — 全部通过
2. `npx tsc --noEmit` — 类型检查通过 (如有 tsconfig)
3. `.ai_state/doing.md` — 无未完成任务 (☐)
以上任一失败 → 修复后再完成, 不允许带错交付。
CODEX_APPEND

  mv AGENTS.md.tmp AGENTS.md
  echo "✓ AGENTS.md 已从 CLAUDE.md 生成"
else
  echo "✓ AGENTS.md 已是最新"
fi

# 5. 验证
echo ""
echo "=== 验证结果 ==="
echo "Claude Code:"
echo "  CLAUDE.md: $([ -f .claude/CLAUDE.md ] && echo '✓' || echo '✗')"
echo "  settings.json: $([ -f .claude/settings.json ] && echo '✓' || echo '✗')"
echo "  Skills: $(ls .claude/skills/ 2>/dev/null | wc -l | tr -d ' ') 个"
echo "  Commands: $(ls .claude/commands/ 2>/dev/null | wc -l | tr -d ' ') 个"
echo "  Hooks: $(ls .claude/hooks/ 2>/dev/null | wc -l | tr -d ' ') 个"
echo ""
echo "Codex CLI:"
echo "  AGENTS.md: $([ -f AGENTS.md ] && echo '✓' || echo '✗')"
echo "  config.toml: $([ -f .codex/config.toml ] && echo '✓' || echo '✗')"
echo "  Skills (link): $([ -L .codex/skills ] && echo '✓' || echo '✗')"
echo "  Hooks: $(ls .codex/hooks/*.js 2>/dev/null | wc -l | tr -d ' ') 个"
echo ""
echo "=== 同步完成 ==="
