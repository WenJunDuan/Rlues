# /vibe-init — 项目初始化 (Codex 端)

## 1. 项目级 AGENTS.md

无项目根 AGENTS.md → 生成一份骨架:

```markdown
# AGENTS.md (项目级)

本项目使用 VibeCoding。开发用 /vibe-dev。
全局铁律见 ~/.codex/AGENTS.md。

## 项目约定
(vibe-init 扫描后填入)

## 测试命令
(vibe-init 扫描后填入)
```

已有 AGENTS.md → 只追加"本项目使用 VibeCoding"说明，不改现有内容。

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

从 ~/.codex/skills/pace/templates/ 复制全部模板 (必须全部复制, 缺一不可):
- project.json — PACE 状态
- tasks.md — Sprint 任务
- progress.md — impl 进度日志 (铁律 5)
- design.md — 设计文档
- handoff.md — spawn_agent 交接
- lessons.md — 经验沉淀 (compound 写入目标, 不能缺)
- review-report.md — 审查模板
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

## 6. Git commit

```bash
git add AGENTS.md .ai_state/ .gitignore
git commit -m "vibecoding: project initialized"
```

## 7. 验证

运行 `bash .ai_state/init.sh` 确认脚本正常。
`npx ctx7 library express 2>&1 | head -1` → 报错则提示: "context7 未装, 库文档查询不可用。运行 npx ctx7 setup --codex。"
告知用户检测结果 + "用 /vibe-dev 开始开发"

已有 .ai_state/ → 提示用户是否重新初始化。

## 兼容 CC

.ai_state/ schema 与 Claude Code 端 VibeCoding 9.4.4 **完全一致**。
同一项目可以在 CC 和 Codex 之间切换使用, 状态文件兼容。
