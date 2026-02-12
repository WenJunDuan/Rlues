---
name: vibe-init
description: 初始化 VibeCoding 项目结构 — 创建 .ai_state/ 和 .knowledge/ 目录
allowed-tools: Read, Write, Bash
---

# /vibe-init — 项目初始化

## 执行步骤

1. 检查项目根目录是否已有 `.ai_state/`
2. 如果没有, 创建完整结构:
   ```bash
   mkdir -p .ai_state/archive
   mkdir -p .knowledge
   ```
3. 从模板创建初始文件:
   - `.ai_state/session.md` — 空会话模板
   - `.ai_state/conventions.md` — 项目规范 (从 README/package.json 推断)
   - `.ai_state/doing.md` — 空任务追踪
4. 扫描项目, 自动填充 conventions.md:
   - 语言/框架 (从 package.json / tsconfig / Cargo.toml 等)
   - 代码风格 (从 .eslintrc / .prettierrc 等)
   - 测试框架 (从 jest.config / vitest.config 等)
   - 构建工具 (从 vite.config / webpack.config 等)
5. cunzhi: 确认 conventions 是否准确

## 幂等

已初始化的项目再次运行 → 只更新 conventions.md, 不覆盖其他文件。
