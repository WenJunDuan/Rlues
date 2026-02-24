---
name: vibe-init
description: 初始化 .ai_state 统一目录
allowed-tools: Read, Write, Bash
---

# /vibe-init

1. 创建 `.ai_state/` 结构:
   ```bash
   mkdir -p .ai_state/{archive,requirements,assets}
   cp .claude/templates/ai-state/*.md .ai_state/
   ```
2. 扫描项目, 自动填充 `.ai_state/conventions.md` (语言/框架/测试/风格)
3. cunzhi: 确认 conventions 是否准确
4. 建议 .gitignore: `.ai_state/archive/` + `.ai_state/assets/*`

幂等: 已初始化 → 只更新 conventions.md, 不覆盖其他。
