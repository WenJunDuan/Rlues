---
name: vibe-init
description: 初始化项目 .ai_state 状态目录
---
## 执行步骤
1. 创建 .ai_state/ 目录
2. 从 .claude/templates/ai-state/ 复制所有模板文件
3. 自动检测项目类型并填充 conventions.md:
   - package.json → Node.js: 语言 TS/JS, 测试 jest/vitest, lint eslint
   - pyproject.toml → Python: 语言 Python, 测试 pytest, lint ruff
   - Cargo.toml → Rust: 语言 Rust, 测试 cargo test, lint clippy
   - go.mod → Go: 语言 Go, 测试 go test, lint golangci-lint
4. 添加 .ai_state/ 到 .gitignore
5. 输出: "VibeCoding Kernel v9.1.5 已初始化。使用 /vibe-dev {需求} 开始。"
