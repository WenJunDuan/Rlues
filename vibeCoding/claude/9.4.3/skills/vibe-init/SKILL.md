---
name: vibe-init
effort: high
disable-model-invocation: true
description: >
  项目初始化。每个新项目首次使用 VibeCoding 时运行。扫描项目、生成环境脚本、创建状态目录。
---

# /vibe-init — 项目初始化

## 1. CC 原生初始化

无 CLAUDE.md → 运行 `/init`，生成后追加: "本项目使用 VibeCoding，开发用 /vibe-dev"
已有 CLAUDE.md → 跳过。

## 2. 项目扫描

```bash
# 检测技术栈、包管理器、测试框架、lint、构建、dev server
ls package.json pyproject.toml Cargo.toml go.mod 2>/dev/null
cat package.json 2>/dev/null | grep -A5 '"scripts"'
ls jest.config* vitest.config* pytest.ini .eslintrc* ruff.toml 2>/dev/null
```

## 3. 创建 .ai_state/

```bash
mkdir -p .ai_state/reviews
```

从 pace/templates/ 复制全部模板。
project.json 填入检测到的 tech_stack, test_cmd, build_cmd, lint_cmd, dev_cmd。

## 4. 生成 init.sh

根据扫描结果生成 .ai_state/init.sh:
- 依赖安装命令
- dev server 启动 (如有)
- 基线测试命令
- `chmod +x .ai_state/init.sh`

检测不到 dev server → 只写依赖安装 + 测试命令。

## 5. .gitignore

```bash
grep -q '.ai_state' .gitignore 2>/dev/null || echo '.ai_state/' >> .gitignore
```

## 6. Git commit

```bash
git add .ai_state/ .gitignore
git commit -m "vibecoding: project initialized"
```

## 7. 验证

运行 `bash .ai_state/init.sh` 确认脚本正常。
`test -f ~/.claude/skills/gstack/SKILL.md` → 没有则提示: "Gstack 未安装, Feature+ 增强受限。运行 /vibe-setup 安装。"
告知用户检测结果 + "用 /vibe-dev 开始开发"

已有 .ai_state/ → 提示用户是否重新初始化。
