---
name: vibe-init
effort: xhigh
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
ls package.json pyproject.toml Cargo.toml go.mod 2>/dev/null
cat package.json 2>/dev/null | grep -A5 '"scripts"'
ls jest.config* vitest.config* pytest.ini .eslintrc* ruff.toml 2>/dev/null
```

## 3. 创建 .ai_state/

```bash
mkdir -p .ai_state/reviews
```

从 ~/.claude/skills/pace/templates/ 复制全部模板 (必须全部复制, 缺一不可):
- project.json — PACE 状态
- tasks.md — Sprint 任务 (含 Boundary/Depends 标注示例)
- progress.md — impl 进度日志 (铁律 5)
- design.md — 设计文档 (含 File Structure Plan 段)
- handoff.md — 跨模型/跨 worker 交接
- lessons.md — 项目级业务经验 (compound 写入目标, 不能缺)
- review-report.md — 审查模板 (含反伪装证据要求)
- init.sh — 基线脚本

project.json 填入检测到的 tech_stack, test_cmd, build_cmd, lint_cmd, dev_cmd。

## 4. 生成 init.sh

根据扫描结果生成 .ai_state/init.sh:
- 依赖安装命令
- dev server 启动 (如有)
- 基线测试命令
- `chmod +x .ai_state/init.sh`

## 5. .gitignore

```bash
grep -q '.ai_state' .gitignore 2>/dev/null || echo '.ai_state/' >> .gitignore
```

## 6. 全局 lessons 检查

```bash
test -d ~/.claude/lessons && ls ~/.claude/lessons/INDEX.md 2>/dev/null
```

无 → 提示 "首次使用全局 lessons, 运行 /vibe-setup 初始化 ~/.claude/lessons/"

## 7. Git commit

```bash
git add .ai_state/ .gitignore
git commit -m "vibecoding: project initialized"
```

## 8. 验证

运行 `bash .ai_state/init.sh` 确认脚本正常。
`test -f ~/.claude/skills/gstack/SKILL.md` → 没有则提示: "Gstack 未安装, Feature+ 增强受限。运行 /vibe-setup 安装。"
`npx ctx7 library express 2>&1 | head -1` → 报错则提示: "context7 未装, 库文档查询不可用。运行 npx ctx7 setup --claude。"
告知用户检测结果 + "用 /vibe-dev 开始开发"

已有 .ai_state/ → 提示用户是否重新初始化。
