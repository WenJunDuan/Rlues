---
name: polish
description: |
  PACE polish stage 专用 skill. 仅 Refactor / System 路径触发.
  review_pass1 后, ship 前的最终清理段. 清理临时代码 / 完善注释 / 检查冗余 / 低效 / 过度设计.
  产出 cleanup-pass-{sprint}.md, 合并 review 意见, stage 由 polish → ship.
effort: high
attach_to_rules: [doc-style, coding-standards]
---

# /polish — Athena Polish Stage Skill (v9.6.2)

## 何时触发

- 路径 ∈ {Refactor, System}
- 当前 stage = polish (review_pass1 后, ship 前)
- review_pass1 VERDICT ∈ {PASS, CONCERNS} (FAIL/REWORK 必须先修复)

**其他路径 (Hotfix / Bugfix / Quick / Feature) 跳过 polish, 直接 review → ship**.

## 启动检查

主 agent 进入 polish stage 时执行:

```bash
# 1. 验证前置条件
test -f .ai_state/details/reviews/sprint-${SPRINT}.md || { echo "无 review_pass1 结果, 不能 polish"; exit 1; }

# 2. 验证 path 适用
PATH_TYPE=$(rg -o 'path: "[A-Za-z]+"' .ai_state/_index.md | head -1)
case "$PATH_TYPE" in
  *Refactor*|*System*) ;;
  *) echo "$PATH_TYPE 不需要 polish, 直接进 ship"; exit 0 ;;
esac

# 3. 加载规则
cat ~/.agents/standards/doc-style.md
cat ~/.agents/standards/coding-standards.md
```

## 5 个检查项 (按顺序, 不允许跳)

### 1. 临时测试代码
```bash
# 扫描
rg -n "console\\.log|print\\(" src/        # 源文件 console.log
rg -n "// TODO|// FIXME|// XXX" src/        # 无 issue 号的标记
rg -n "test123|foo|bar" src/                 # 在生产代码出现 hardcoded test
```

每个 finding → executed (立即修) 或 deferred (写入 cleanup-pass.md 「待办」段, 必须给 issue 链接).

### 2. 注释完善
- 公开 API (export) 缺 docstring → 补 (P0)
- 复杂函数 (≥ 30 行) 缺解释性注释 → 补 (P1)
- 注释掉的代码 → 删 (P2)
- TODO 无 issue 号 → 加 issue 或删 (P1)

### 3. 冗余检查
- 死代码: `rg <export-name>` 0 引用 → 删
- 重复实现: 同样逻辑两处 → 提取共享函数
- 配置 / 常量重复 → 合并

### 4. 低效检查
- N+1 查询 → SQL JOIN / batch fetch
- O(n²) where O(n log n) 可达 → 重写
- 同步阻塞 in async → 改 async

### 5. 过度设计 (YAGNI)
- 抽象层只 1 个实现 → 删抽象
- 未来才用的扩展点 → 删
- Generic 但只 1 个类型 → 删 generic
- Builder pattern with ≤ 3 params → 改普通函数

## 产出

写入 `.ai_state/details/cleanup-pass-${SPRINT}.md`:

模板见 `~/.agents/skills/pace/templates/details/cleanup-pass.md`. 5 段对应 5 个检查项 + 合并 review 意见段.

## 合并 review 意见 (强制)

cleanup-pass.md 末尾必须有 "合并 review 意见" 段, 把 review_pass1 中 P2 级 (以及 polish 期间可顺手处理的 P1) finding 在 polish 阶段处理掉:

```markdown
## 合并 review 意见 (来自 details/reviews/sprint-{N}.md)

- review finding F3 P1: 已在 polish 处理 (commit xxx)
- review finding F5 P2: 已在 polish 处理 (commit yyy)
- review finding IM-2 P1: deferred 到 docs sprint (写入 lessons.md)
```

## VERDICT (polish 自己)

- **PASS**: 5 个检查项 executed 或 deferred (有明确 issue 引用), 改后测试 GREEN → stage 转 ship
- **REWORK**: polish 时发现新 P0 (例如清理时发现死代码其实被反射调用) → 回 review_pass1

## CX 端实现路径

CX 端 polish stage 由**主 agent**执行 (不 spawn subagent).

工作流:
1. 主 agent 读启动检查
2. 主 agent 顺序执行 5 个检查项
3. 主 agent 写 cleanup-pass.md
4. 主 agent 把 stage 改成 ship

可选: 主 agent 可 spawn `polish_worker` (cx/.codex/agents/polish_worker.toml) 或 `reviewer` 做"polish 后的二次 review", 但不强制.

## delivery-gate 强制

`~/.codex/hooks/delivery-gate.py` 会检查:
- path ∈ {Refactor, System}
- stage = ship
- → 必须存在 `.ai_state/details/cleanup-pass-${SPRINT}.md`, 否则 exit 2 + 提示运行 /polish

## 不要做

- 不引入新功能
- 不改 design.md 实现 (仅清理)
- 不删除合理的抽象 (Strategy 有 ≥ 2 个实现就保留)
- 不加新依赖
- 不修改测试逻辑 (除非清理临时 test value)

## 例外

- 项目自己声明跳过 polish (在 _index.md.skip_polish = true), 则仍写一份空 cleanup-pass.md 但所有段标 "(skipped: explicit opt-out)" → 仍可 ship
