# /athena-init (Codex) — 项目初始化

# 描述
> 项目初始化。每个新项目首次使用 Athena 时运行。
# end

参考: <https://developers.openai.com/codex/concepts/customization>

`.ai_state/_index.md` 已存在 → 提示用户用 `/athena-migrate` 升级或确认覆盖。

## 1. 项目扫描

```bash
ls package.json pyproject.toml Cargo.toml go.mod build.gradle pom.xml 2>/dev/null
cat package.json 2>/dev/null | grep -A5 '"scripts"'
ls jest.config* vitest.config* pytest.ini .eslintrc* ruff.toml biome.json 2>/dev/null
```

## 2. 创建 .ai_state/ (v9.6 schema)

```bash
mkdir -p .ai_state/details/reviews .ai_state/details/tasks-archive
```

## 3. 拷贝模板

从 `~/.codex/skills/pace/templates/` 复制:
- `_index.md`  →  `.ai_state/_index.md`
- 所有 `details/*.md`
- `goal-conditions.md`
- `init.sh`

## 4. 填充 _index.md frontmatter

把扫描结果写入: tech_stack, test_cmd, build_cmd, lint_cmd, dev_cmd

平台特征 (`codex --version` 输出):
- `cx_version`: 解析 `codex --version` 输出 (形如 "codex-cli 0.128.3" 或 "rust-v0.130.1")
- `goal_supported`: **cx_version ≥ "0.128.0" → true** (Codex /goal 在 v0.128.0 GA, 2026-04-30)
  参考: <https://developers.openai.com/codex/changelog> + GitHub release rust-v0.128.0
- `batch_supported`: Codex subagent (max_threads in [agents]) 部分支持 → 视 max_threads 而定 (无 worktree 隔离, 与 CC /batch 行为不等价)
- `background_supported`: false (Codex 无 /background)
- `session_memory_active`: false (Codex 无 ~/.claude/projects/ 等价物)
- `cross_session_memory`: "none"

## 5. 生成 init.sh

根据扫描结果定制 `.ai_state/init.sh`. `chmod +x`.

## 6. .gitignore

```bash
grep -q '.ai_state' .gitignore 2>/dev/null || echo '.ai_state/' >> .gitignore
```

## 7. Git commit

```bash
git add .ai_state/ .gitignore
git commit -m "athena: project initialized (v9.6.1 schema, Codex)"
```

## 8. 验证

```bash
bash .ai_state/init.sh
```

告知用户:
- "Athena (Codex 版 v9.6.1) 已就绪。用 `/athena-dev <需求>` 开始, 或 `/athena-status` 看面板。"
- 如 `goal_supported: true` → 提示: "Codex /goal 已对齐 v0.128+, PACE 各 stage 可用 `/goal` 启动 autonomous loop。模板见 `~/.codex/skills/pace/templates/goal-conditions.md`。"
